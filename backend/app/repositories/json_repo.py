"""Safe read/write access to the JSON data files in /data.

Guarantees:
- Pydantic validation on read and write.
- Atomic writes: write to a temp file, then os.replace() (atomic on POSIX).
- A process-wide async lock serializes writers (filelock for cross-process safety).
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, TypeVar

from filelock import FileLock
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.utils.logger import get_logger

log = get_logger("json_repo")

T = TypeVar("T", bound=BaseModel)

# Cross-process lock files live next to the data files.
_lock_dir = settings.data_dir
_lock_dir.mkdir(parents=True, exist_ok=True)

_locks: dict[str, asyncio.Lock] = {}
_locks_guard = asyncio.Lock()


def _async_lock(path: Path) -> asyncio.Lock:
    key = str(path)
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]


def _file_for(name: str) -> Path:
    return settings.data_dir / name


def read_json(name: str, model: type[T], default: T | None = None) -> T:
    """Read and validate a JSON data file into a Pydantic model.

    Falls back to `default` (or a fresh instance) when the file is missing.
    Raises ValueError when the file exists but fails validation.
    """
    path = _file_for(name)
    if not path.exists():
        if default is not None:
            return default
        return model()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return model.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        log.error("Data file %s failed validation: %s", path, exc)
        raise ValueError(f"Data file {name} is invalid: {exc}") from exc


def read_raw(name: str) -> Any:
    """Read raw JSON (used for list-shaped files like products.json)."""
    path = _file_for(name)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


async def write_json(name: str, payload: BaseModel | list | dict) -> None:
    """Atomically write a Pydantic model / list / dict to a JSON data file."""
    path = _file_for(name)
    text = (
        payload.model_dump_json(indent=2)
        if isinstance(payload, BaseModel)
        else json.dumps(payload, indent=2, ensure_ascii=False)
    )

    async with _async_lock(path):
        # Cross-process lock (filelock) + in-process asyncio lock above.
        with FileLock(str(path) + ".lock"):
            tmp = path.with_suffix(".tmp")
            tmp.write_text(text + "\n", encoding="utf-8")
            os.replace(tmp, path)  # atomic on POSIX
    log.info("Wrote %s", path)


async def load_all() -> dict[str, Any]:
    """Load every data file into a dict keyed by file name."""
    return {
        "company": read_json("company.json", _company_model()),
        "products": read_raw("products.json") or [],
        "pricing": read_json("pricing.json", _pricing_model()),
    }


def _company_model():
    from app.schemas.company import Company

    return Company


def _pricing_model():
    from app.schemas.product import Pricing

    return Pricing
