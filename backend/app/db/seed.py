"""Seed sample orders on first run so the dashboard isn't empty."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order
from app.repositories import order_repo
from app.utils.logger import get_logger

log = get_logger("seed")

# (product_id, quantity, customer_name, contact, address, status)
_SAMPLE_ORDERS = [
    ("P001", 2, "Aisha Rahman", "+91-9876543210", "12 Lake View, Mumbai", "delivered"),
    ("P003", 1, "Daniel Okafor", "+234-8012345678", "8 Market Road, Lagos", "shipped"),
    ("P002", 5, "Mei Lin", "+65-91234567", "22 Orchard Blvd, Singapore", "confirmed"),
]


async def seed_sample_orders(session: AsyncSession, catalog: dict) -> None:
    """Insert sample orders if the orders table is empty."""
    existing = await session.scalar(select(func.count(Order.id)))
    if existing:
        return

    for product_id, qty, name, contact, address, status in _SAMPLE_ORDERS:
        product = catalog.get(product_id)
        if not product:
            continue
        unit_price = float(product["price"])
        order = await order_repo.create_order_with_items(
            session,
            customer_name=name,
            contact=contact,
            address=address,
            notes=None,
            items=[
                {
                    "product_id": product_id,
                    "product_name": product["name"],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "subtotal": round(unit_price * qty, 2),
                }
            ],
        )
        if status != "pending":
            await order_repo.update_order_status(session, order.id, status)

    log.info("Seeded %d sample orders", len(_SAMPLE_ORDERS))
