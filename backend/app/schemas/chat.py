"""Pydantic schemas for chat API payloads."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)


class TraceEntry(BaseModel):
    agent: str
    action: str
    status: str
    latency_ms: int


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    order_id: str | None = None
    trace: list[TraceEntry] = Field(default_factory=list)


class NewSessionResponse(BaseModel):
    session_id: str
    title: str


class ChatMessageOut(BaseModel):
    role: str  # user | assistant
    content: str
    agent: str | None = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageOut]


class SessionSummary(BaseModel):
    session_id: str
    title: str
    last_activity: str
    message_count: int
