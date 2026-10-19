"""Shared LangGraph state for the multi-agent system."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State threaded through the LangGraph supervisor graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    intent: str                      # ask_company | ask_products | ask_price | place_order | smalltalk | unknown
    entities: dict                   # product_name, quantity, customer_name, contact, address
    next_agent: str                  # chat_agent | catalog_agent | order_agent | "" (END)
    order_draft: dict | None         # accumulated order fields across turns
    order_result: dict | None        # final order confirmation payload
    trace: list[dict]                # per-node execution records for the dashboard/API
    session_id: str
