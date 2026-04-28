"""
backend/main.py
FastAPI application entry point.
"""

import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path so `ml` package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.config as cfg
from backend.routers import bias, explain, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load ML artifacts once. Shutdown: nothing to clean up."""
    print("-- NYAYA startup --------------------------------")
    cfg.validate()
    # Pre-load SHAP artifacts (avoids cold-start latency on first request)
    try:
        from ml.explainer import load_artifacts
        load_artifacts()
    except Exception as e:
        print(f"[WARN] SHAP load warning: {e} (will retry on first request)")
    print(f"   Mode: {'GCP (Firestore + BigQuery)' if cfg.USE_GCP else 'LOCAL (JSON + pandas)'}")
    print(f"   Gemini: {'Vertex AI' if cfg.USE_VERTEX_AI else 'AI Studio'}")
    print("-- Ready ----------------------------------------")
    yield


app = FastAPI(
    title="NYAYA — India's AI Accountability Infrastructure",
    description=(
        "Detect bias in AI datasets. Explain decisions in Hindi. "
        "Audit historical patterns. Built for DPDPA 2023 compliance."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(bias.router,    tags=["Bias Detection"])
app.include_router(explain.router, tags=["Explainability"])
app.include_router(audit.router,   tags=["Audit"])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode":   "gcp" if cfg.USE_GCP else "local",
        "gemini": "vertex" if cfg.USE_VERTEX_AI else "ai_studio",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
