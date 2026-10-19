"""Catalog agent — the source of truth for company info, products, and pricing.

Always grounds answers in the actual JSON data (via the catalog tools) and
formats them with the LLM, falling back to templates when the LLM is down.
"""
from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import safe_llm_call
from app.agents.state import AgentState
from app.agents.tools import get_company_details, get_price, list_products, search_products
from app.utils.tracer import agent_trace

_FORMAT_PROMPT = """You are Multivisions' sales assistant. Using ONLY the data below, write a friendly, concise answer to the user's query. Never invent products, prices, or facts. If the data says something is not available, say so politely.

Data:
{data}

Query context: {context}
"""


async def _format(data: dict | list, context: str, fallback: str) -> str:
    payload = json.dumps(data, ensure_ascii=False, default=str)
    reply = await safe_llm_call(
        [
            SystemMessage(
                content="You are Multivisions' sales assistant. Answer concisely and never invent data."
            ),
            HumanMessage(content=_FORMAT_PROMPT.format(data=payload, context=context)),
        ],
        fallback=fallback,
    )
    return reply


def _company_fallback(data: dict) -> str:
    lines = [f"**{data.get('name', 'Our company')}**"]
    if data.get("tagline"):
        lines.append(f"_{data['tagline']}_")
    if data.get("description"):
        lines.append(data["description"])
    if data.get("email"):
        lines.append(f"\nEmail: {data['email']}")
    if data.get("phone"):
        lines.append(f"Phone: {data['phone']}")
    if data.get("address"):
        lines.append(f"Address: {data['address']}")
    if data.get("working_hours"):
        lines.append(f"Hours: {data['working_hours']}")
    return "\n".join(lines)


def _products_fallback(products: list) -> str:
    if not products:
        return "I couldn't find any products matching that. Try asking what products we sell."
    lines = ["Here are the products I found:"]
    for p in products[:10]:
        price = f"${p.get('price', 0):,.2f}"
        lines.append(f"- **{p.get('name')}** ({p.get('category', 'General')}) — {price}")
    return "\n".join(lines)


def _price_fallback(data: dict) -> str:
    if not data.get("found"):
        return f"Sorry, I couldn't find a product called '{data.get('product')}'. Try asking what products we sell."
    lines = [
        f"**{data.get('name')}** is priced at **${data.get('price', 0):,.2f}** {data.get('currency', 'USD')}."
    ]
    if data.get("stock") is not None:
        lines.append(f"Stock available: {data.get('stock')} units.")
    tiers = data.get("tiers") or []
    if tiers:
        tier_txt = ", ".join(
            f"{t.get('name')}: {t.get('discount_pct')}% off from {t.get('min_qty')}+ units"
            for t in tiers
        )
        lines.append(f"Volume discounts: {tier_txt}.")
    if data.get("tax_pct"):
        lines.append(f"A {data.get('tax_pct')}% tax applies at checkout.")
    return "\n".join(lines)


async def catalog_agent_node(state: AgentState) -> dict:
    """Answer an information query using the catalog tools."""
    intent = state.get("intent", "ask_products")
    entities = state.get("entities", {}) or {}

    async with agent_trace(
        state["session_id"], "catalog", f"answer_{intent}", {"intent": intent, "entities": entities}
    ) as tr:
        if intent == "ask_company":
            data = await get_company_details.ainvoke({})
            reply = await _format(data, "company details", _company_fallback(data))

        elif intent == "ask_price":
            ref = entities.get("product_name") or entities.get("product_id") or ""
            if not ref:
                reply = "Which product would you like the price for?"
            else:
                data = await get_price.ainvoke({"product_id_or_name": ref})
                data = data if isinstance(data, dict) else dict(data)
                data.setdefault("product", ref)
                reply = await _format(data, "product price", _price_fallback(data))

        else:  # ask_products
            query = entities.get("product_name") or entities.get("category") or ""
            if query:
                data = await search_products.ainvoke({"query": query})
            else:
                data = await list_products.ainvoke({"category": entities.get("category")})
            reply = await _format(data, "product list", _products_fallback(data))

        tr.set_output({"reply": reply})

    return {
        "messages": [AIMessage(content=reply)],
        "next_agent": "",
        "trace": state["trace"] + [tr.entry],
    }
