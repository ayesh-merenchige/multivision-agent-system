"""Pydantic schemas for products and pricing."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="General", max_length=100)
    description: str = ""
    price: float = Field(ge=0)
    currency: str = Field(default="USD", max_length=10)
    stock: int = Field(default=0, ge=0)
    image_url: str = ""
    tags: list[str] = Field(default_factory=list)
    active: bool = True


class ProductCreate(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="General", max_length=100)
    description: str = ""
    price: float = Field(ge=0)
    currency: str = Field(default="USD", max_length=10)
    stock: int = Field(default=0, ge=0)
    image_url: str = ""
    tags: list[str] = Field(default_factory=list)
    active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    tags: list[str] | None = None
    active: bool | None = None


class PricingTier(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    min_qty: int = Field(ge=0)
    discount_pct: float = Field(ge=0, le=100)


class Pricing(BaseModel):
    tiers: list[PricingTier] = Field(default_factory=list)
    tax_pct: float = Field(default=0, ge=0, le=100)


class PricingUpdate(BaseModel):
    tiers: list[PricingTier] | None = None
    tax_pct: float | None = Field(default=None, ge=0, le=100)
