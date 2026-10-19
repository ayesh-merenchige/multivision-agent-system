"""Application logging helper (stdout, structured)."""
from __future__ import annotations

import logging
import sys

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        )
        root = logging.getLogger("multivisions")
        root.setLevel(logging.INFO)
        if not root.handlers:
            root.addHandler(handler)
        _configured = True
    return logging.getLogger(f"multivisions.{name}")
