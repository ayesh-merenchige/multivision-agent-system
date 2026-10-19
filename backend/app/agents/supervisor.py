"""Supervisor / router node.

The supervisor inspects the shared state and decides which agent runs next.
On the first turn (``next_agent`` unset) it delegates to the Chat/NLU agent;
afterwards it honours whatever node set ``next_agent``.
"""
from __future__ import annotations

from app.agents.state import AgentState
from app.utils.tracer import agent_trace


async def supervisor_node(state: AgentState) -> dict:
    """Route the conversation. Returns the trace entry so the API/dashboard
    can see the routing decision; the conditional edge does the actual routing."""
    next_agent = state.get("next_agent", "") or "chat_agent"
    async with agent_trace(
        state["session_id"], "supervisor", "route", {"next_agent": next_agent}
    ) as tr:
        pass
    return {"trace": state["trace"] + [tr.entry]}


def route_from_supervisor(state: AgentState) -> str:
    """Conditional edge: pick the next node based on state['next_agent']."""
    return state.get("next_agent") or "chat_agent"
