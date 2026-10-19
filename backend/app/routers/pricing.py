"""Pricing CRUD — backed by /data/pricing.json."""
from __future__ import annotations

from fastapi import APIRouter

from app.repositories import json_repo
from app.schemas.product import Pricing, PricingUpdate

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


@router.get("", response_model=Pricing)
@router.get("/", response_model=Pricing)
async def get_pricing():
    return json_repo.read_json("pricing.json", Pricing)


@router.put("", response_model=Pricing)
@router.put("/", response_model=Pricing)
async def update_pricing(update: PricingUpdate):
    current = json_repo.read_json("pricing.json", Pricing)
    updated = current.model_copy(update=update.model_dump(exclude_unset=True))
    await json_repo.write_json("pricing.json", updated)
    return updated
