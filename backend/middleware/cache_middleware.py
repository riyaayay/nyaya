"""
backend/middleware/cache_middleware.py
File-based cache with SHA256 keys and TTL awareness.
Works in LOCAL mode without Redis/Memcached.
"""

import hashlib
import json
import time
from pathlib import Path
from backend.config import CACHE_DIR


def _key_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def make_key(*parts: str) -> str:
    """SHA256 of concatenated parts → stable cache key."""
    raw = ":".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def get_cached(key: str, ttl: int = 3600) -> dict | None:
    """Return cached value if exists and not expired, else None."""
    path = _key_path(key)
    if not path.exists():
        return None
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - envelope.get("_ts", 0) < ttl:
            return envelope.get("data")
    except Exception:
        pass
    return None


def set_cached(key: str, value: dict) -> None:
    """Write value to cache with current timestamp."""
    path = _key_path(key)
    envelope = {"_ts": time.time(), "data": value}
    path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
