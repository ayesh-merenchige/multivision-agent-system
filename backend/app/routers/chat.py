"""Chat API: runs the LangGraph supervisor graph per message.

Also provides session management and an SSE streaming variant.
"""
from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_graph
from app.db.session import get_db
from app.repositories import log_repo
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    NewSessionResponse,
    SessionSummary,
    TraceEntry,
)
from app.utils.logger import get_logger

log = get_logger("router.chat")
router = APIRouter(prefix="/api/chat", tags=["chat"])


async def run_chat_turn(db: AsyncSession, session_id: str, message: str) -> dict:
    """Execute one graph turn and return the reply payload."""
    await log_repo.upsert_chat_session(db, session_id)

    # Reconstruct prior conversation from the agent logs, then append the new message.
    history = await log_repo.chat_history(db, session_id)
    messages: list = []
    for m in history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            messages.append(AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=message))

    # Rebuild the in-flight order draft (graph state resets each invocation).
    order_draft = await log_repo.get_latest_order_draft(db, session_id)

    initial = {
        "messages": messages,
        "intent": "unknown",
        "entities": {},
        "next_agent": "",
        "order_draft": order_draft,
        "order_result": None,
        "trace": [],
        "session_id": session_id,
    }

    result = await get_graph().ainvoke(initial)

    reply = ""
    if result.get("messages"):
        last = result["messages"][-1]
        reply = getattr(last, "content", "") or ""

    order_result = result.get("order_result") or {}
    trace = result.get("trace", []) or []

    return {
        "session_id": session_id,
        "reply": reply,
        "intent": result.get("intent", "unknown"),
        "order_id": order_result.get("order_id"),
        "trace": [t if isinstance(t, dict) else dict(t) for t in trace],
    }


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Process a user message through the multi-agent graph."""
    try:
        return await run_chat_turn(db, payload.session_id, payload.message)
    except Exception as exc:  # noqa: BLE001 - graceful fallback
        log.error("chat turn failed: %s", exc)
        raise HTTPException(
            status_code=500, detail="Sorry, something went wrong while processing your message."
        ) from exc


@router.post("/stream")
async def chat_stream(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """SSE variant: streams the reply token-by-token, then a done event."""

    async def event_generator():
        try:
            result = await run_chat_turn(db, payload.session_id, payload.message)
        except Exception as exc:  # noqa: BLE001
            log.error("chat stream failed: %s", exc)
            result = {
                "reply": "Sorry, something went wrong while processing your message.",
                "intent": "error",
                "order_id": None,
                "trace": [],
            }

        # Stream the reply in word-sized chunks for a live feel.
        words = result["reply"].split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
            await asyncio.sleep(0.03)

        yield f"data: {json.dumps({'type': 'done', 'session_id': result['session_id'], 'intent': result['intent'], 'order_id': result.get('order_id'), 'trace': result['trace']})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/new-session", response_model=NewSessionResponse)
async def new_session(db: AsyncSession = Depends(get_db)):
    """Create a fresh chat session."""
    session_id = str(uuid.uuid4())
    await log_repo.upsert_chat_session(db, session_id, title="New chat")
    return NewSessionResponse(session_id=session_id, title="New chat")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return the reconstructed message history for a session."""
    messages = await log_repo.chat_history(db, session_id)
    return ChatHistoryResponse(session_id=session_id, messages=messages)


@router.get("/sessions", response_model=list[SessionSummary])
async def sessions(db: AsyncSession = Depends(get_db)):
    """List recent chat sessions (for the chat sidebar)."""
    return await log_repo.list_sessions(db)
