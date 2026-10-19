"""Order persistence: CRUD + atomic order-ID generation."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Counter, Order, OrderItem


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


async def next_order_id(session: AsyncSession) -> str:
    """Generate the next sequential order id for today: MV-YYYYMMDD-XXXX.

    Increments the per-day counter row on the caller's current transaction
    (autobegun or explicit) so the counter bump commits atomically with the
    order insert. SQLite serializes write transactions, so concurrent
    requests cannot receive the same sequence number.
    """
    today = _today()
    result = await session.execute(
        select(Counter).where(Counter.date == today)
    )
    counter = result.scalar_one_or_none()
    if counter is None:
        counter = Counter(date=today, value=1)
        session.add(counter)
        await session.flush()
        seq = 1
    else:
        counter.value += 1
        seq = counter.value
    return f"MV-{today}-{seq:04d}"


async def create_order_with_items(
    session: AsyncSession,
    customer_name: str,
    contact: str,
    address: str,
    notes: str | None,
    items: list[dict],
    total_amount: float | None = None,
) -> Order:
    """Create an order from fully-resolved items.

    Each item dict: {product_id, product_name, quantity, unit_price, subtotal}.
    ``total_amount`` overrides the computed sum (e.g. to include tax).
    """
    order_id = await next_order_id(session)

    total = round(total_amount if total_amount is not None
                  else sum(i["subtotal"] for i in items), 2)
    order = Order(
        id=order_id,
        customer_name=customer_name,
        contact=contact,
        address=address,
        notes=notes,
        status="pending",
        total_amount=total,
    )
    for i in items:
        order.items.append(
            OrderItem(
                order_id=order_id,
                product_id=i["product_id"],
                product_name=i["product_name"],
                quantity=i["quantity"],
                unit_price=i["unit_price"],
                subtotal=i["subtotal"],
            )
        )
    session.add(order)
    await session.commit()
    await session.refresh(order, attribute_names=["items"])
    return order


async def get_order(session: AsyncSession, order_id: str) -> Order | None:
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def list_orders(
    session: AsyncSession, status: str | None = None, limit: int = 50
) -> list[Order]:
    stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Order.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_order_status(
    session: AsyncSession, order_id: str, status: str
) -> Order | None:
    order = await get_order(session, order_id)
    if order is None:
        return None
    order.status = status
    await session.commit()
    await session.refresh(order, attribute_names=["items"])
    return order


async def stats_overview(session: AsyncSession) -> dict:
    total_orders = await session.scalar(select(func.count(Order.id))) or 0
    revenue = (
        await session.scalar(
            select(func.coalesce(func.sum(Order.total_amount), 0.0)).where(
                Order.status != "cancelled"
            )
        )
        or 0.0
    )
    return {"total_orders": int(total_orders), "revenue": round(float(revenue), 2)}
