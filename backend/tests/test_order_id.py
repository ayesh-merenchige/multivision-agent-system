"""Tests for atomic order-ID generation (MV-YYYYMMDD-XXXX)."""
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
async def test_order_id_format(db):
    order_id = await order_repo.next_order_id(db)
    assert order_id.startswith("MV-")
    date_part, seq_part = order_id.split("-")[1], order_id.split("-")[2]
    assert len(date_part) == 8 and date_part.isdigit()
    assert len(seq_part) == 4 and seq_part.isdigit()


@pytest.mark.asyncio
async def test_order_id_sequential(db):
    first = await order_repo.next_order_id(db)
    second = await order_repo.next_order_id(db)
    assert first != second
    assert int(second.split("-")[2]) == int(first.split("-")[2]) + 1


@pytest.mark.asyncio
async def test_order_id_same_prefix_same_day(db):
    ids = [await order_repo.next_order_id(db) for _ in range(3)]
    prefixes = {i.rsplit("-", 1)[0] for i in ids}
    assert len(prefixes) == 1  # all share MV-YYYYMMDD
