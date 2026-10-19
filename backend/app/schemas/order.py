"""Pydantic schemas for orders."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import utcnow


class OrderItemIn(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class OrderItemOut(BaseModel):
    id: int
    order_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    customer_name: str
    contact: str
    address: str
    notes: str | None
    status: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    contact: str = Field(min_length=1, max_length=200)
    address: str = ""
    notes: str | None = None
    items: list[OrderItemIn] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|confirmed|shipped|delivered|cancelled)$")


class OrderCreated(BaseModel):
    order: OrderOut
    message: str
