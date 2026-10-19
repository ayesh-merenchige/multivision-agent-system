"""Async SQLAlchemy engine + session factory (SQLite via aiosqlite)."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.config import settings

# Create the async engine once at import time and reuse it everywhere.
_engine_kwargs: dict = dict(
    echo=False,
    future=True,
    # SQLite needs to allow cross-thread usage when combined with sync tooling;
    # busy timeout (seconds) lets concurrent writers wait for the write lock.
    connect_args={"check_same_thread": False, "timeout": 30},
)
# In-memory SQLite requires a shared connection (StaticPool), otherwise every
# pooled connection gets its own empty database.
if ":memory:" in settings.database_url:
    _engine_kwargs["poolclass"] = StaticPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)

# Session factory bound to the engine.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a scoped async session."""
    async with AsyncSessionLocal() as session:
        yield session
