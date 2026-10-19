"""Company CRUD — backed by /data/company.json."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories import json_repo
from app.schemas.company import Company, CompanyUpdate

router = APIRouter(prefix="/api/company", tags=["company"])


@router.get("", response_model=Company)
@router.get("/", response_model=Company)
async def get_company():
    return json_repo.read_json("company.json", Company)


@router.put("", response_model=Company)
@router.put("/", response_model=Company)
async def update_company(update: CompanyUpdate):
    current = json_repo.read_json("company.json", Company)
    updated = current.model_copy(update=update.model_dump(exclude_unset=True))
    await json_repo.write_json("company.json", updated)
    return updated
