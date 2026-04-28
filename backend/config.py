"""
backend/config.py
Central configuration. All secrets come from environment variables.
Supports two modes:
  - LOCAL mode: uses local JSON files instead of Firestore/BigQuery
  - GCP mode:   uses real Firestore + BigQuery (set USE_GCP=true)
"""

import os
from pathlib import Path

# ── Gemini / Vertex AI ────────────────────────────────────────────────────────
# Option A: Google AI Studio (free tier)
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY", "")

# Option B: Vertex AI (GCP billing required)
GCP_PROJECT_ID   = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION     = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL     = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# Automatically pick Vertex if project is set, else fall back to AI Studio
USE_VERTEX_AI    = bool(GCP_PROJECT_ID)

# ── Cloud mode toggle ─────────────────────────────────────────────────────────
# Set USE_GCP=true to use real Firestore + BigQuery
# Leave unset for fully local demo (no cloud needed)
USE_GCP = os.getenv("USE_GCP", "false").lower() == "true"

# ── Firestore ─────────────────────────────────────────────────────────────────
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "decisions")

# ── BigQuery ──────────────────────────────────────────────────────────────────
BQ_DATASET  = os.getenv("BQ_DATASET", "nyaya_decisions")
BQ_TABLE    = os.getenv("BQ_TABLE", "decisions")

# ── Local data paths (LOCAL mode) ─────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent.parent
ML_DATA_DIR     = BASE_DIR / "ml" / "data"
ML_MODELS_DIR   = BASE_DIR / "ml" / "models"
CACHE_DIR       = BASE_DIR / "backend" / "cache"
LOCAL_DECISIONS = ML_DATA_DIR / "decisions.json"

# ── Cache / demo stability ────────────────────────────────────────────────────
CACHE_TTL_BIAS    = 3600   # 1 hour
CACHE_TTL_EXPLAIN = 86400  # 24 hours
CACHE_TTL_AUDIT   = 1800   # 30 minutes
GEMINI_TIMEOUT    = 15.0   # seconds before falling back to cache

# ── SHAP ──────────────────────────────────────────────────────────────────────
GENDER_PROXY_THRESHOLD = 0.30  # SHAP gender proxy > this → flag decision

# ── API ───────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")


def validate():
    """
    Called at startup. Warns about missing optional config.
    Does NOT hard-fail on missing keys — LOCAL mode works without them.
    """
    issues = []
    if not GOOGLE_API_KEY and not GCP_PROJECT_ID:
        issues.append(
            "No Gemini credentials found. Set GOOGLE_API_KEY (AI Studio) "
            "or GCP_PROJECT_ID (Vertex AI). Fallback cache will be used."
        )
    if USE_GCP and not GCP_PROJECT_ID:
        issues.append("USE_GCP=true but GCP_PROJECT_ID is not set.")
    for msg in issues:
        print(f"[WARN]  CONFIG WARNING: {msg}")
    return issues

