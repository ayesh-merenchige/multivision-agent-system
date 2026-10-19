"""Stats API — agent activity metrics, KPIs, timeline, recent activity."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentLog, ChatSession, Order
from app.db.session import get_db
from app.repositories import log_repo, order_repo

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    order_stats = await order_repo.stats_overview(db)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    active_sessions = int(
        await db.scalar(
            select(func.count(ChatSession.id)).where(ChatSession.updated_at >= since)
        )
        or 0
    )
    agent_calls = await log_repo.calls_last_24h(db)
    return {
        "total_orders": order_stats["total_orders"],
        "revenue": order_stats["revenue"],
        "active_sessions": active_sessions,
        "agent_calls": agent_calls,
    }


@router.get("/agents")
async def agents(db: AsyncSession = Depends(get_db)):
    return await log_repo.agent_stats(db)


@router.get("/timeline")
async def timeline(days: int = Query(default=7, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    return await log_repo.timeline(db, days=days)


@router.get("/recent-activity")
async def recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    agent: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    logs = await log_repo.recent_logs(db, limit=limit, agent=agent)
    return [
        {
            "id": log.id,
            "session_id": log.session_id,
            "agent": log.agent_name,
            "action": log.action,
            "status": log.status,
            "latency_ms": log.latency_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/orders-by-status")
async def orders_by_status(db: AsyncSession = Depends(get_db)):
    """Order counts per status (for the dashboard pie chart)."""
    rows = await db.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    )
    return [{"status": status, "count": int(count)} for status, count in rows.all()]
