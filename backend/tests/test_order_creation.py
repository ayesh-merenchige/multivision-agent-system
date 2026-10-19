"""Tests for order creation + persistence."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "backend"))
os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key")

import pytest

from app.db.models import Base
from app.db.session import AsyncSessionLocal, engine
from app.repositories import order_repo


@pytest.fixture()
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_order_persists_items(db):
    order = await order_repo.create_order_with_items(
        db,
        customer_name="Jane Doe",
        contact="jane@example.com",
        address="1 Main St",
        notes=None,
        items=[
            {
                "product_id": "P001",
                "product_name": "Widget",
                "quantity": 3,
                "unit_price": 10.0,
                "subtotal": 30.0,
            }
        ],
    )
    assert order.id.startswith("MV-")
    assert order.status == "pending"
    assert order.total_amount == 30.0
    assert len(order.items) == 1
    assert order.items[0].product_name == "Widget"


@pytest.mark.asyncio
async def test_get_order(db):
    created = await order_repo.create_order_with_items(
        db, "A", "c", "addr", None,
        [{"product_id": "P001", "product_name": "W", "quantity": 1,
          "unit_price": 5.0, "subtotal": 5.0}],
    )
    fetched = await order_repo.get_order(db, created.id)
    assert fetched is not None
    assert fetched.customer_name == "A"


@pytest.mark.asyncio
async def test_update_status(db):
    created = await order_repo.create_order_with_items(
        db, "A", "c", "addr", None,
        [{"product_id": "P001", "product_name": "W", "quantity": 1,
          "unit_price": 5.0, "subtotal": 5.0}],
    )
    updated = await order_repo.update_order_status(db, created.id, "confirmed")
    assert updated.status == "confirmed"


@pytest.mark.asyncio
async def test_list_orders_filter_by_status(db):
    o1 = await order_repo.create_order_with_items(
        db, "A", "c", "addr", None,
        [{"product_id": "P001", "product_name": "W", "quantity": 1,
          "unit_price": 5.0, "subtotal": 5.0}],
    )
    await order_repo.create_order_with_items(
        db, "B", "c", "addr", None,
        [{"product_id": "P002", "product_name": "X", "quantity": 1,
          "unit_price": 7.0, "subtotal": 7.0}],
    )
    await order_repo.update_order_status(db, o1.id, "shipped")

    pending = await order_repo.list_orders(db, status="pending")
    shipped = await order_repo.list_orders(db, status="shipped")
    assert len(pending) == 1
    assert len(shipped) == 1
    assert shipped[0].id == o1.id
