"""
backend/routers/bias.py
POST /analyze-dataset
Hybrid bias detection: deterministic stats → Gemini interpretation.
"""

import hashlib
import io
import json
from fastapi import APIRouter, File, UploadFile, HTTPException
import pandas as pd

from backend.services.bias_stats import compute_bias_metrics
from backend.services.gemini_service import call_gemini_safe, build_bias_prompt
from backend.middleware.cache_middleware import get_cached, set_cached, make_key
from backend.config import CACHE_TTL_BIAS

router = APIRouter()


@router.post("/analyze-dataset")
async def analyze_dataset(file: UploadFile = File(...)):
    """
    Accepts a CSV file. Returns a structured bias report.

    Pipeline:
      1. Parse CSV
      2. Compute deterministic statistical metrics (bias_stats.py)
      3. Pass metrics + sample rows to Gemini for interpretation
      4. Merge: statistical risk_scores + Gemini narrative
    """
    # ── Read file ─────────────────────────────────────────────────────────────
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    required_cols = {"age", "gender", "income", "loan_amount",
                     "pin_code", "employment_type", "credit_score", "outcome"}
    missing = required_cols - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}"
        )

    # ── Cache key: SHA256 of file bytes ──────────────────────────────────────
    file_hash = hashlib.sha256(content).hexdigest()[:32]
    cache_key  = make_key("bias", file_hash)

    # ── 1. Deterministic stats (always computed — forms the factual base) ─────
    try:
        computed_metrics = compute_bias_metrics(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check cache AFTER computing stats (stats are fast; Gemini call is cached)
    cached = get_cached(cache_key, ttl=CACHE_TTL_BIAS)
    if cached:
        # Return cached Gemini response but always include fresh stats
        cached["computed_metrics"] = computed_metrics
        return cached

    # ── 2. Build Gemini prompt with pre-computed metrics ──────────────────────
    sample_rows = df.head(20).to_csv(index=False)
    prompt = build_bias_prompt(computed_metrics, sample_rows)

    # ── 3. Call Gemini (with timeout + fallback) ──────────────────────────────
    gemini_result = await call_gemini_safe(
        prompt=prompt,
        cache_key=cache_key,
        fallback_endpoint="bias",
        ttl=CACHE_TTL_BIAS,
    )

    # ── 4. Merge: ensure risk_scores from stats are authoritative ────────────
    if "top_risky_features" in gemini_result:
        stat_scores = {
            f["feature"]: f["risk_score"]
            for f in computed_metrics.get("top_risky_features", [])
        }
        for feat in gemini_result["top_risky_features"]:
            fname = feat.get("feature", "")
            if fname in stat_scores:
                feat["risk_score"] = stat_scores[fname]  # stats override AI

    response = {
        **gemini_result,
        "computed_metrics": computed_metrics,
        "dataset_rows":     len(df),
        "_fallback":        gemini_result.get("_fallback", False),
    }
    set_cached(cache_key, response)
    return response
