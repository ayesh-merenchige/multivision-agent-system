"""Pydantic schemas for company data."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Socials(BaseModel):
    linkedin: str = ""
    twitter: str = ""
    facebook: str = ""


class Company(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    tagline: str = ""
    description: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    website: str = ""
    working_hours: str = ""
    socials: Socials = Socials()


class CompanyUpdate(BaseModel):
    """All fields optional — partial update semantics."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    tagline: str | None = None
    description: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    working_hours: str | None = None
    socials: Socials | None = None
