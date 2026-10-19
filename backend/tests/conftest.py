"""Shared pytest fixtures: a dummy Gemini key + a temp SQLite DB + temp data dir."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the repo root is importable and a dummy API key is present BEFORE
# importing any app module (config fails loudly without GEMINI_API_KEY).
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "backend"))
os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture()
def data_dir(tmp_path: Path, monkeypatch):
    """Point the app's DATA_DIR at a temp dir with seed files."""
    import json

    d = tmp_path / "data"
    d.mkdir()
    (d / "company.json").write_text(json.dumps({
        "name": "Test Co", "tagline": "t", "description": "d", "email": "e@x.com",
        "phone": "1", "address": "a", "website": "w", "working_hours": "9-5",
        "socials": {"linkedin": "", "twitter": "", "facebook": ""},
    }))
    (d / "products.json").write_text(json.dumps([
        {"id": "P001", "name": "Widget", "category": "Gadgets", "description": "d",
         "price": 10.0, "currency": "USD", "stock": 5, "image_url": "",
         "tags": ["gadget"], "active": True},
    ]))
    (d / "pricing.json").write_text(json.dumps({
        "tiers": [{"name": "standard", "min_qty": 1, "discount_pct": 0}],
        "tax_pct": 5,
    }))

    from app.config import settings

    monkeypatch.setattr(settings, "data_dir", d)
    return d
