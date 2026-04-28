"""
backend/middleware/fallback_middleware.py
Demo-safe fallback: returns pre-computed responses when Gemini fails/times out.
Pre-computed cache files are committed to the repo — demo works with zero network.
"""

import json
from pathlib import Path
from backend.config import CACHE_DIR


FALLBACK_FILES = {
    "bias":    CACHE_DIR / "bias_demo_cache.json",
    "explain": CACHE_DIR / "explain_demo_cache.json",
    "audit":   CACHE_DIR / "audit_demo_cache.json",
}


def get_fallback(endpoint: str, key: str = None) -> dict:
    """
    Returns pre-computed demo response for the given endpoint.
    Adds _fallback=True flag so UI can show subtle 'Cached ⚡' badge.

    For 'explain' endpoint: pass decision_id as `key` to retrieve per-case fallback.
    If key not found, returns first available entry.
    """
    path = FALLBACK_FILES.get(endpoint)
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))

        # Keyed lookup (explain endpoint stores {decision_id: {...}, ...})
        if key and isinstance(data, dict) and key in data:
            result = data[key]
            result["_fallback"] = True
            return result

        # If keyed but key not found, try first entry
        if key and isinstance(data, dict) and not data.get("_fallback"):
            first_key = next(iter(data), None)
            if first_key and isinstance(data[first_key], dict):
                result = data[first_key]
                result["_fallback"] = True
                return result

        # Standard (non-keyed) fallback
        if isinstance(data, dict):
            data["_fallback"] = True
        return data

    raise RuntimeError(
        f"No fallback available for endpoint '{endpoint}'. "
        f"Run scripts/generate_demo_cache.py to create it."
    )
