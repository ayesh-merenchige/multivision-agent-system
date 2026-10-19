"""Orders API — manual CRUD + status transitions (SQLite)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories import order_repo
from app.schemas.order import (
    OrderCreate,
    OrderCreated,
    OrderOut,
    OrderStatusUpdate,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=list[OrderOut])
@router.get("/", response_model=list[OrderOut])
async def list_orders(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    orders = await order_repo.list_orders(db, status=status, limit=limit)
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    order = await order_repo.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return OrderOut.model_validate(order)


@router.post("", response_model=OrderCreated, status_code=201)
@router.post("/", response_model=OrderCreated, status_code=201)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Manually create an order (unit prices resolved from the product catalog)."""
    from app.repositories import json_repo
    from app.schemas.product import Product

    raw = json_repo.read_raw("products.json") or []
    catalog = {p["id"]: p for p in raw}

    items = []
    for item in payload.items:
        product = catalog.get(item.product_id)
        if product is None:
            raise HTTPException(
                status_code=400, detail=f"Unknown product_id '{item.product_id}'"
            )
        unit_price = float(product["price"])
        items.append(
            {
                "product_id": item.product_id,
                "product_name": product["name"],
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": round(unit_price * item.quantity, 2),
            }
        )

    order = await order_repo.create_order_with_items(
        db,
        customer_name=payload.customer_name,
        contact=payload.contact,
        address=payload.address,
        notes=payload.notes,
        items=items,
    )
    return OrderCreated(
        order=OrderOut.model_validate(order),
        message=f"Order {order.id} created successfully.",
    )


@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_status(
    order_id: str, payload: OrderStatusUpdate, db: AsyncSession = Depends(get_db)
):
    order = await order_repo.update_order_status(db, order_id, payload.status)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return OrderOut.model_validate(order)
