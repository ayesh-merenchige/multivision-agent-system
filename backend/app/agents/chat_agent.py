"""Chat / NLU agent.

Classifies the user's intent and extracts entities using Gemini (with a
keyword-based fallback). Routes information queries to the Catalog agent and
order requests to the Order agent; answers smalltalk directly.
"""
from __future__ import annotations

import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import safe_llm_call
from app.agents.state import AgentState
from app.utils.logger import get_logger
from app.utils.tracer import agent_trace

log = get_logger("chat_agent")

_INTENT_NAMES = ["ask_company", "ask_products", "ask_price", "place_order", "smalltalk", "unknown"]

_SYSTEM_PROMPT = """You are Multivisions' sales assistant. You can talk about company details, products, and pricing, and help users place orders. Never invent product data — always call the catalog tool. When the user wants to order, collect product_name, quantity, customer_name, contact, address before confirming. Keep replies friendly, concise, and professional.

Your job right now is ONLY to classify the user's message and extract entities.
Respond with ONLY valid JSON (no markdown, no explanation) in this exact shape:
{{"intent": "<one of {intents}>", "entities": {{"product_name": "", "quantity": null, "customer_name": "", "contact": "", "address": ""}}}}

Rules:
- intent must be exactly one of: {intents}
- entities.quantity is a number or null
- If the user wants to order, intent = place_order
- If the user asks about the company, intent = ask_company
- If the user asks about products/catalog, intent = ask_products
- If the user asks about a price, intent = ask_price
- Greetings, thanks, small talk → smalltalk
- Anything else → unknown
""".format(intents=", ".join(_INTENT_NAMES))


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _keyword_fallback(message: str) -> tuple[str, dict]:
    """Deterministic intent/entity extraction when the LLM is unavailable."""
    m = message.lower()
    entities: dict = {}

    # --- entity extraction ---------------------------------------------------
    qty_match = re.search(
        r"(\d+)\s+([a-z0-9\- ]+?)(?:\s+(?:to|for|my|name|contact|phone|email|address)|$)",
        m,
    )
    name_match = re.search(
        r"(?:my name is|name is|i am|i'm|name)\s+([a-z ]+?)(?:,|\.|$|\s+contact|\s+phone|\s+email|\s+address)",
        m,
    )
    if name_match:
        entities["customer_name"] = name_match.group(1).strip().title()

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", message)
    phone_match = re.search(r"(?:contact|phone|mobile|email)[\s:]*([+\d][\d\s-]{6,}\d)", m)
    if email_match:
        entities["contact"] = email_match.group(0)
    elif phone_match:
        entities["contact"] = phone_match.group(1).strip()

    addr_match = re.search(r"(?:address|deliver to|ship to)[\s:]*([a-z0-9 ,]+)$", m)
    if addr_match:
        entities["address"] = addr_match.group(1).strip()

    # --- intent classification -------------------------------------------------
    if any(w in m for w in ["order", "buy", "purchase", "want to get", "like to get"]):
        if qty_match:
            entities["quantity"] = int(qty_match.group(1))
            entities["product_name"] = qty_match.group(2).strip()
        return "place_order", entities
    if any(w in m for w in ["price", "cost", "how much"]):
        return "ask_price", entities
    if any(w in m for w in ["product", "sell", "catalog", "items", "device", "devices", "offer"]):
        return "ask_products", entities
    if any(w in m for w in ["company", "about", "who are you", "hours", "located", "where are you"]):
        return "ask_company", entities
    if any(w in m for w in ["hello", "hi", "hey", "thanks", "thank", "bye", "ok"]):
        return "smalltalk", entities
    return "unknown", entities


async def _classify(message: str, order_draft: dict | None) -> tuple[str, dict]:
    """Return (intent, entities) using the LLM, falling back to keywords."""
    draft_hint = ""
    if order_draft:
        draft_hint = (
            "\nNOTE: We are mid-order with this draft already captured: "
            + json.dumps(order_draft)
            + "\nExtract any NEW entities from the user's message and set intent=place_order."
        )
    prompt = _SYSTEM_PROMPT + "\nUser message: " + message + draft_hint
    raw = await safe_llm_call(
        [SystemMessage(content=prompt), HumanMessage(content=message)],
        fallback="",
    )
    try:
        data = _parse_json(raw)
        intent = data.get("intent", "unknown")
        if intent not in _INTENT_NAMES:
            intent = "unknown"
        entities = data.get("entities") or {}
        if not isinstance(entities, dict):
            entities = {}
        entities = {k: entities.get(k) for k in
                    ("product_name", "quantity", "customer_name", "contact", "address", "product_id", "category")}
        intent = _apply_draft_routing(intent, order_draft)
        return intent, entities
    except Exception:  # noqa: BLE001 - fall back to deterministic classifier
        log.warning("LLM classification failed; using keyword fallback")
        intent, entities = _keyword_fallback(message)
        intent = _apply_draft_routing(intent, order_draft)
        return intent, entities


def _apply_draft_routing(intent: str, order_draft: dict | None) -> str:
    """While an order draft is open, keep the conversation in the order flow
    unless the user explicitly asks an information question."""
    if not order_draft:
        return intent
    if intent in ("ask_company", "ask_products", "ask_price"):
        return intent  # let the user ask a quick question mid-order
    return "place_order"


async def chat_agent_node(state: AgentState) -> dict:
    """Classify intent, extract entities, and route or answer."""
    message = state["messages"][-1].content if state["messages"] else ""
    order_draft = state.get("order_draft")

    async with agent_trace(
        state["session_id"], "chat", "classify_intent", {"message": message}
    ) as tr:
        intent, entities = await _classify(message, order_draft)

        reply = ""
        next_agent = ""
        merged = None

        if intent in ("ask_company", "ask_products", "ask_price"):
            # Delegate to the catalog agent — no reply yet.
            next_agent = "catalog_agent"
        elif intent == "place_order":
            # Merge extracted entities into the running order draft.
            merged = dict(order_draft or {})
            for k in ("product_name", "product_id", "quantity", "customer_name", "contact", "address", "category"):
                v = entities.get(k)
                if v not in (None, ""):
                    merged[k] = v
            next_agent = "order_agent"
        else:
            # smalltalk / unknown — answer directly and end the turn.
            reply = await safe_llm_call(
                [
                    SystemMessage(
                        content="You are Multivisions' friendly sales assistant. Reply concisely."
                    ),
                    HumanMessage(content=message),
                ],
                fallback="Thanks for chatting with Multivisions! How can I help you today?",
            )
            next_agent = ""

        tr.set_output({"intent": intent, "entities": entities, "reply": reply, "order_draft": merged})

    update: dict = {
        "intent": intent,
        "entities": entities,
        "next_agent": next_agent,
        "trace": state["trace"] + [tr.entry],
    }
    if merged is not None:
        update["order_draft"] = merged
    if reply:
        update["messages"] = [AIMessage(content=reply)]
    return update


def route_from_chat(state: AgentState) -> str:
    """Conditional edge after the chat agent."""
    return state.get("next_agent") or "__END__"
