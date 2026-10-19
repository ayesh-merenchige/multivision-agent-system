"""Tests for the safe JSON data-file repository."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "backend"))
os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key")

import pytest

from app.repositories import json_repo
from app.schemas.company import Company
from app.schemas.product import Pricing


@pytest.fixture()
def data_dir(tmp_path: Path, monkeypatch):
    import json

    d = tmp_path / "data"
    d.mkdir()
    (d / "company.json").write_text(json.dumps({
        "name": "Test Co", "tagline": "t", "description": "d", "email": "e@x.com",
        "phone": "1", "address": "a", "website": "w", "working_hours": "9-5",
        "socials": {"linkedin": "", "twitter": "", "facebook": ""},
    }))
    (d / "pricing.json").write_text(json.dumps({
        "tiers": [{"name": "standard", "min_qty": 1, "discount_pct": 0}],
        "tax_pct": 5,
    }))
    from app.config import settings

    monkeypatch.setattr(settings, "data_dir", d)
    return d


@pytest.mark.asyncio
async def test_read_company(data_dir):
    company = json_repo.read_json("company.json", Company)
    assert company.name == "Test Co"


@pytest.mark.asyncio
async def test_write_is_atomic_and_validates(data_dir):
    company = json_repo.read_json("company.json", Company)
    company.tagline = "Updated"
    await json_repo.write_json("company.json", company)

    # Re-read and confirm persistence
    reread = json_repo.read_json("company.json", Company)
    assert reread.tagline == "Updated"

    # No leftover temp files
    leftovers = list(data_dir.glob("*.tmp"))
    assert leftovers == []


@pytest.mark.asyncio
async def test_missing_file_returns_default(data_dir):
    company = json_repo.read_json("nonexistent.json", Company, default=Company(name="Default"))
    assert company.name == "Default"


@pytest.mark.asyncio
async def test_invalid_file_raises(data_dir):
    (data_dir / "company.json").write_text("{ not valid json")
    with pytest.raises(ValueError):
        json_repo.read_json("company.json", Company)


@pytest.mark.asyncio
async def test_pricing_roundtrip(data_dir):
    pricing = json_repo.read_json("pricing.json", Pricing)
    assert pricing.tax_pct == 5
    pricing.tax_pct = 8
    await json_repo.write_json("pricing.json", pricing)
    assert json_repo.read_json("pricing.json", Pricing).tax_pct == 8
