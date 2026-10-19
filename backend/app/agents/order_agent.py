"""Order agent — handles the complete order lifecycle.

Collects order fields across turns (via the shared order draft), resolves
pricing with tier discounts + tax, persists the order, and confirms.
"""
from __future__ import annotations

from langchain_core.messages import AIMessage

from app.agents.state import AgentState
from app.agents.tools import create_order, get_price
from app.repositories.json_repo import read_json
from app.schemas.product import Pricing
from app.utils.tracer import agent_trace

_REQUIRED_FIELDS = ("product_name", "quantity", "customer_name", "contact", "address")


def _coerce_quantity(value) -> int | None:
    try:
        qty = int(str(value).strip())
        return qty if qty > 0 else None
    except (TypeError, ValueError):
        return None


def _find_tier_discount(tiers: list, qty: int) -> float:
    """Best (highest) discount tier whose min_qty is satisfied."""
    applicable = [t for t in tiers if qty >= t.min_qty]
    if not applicable:
        return 0.0
    return max(t.discount_pct for t in applicable)


def _confirmation_message(result: dict, product_name: str, qty: int,
                          unit_price: float, discount_pct: float, tax_pct: float) -> str:
    lines = [
        f"✅ Order placed successfully! Your order id is **{result['order_id']}**.",
        "",
        f"- **{product_name}** × {qty} — ${unit_price:,.2f} each",
    ]
    if discount_pct:
        lines.append(f"- Volume discount applied: {discount_pct:.0f}%")
    if tax_pct:
        lines.append(f"- Tax: {tax_pct:.0f}%")
    lines += [
        "",
        f"**Total: ${result['total_amount']:,.2f}**",
        f"Status: {result['status']}",
        "",
        "Thank you for ordering with Multivisions! We'll contact you shortly to confirm delivery.",
    ]
    return "\n".join(lines)


def _missing_fields_message(missing: list[str]) -> str:
    friendly = {
        "product_name": "the product you'd like to order",
        "quantity": "the quantity",
        "customer_name": "your name",
        "contact": "your contact (phone or email)",
        "address": "your delivery address",
    }
    items = "\n".join(f"- {friendly.get(f, f)}" for f in missing)
    return (
        "I'd be happy to help you place that order! I still need a few details:\n"
        + items
        + "\n\nPlease share them and I'll confirm your order."
    )


async def order_agent_node(state: AgentState) -> dict:
    """Validate the order draft, price it, persist it, and confirm."""
    draft = dict(state.get("order_draft") or {})
    entities = state.get("entities", {}) or {}

    # Merge any newly extracted entities into the draft.
    for k in ("product_name", "product_id", "quantity", "customer_name", "contact", "address"):
        v = entities.get(k)
        if v not in (None, ""):
            draft[k] = v
    if draft.get("quantity") is not None:
        draft["quantity"] = _coerce_quantity(draft["quantity"])

    async with agent_trace(
        state["session_id"], "order", "handle_order", {"draft": draft}
    ) as tr:
        missing = [f for f in _REQUIRED_FIELDS if not draft.get(f)]
        result = None
        reply = ""
        next_agent = ""

        if missing:
            reply = _missing_fields_message(missing)
            next_agent = "chat_agent"  # collect details in the next turn(s)
        else:
            price_data = await get_price.ainvoke({"product_id_or_name": draft["product_name"]})
            price_data = price_data if isinstance(price_data, dict) else dict(price_data)

            if not price_data.get("found"):
                reply = (
                    f"Sorry, I couldn't find a product called '{draft['product_name']}'. "
                    "Try asking what products we sell."
                )
                next_agent = "chat_agent"
            else:
                pricing = read_json("pricing.json", Pricing)
                qty = int(draft["quantity"])
                unit_price = float(price_data["price"])
                discount_pct = _find_tier_discount(pricing.tiers, qty)
                tax_pct = pricing.tax_pct

                discounted_unit = round(unit_price * (1 - discount_pct / 100), 2)
                subtotal = round(discounted_unit * qty, 2)
                total = round(subtotal * (1 + tax_pct / 100), 2)

                result = await create_order.ainvoke(
                    {
                        "customer_name": draft["customer_name"],
                        "contact": draft["contact"],
                        "address": draft["address"],
                        "items": [
                            {
                                "product_id": price_data.get("product_id", draft.get("product_id", "")),
                                "product_name": price_data.get("name", draft["product_name"]),
                                "quantity": qty,
                                "unit_price": discounted_unit,
                                "subtotal": subtotal,
                            }
                        ],
                        "notes": "",
                        "total_amount": total,
                    }
                )
                reply = _confirmation_message(
                    result, price_data.get("name", draft["product_name"]),
                    qty, unit_price, discount_pct, tax_pct,
                )
                next_agent = ""

        tr.set_output({"reply": reply, "order_draft": draft, "order_result": result})

    return {
        "messages": [AIMessage(content=reply)],
        "order_draft": draft,
        "order_result": result,
        "next_agent": next_agent,
        "trace": state["trace"] + [tr.entry],
    }
