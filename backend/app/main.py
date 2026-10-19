"""FastAPI application entry point.

Startup: create SQLite tables, seed sample orders, compile the LangGraph graph.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.graph import get_graph
from app.config import settings
from app.db.models import Base
from app.db.seed import seed_sample_orders
from app.db.session import AsyncSessionLocal, engine
from app.repositories import json_repo
from app.routers import chat, company, orders, products, pricing, stats
from app.utils.logger import get_logger

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- create tables -----------------------------------------------------
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables created/verified")

    # --- seed sample orders --------------------------------------------------
    raw_products = json_repo.read_raw("products.json") or []
    catalog = {p["id"]: p for p in raw_products if "id" in p}
    async with AsyncSessionLocal() as session:
        await seed_sample_orders(session, catalog)

    # --- compile the graph once --------------------------------------------
    get_graph()
    log.info("Startup complete")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Multivisions API",
        description="Multi-agent business assistant — FastAPI + LangGraph + Gemini",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router)
    app.include_router(company.router)
    app.include_router(products.router)
    app.include_router(pricing.router)
    app.include_router(orders.router)
    app.include_router(stats.router)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "app": "multivisions"}

    return app


app = create_app()
