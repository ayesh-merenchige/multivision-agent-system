"""LangChain @tool functions used by the Catalog and Order agents.

The catalog tools read the JSON data store; the order tools persist to SQLite.
Nodes invoke these directly (rather than via LLM tool-calling) for reliability,
while still exposing them as proper LangChain tools.
"""
from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from app.db.session import AsyncSessionLocal
from app.repositories import order_repo
from app.repositories import json_repo


# ---------------------------------------------------------------------------
# Catalog tools
# ---------------------------------------------------------------------------


@tool
async def get_company_details() -> dict:
    """Return the company profile (name, tagline, contact, address, hours)."""
    from app.schemas.company import Company

    company = json_repo.read_json("company.json", Company)
    return company.model_dump()


@tool
async def list_products(category: Optional[str] = None) -> list:
    """List products, optionally filtered by category. Only active products."""
    raw = json_repo.read_raw("products.json") or []
    products = [p for p in raw if p.get("active", True)]
    if category:
        products = [p for p in products if p.get("category") == category]
    return products


@tool
async def get_product(product_id_or_name: str) -> dict:
    """Find a single product by its id or exact/partial name."""
    raw = json_repo.read_raw("products.json") or []
    query = product_id_or_name.strip().lower()
    for p in raw:
        if p.get("id", "").lower() == query:
            return p
    for p in raw:
        if p.get("name", "").lower() == query:
            return p
    for p in raw:
        if query in p.get("name", "").lower():
            return p
    return {}


@tool
async def get_price(product_id_or_name: str) -> dict:
    """Return price + tier/tax context for a product."""
    from app.schemas.product import Pricing

    product = (await get_product.ainvoke({"product_id_or_name": product_id_or_name})) or {}
    if not product:
        return {"found": False, "product": product_id_or_name}
    pricing = json_repo.read_json("pricing.json", Pricing)
    return {
        "found": True,
        "product_id": product.get("id"),
        "name": product.get("name"),
        "price": product.get("price"),
        "currency": product.get("currency", "USD"),
        "stock": product.get("stock", 0),
        "tiers": [t.model_dump() for t in pricing.tiers],
        "tax_pct": pricing.tax_pct,
    }


@tool
async def search_products(query: str) -> list:
    """Fuzzy word search across product name, category, description and tags."""
    raw = json_repo.read_raw("products.json") or []
    terms = [t for t in query.lower().split() if t]
    scored: list[tuple[int, dict]] = []
    for p in raw:
        if not p.get("active", True):
            continue
        haystack = " ".join(
            [
                p.get("name", ""),
                p.get("category", ""),
                p.get("description", ""),
                " ".join(p.get("tags", [])),
            ]
        ).lower()
        score = sum(1 for t in terms if t in haystack)
        if score:
            scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored]


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------


@tool
async def generate_order_id() -> str:
    """Generate the next sequential order id (MV-YYYYMMDD-XXXX)."""
    async with AsyncSessionLocal() as session:
        return await order_repo.next_order_id(session)


@tool
async def create_order(
    customer_name: str,
    contact: str,
    address: str,
    items: list[dict],
    notes: str = "",
    total_amount: float | None = None,
) -> dict:
    """Persist a new order. items: [{product_id, product_name, quantity, unit_price, subtotal}]."""
    async with AsyncSessionLocal() as session:
        order = await order_repo.create_order_with_items(
            session, customer_name, contact, address, notes, items,
            total_amount=total_amount,
        )
    return {
        "order_id": order.id,
        "customer_name": order.customer_name,
        "status": order.status,
        "total_amount": order.total_amount,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "subtotal": i.subtotal,
            }
            for i in order.items
        ],
    }


@tool
async def get_order(order_id: str) -> dict:
    """Fetch an order by id."""
    async with AsyncSessionLocal() as session:
        order = await order_repo.get_order(session, order_id)
    if order is None:
        return {"found": False, "order_id": order_id}
    return {
        "found": True,
        "order_id": order.id,
        "customer_name": order.customer_name,
        "status": order.status,
        "total_amount": order.total_amount,
    }


@tool
async def list_orders(status: Optional[str] = None) -> list:
    """List recent orders, optionally filtered by status."""
    async with AsyncSessionLocal() as session:
        orders = await order_repo.list_orders(session, status=status, limit=50)
    return [
        {"order_id": o.id, "customer_name": o.customer_name, "status": o.status,
         "total_amount": o.total_amount}
        for o in orders
    ]


@tool
async def update_order_status(order_id: str, status: str) -> dict:
    """Update an order's status (pending|confirmed|shipped|delivered|cancelled)."""
    async with AsyncSessionLocal() as session:
        order = await order_repo.update_order_status(session, order_id, status)
    if order is None:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order.id, "status": order.status}
