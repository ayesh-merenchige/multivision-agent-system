"""Shared Gemini LLM instance + safe invocation helper.

The model is constructed eagerly at import time. This is safe because
``app.config`` already fails loudly when GEMINI_API_KEY is missing, so the
module can only be imported in a properly configured environment.
"""
from __future__ import annotations

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.utils.logger import get_logger

log = get_logger("llm")

# Construct once at import and reuse for the process lifetime.
llm: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.gemini_api_key,
    temperature=0.3,
    max_output_tokens=1024,
)


def get_llm() -> ChatGoogleGenerativeAI:
    """Return the shared Gemini chat model."""
    return llm


async def safe_llm_call(messages: list[BaseMessage], fallback: str) -> str:
    """Invoke the LLM, returning a friendly fallback message on any error."""
    try:
        response = await get_llm().ainvoke(messages)
        return response.content.strip()
    except Exception as exc:  # noqa: BLE001 - graceful degradation
        log.error("LLM call failed: %s", exc)
        return fallback
