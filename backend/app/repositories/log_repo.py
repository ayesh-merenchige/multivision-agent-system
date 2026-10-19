"""AgentLog persistence + chat history reconstruction."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentLog, ChatSession, Order


async def record_log(
    session: AsyncSession,
    *,
    session_id: str,
    agent_name: str,
    action: str,
    input_payload: dict | str,
    output_payload: dict | str,
    latency_ms: int,
    status: str = "success",
) -> AgentLog:
    """Persist one agent invocation record."""
    def _dumps(v: dict | str) -> str:
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)

    entry = AgentLog(
        session_id=session_id,
        agent_name=agent_name,
        action=action,
        input_payload=_dumps(input_payload),
        output_payload=_dumps(output_payload),
        latency_ms=latency_ms,
        status=status,
    )
    session.add(entry)
    await session.commit()
    return entry


async def recent_logs(
    session: AsyncSession, limit: int = 20, agent: str | None = None
) -> list[AgentLog]:
    stmt = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
    if agent:
        stmt = stmt.where(AgentLog.agent_name == agent)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def agent_stats(session: AsyncSession) -> list[dict]:
    """Per-agent invocation counts, avg latency, success rate, last-called."""
    success_count = func.sum(
        case((AgentLog.status == "success", 1), else_=0)
    ).label("successes")

    rows = await session.execute(
        select(
            AgentLog.agent_name,
            func.count(AgentLog.id).label("calls"),
            func.avg(AgentLog.latency_ms).label("avg_latency"),
            success_count,
            func.max(AgentLog.created_at).label("last_called"),
        ).group_by(AgentLog.agent_name)
    )
    out = []
    for r in rows.all():
        calls = int(r.calls or 0)
        successes = int(r.successes or 0)
        out.append(
            {
                "agent": r.agent_name,
                "calls": calls,
                "avg_latency_ms": round(float(r.avg_latency or 0), 1),
                "success_rate": round(successes / calls * 100, 1) if calls else 0.0,
                "last_called": r.last_called.isoformat() if r.last_called else None,
            }
        )
    return out


async def calls_last_24h(session: AsyncSession) -> int:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    return int(
        await session.scalar(
            select(func.count(AgentLog.id)).where(AgentLog.created_at >= since)
        )
        or 0
    )


async def timeline(session: AsyncSession, days: int = 7) -> list[dict]:
    """Orders + chats per day for the last `days` days (UTC)."""
    since = datetime.now(timezone.utc) - timedelta(days=days - 1)
    since_str = since.date().isoformat()

    order_rows = await session.execute(
        select(
            func.date(Order.created_at).label("day"),
            func.count(Order.id).label("orders"),
        )
        .where(func.date(Order.created_at) >= since_str)
        .group_by(func.date(Order.created_at))
    )
    chat_rows = await session.execute(
        select(
            func.date(AgentLog.created_at).label("day"),
            func.count(func.distinct(AgentLog.session_id)).label("chats"),
        )
        .where(func.date(AgentLog.created_at) >= since_str)
        .group_by(func.date(AgentLog.created_at))
    )

    orders_by_day = {str(r.day): int(r.orders) for r in order_rows.all()}
    chats_by_day = {str(r.day): int(r.chats) for r in chat_rows.all()}

    out = []
    for i in range(days):
        day = (since + timedelta(days=i)).date().isoformat()
        out.append(
            {
                "date": day,
                "orders": orders_by_day.get(day, 0),
                "chats": chats_by_day.get(day, 0),
            }
        )
    return out


# ---------------------------------------------------------------------------
# Chat sessions & history (reconstructed from AgentLog input/output payloads)
# ---------------------------------------------------------------------------


async def upsert_chat_session(
    session: AsyncSession, session_id: str, title: str = "New chat"
) -> ChatSession:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    stmt = (
        sqlite_insert(ChatSession)
        .values(id=session_id, title=title, created_at=func.now(), updated_at=func.now())
        .on_conflict_do_update(
            index_elements=[ChatSession.id],
            set_={"updated_at": func.now()},
        )
    )
    await session.execute(stmt)
    await session.commit()
    result = await session.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    return result.scalar_one()


async def list_sessions(session: AsyncSession, limit: int = 20) -> list[dict]:
    rows = await session.execute(
        select(
            AgentLog.session_id,
            func.max(AgentLog.created_at).label("last_activity"),
            func.count(AgentLog.id).label("message_count"),
        )
        .group_by(AgentLog.session_id)
        .order_by(func.max(AgentLog.created_at).desc())
        .limit(limit)
    )
    out = []
    for r in rows.all():
        out.append(
            {
                "session_id": r.session_id,
                "title": "Chat session",
                "last_activity": r.last_activity.isoformat() if r.last_activity else "",
                "message_count": int(r.message_count or 0),
            }
        )
    return out


async def get_latest_order_draft(session: AsyncSession, session_id: str) -> dict | None:
    """Reconstruct the most recent order draft from agent-log output payloads.

    The LangGraph state (including order_draft) resets each invocation, so we
    rebuild it from the persisted chat/order agent logs.
    """
    rows = await session.execute(
        select(AgentLog)
        .where(AgentLog.session_id == session_id)
        .order_by(AgentLog.created_at.desc(), AgentLog.id.desc())
        .limit(15)
    )
    for log in rows.scalars().all():
        try:
            out = json.loads(log.output_payload) if log.output_payload else {}
        except json.JSONDecodeError:
            continue
        draft = out.get("order_draft")
        if draft and isinstance(draft, dict):
            return draft
    return None


async def chat_history(session: AsyncSession, session_id: str) -> list[dict]:
    """Reconstruct the user/assistant message list for a session from logs."""
    rows = await session.execute(
        select(AgentLog)
        .where(AgentLog.session_id == session_id)
        .order_by(AgentLog.created_at.asc(), AgentLog.id.asc())
    )
    messages: list[dict] = []
    for log in rows.scalars().all():
        try:
            inp = json.loads(log.input_payload) if log.input_payload else {}
        except json.JSONDecodeError:
            inp = {}
        try:
            out = json.loads(log.output_payload) if log.output_payload else {}
        except json.JSONDecodeError:
            out = {}
        # The chat agent logs the raw user message under "message".
        if "message" in inp:
            messages.append(
                {
                    "role": "user",
                    "content": inp.get("message", ""),
                    "agent": None,
                    "created_at": log.created_at.isoformat(),
                }
            )
        # Answering agents (chat/catalog/order) log their reply under "reply".
        reply = out.get("reply")
        if reply:
            messages.append(
                {
                    "role": "assistant",
                    "content": reply,
                    "agent": log.agent_name,
                    "created_at": log.created_at.isoformat(),
                }
            )
    return messages
