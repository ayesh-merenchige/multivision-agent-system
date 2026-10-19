"""Products CRUD — backed by /data/products.json."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories import json_repo
from app.schemas.product import Product, ProductCreate, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


def _read_all() -> list[Product]:
    raw = json_repo.read_raw("products.json") or []
    return [Product.model_validate(p) for p in raw]


async def _write_all(products: list[Product]) -> None:
    await json_repo.write_json("products.json", [p.model_dump() for p in products])


@router.get("", response_model=list[Product])
@router.get("/", response_model=list[Product])
async def list_products(
    category: str | None = Query(default=None),
    active: bool | None = Query(default=None),
):
    products = _read_all()
    if category:
        products = [p for p in products if p.category == category]
    if active is not None:
        products = [p for p in products if p.active == active]
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    for p in _read_all():
        if p.id == product_id:
            return p
    raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")


@router.post("", response_model=Product, status_code=201)
@router.post("/", response_model=Product, status_code=201)
async def create_product(payload: ProductCreate):
    products = _read_all()
    if any(p.id == payload.id for p in products):
        raise HTTPException(status_code=409, detail=f"Product id '{payload.id}' already exists")
    product = Product.model_validate(payload.model_dump())
    products.append(product)
    await _write_all(products)
    return product


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: str, update: ProductUpdate):
    products = _read_all()
    for i, p in enumerate(products):
        if p.id == product_id:
            products[i] = p.model_copy(update=update.model_dump(exclude_unset=True))
            await _write_all(products)
            return products[i]
    raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str):
    products = _read_all()
    remaining = [p for p in products if p.id != product_id]
    if len(remaining) == len(products):
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    await _write_all(remaining)
