"""LangGraph supervisor graph — built once at startup and reused.

Flow:
    START → supervisor → chat_agent → (catalog_agent | order_agent | END)
                  ↑___________| (order collection loops back through chat)
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.catalog_agent import catalog_agent_node
from app.agents.chat_agent import chat_agent_node, route_from_chat
from app.agents.order_agent import order_agent_node
from app.agents.state import AgentState
from app.agents.supervisor import route_from_supervisor, supervisor_node
from app.utils.logger import get_logger

log = get_logger("graph")

_graph = None


def build_graph():
    """Compile the multi-agent supervisor graph."""
    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("chat_agent", chat_agent_node)
    builder.add_node("catalog_agent", catalog_agent_node)
    builder.add_node("order_agent", order_agent_node)

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "chat_agent": "chat_agent",
            "catalog_agent": "catalog_agent",
            "order_agent": "order_agent",
            END: END,
        },
    )

    builder.add_conditional_edges(
        "chat_agent",
        route_from_chat,
        {
            "catalog_agent": "catalog_agent",
            "order_agent": "order_agent",
            END: END,
        },
    )

    builder.add_edge("catalog_agent", END)
    builder.add_edge("order_agent", END)

    return builder.compile()


def get_graph():
    """Return the compiled graph, building it on first use."""
    global _graph
    if _graph is None:
        _graph = build_graph()
        log.info("LangGraph supervisor graph compiled")
    return _graph
