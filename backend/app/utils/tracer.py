"""Per-node execution tracer: writes an AgentLog row and exposes a trace entry.

Usage inside a graph node::

    async with agent_trace(session_id, "catalog", "answer_query", {"intent": intent}) as tr:
        reply = await do_work()
        tr.set_output({"reply": reply})
    # tr.entry is final here (latency + status recorded on exit)
    return {"messages": [AIMessage(content=reply)], "trace": state["trace"] + [tr.entry]}
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from app.repositories.log_repo import record_log
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.db.session import AsyncSessionLocal

log = get_logger("tracer")


class _Recorder:
    def __init__(self) -> None:
        self.entry: dict[str, Any] = {}
        self._output: dict[str, Any] = {}

    def set_output(self, output: dict[str, Any]) -> None:
        self._output = output


@asynccontextmanager
async def agent_trace(
    session_id: str,
    agent_name: str,
    action: str,
    input_payload: dict[str, Any],
):
    """Trace one agent invocation: measure latency, log to DB, expose entry."""
    recorder = _Recorder()
    start = time.perf_counter()
    status = "success"
    try:
        yield recorder
    except Exception as exc:  # noqa: BLE001
        status = "error"
        recorder.set_output({"error": str(exc)})
        raise
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        recorder.entry = {
            "agent": agent_name,
            "action": action,
            "status": status,
            "latency_ms": latency_ms,
        }
        try:
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                await record_log(
                    db,
                    session_id=session_id,
                    agent_name=agent_name,
                    action=action,
                    input_payload=input_payload,
                    output_payload=recorder._output,
                    latency_ms=latency_ms,
                    status=status,
                )
        except Exception as exc:  # noqa: BLE001 - never crash a request on logging
            log.error("Failed to write agent log: %s", exc)
