"""
backend/routers/audit.py
GET /audit-history
Runs 3 BigQuery analytical queries + Gemini compliance report.
"""

from datetime import date
from fastapi import APIRouter, Query

from backend.services import bigquery_service as bq
from backend.services.firestore_service import get_decisions_batch
from backend.services.gemini_service import call_gemini_safe, build_audit_prompt
from backend.middleware.cache_middleware import make_key
from backend.config import CACHE_TTL_AUDIT, GENDER_PROXY_THRESHOLD

router = APIRouter()


@router.get("/audit-history")
async def audit_history(
    gender_proxy_threshold: float = Query(default=GENDER_PROXY_THRESHOLD, ge=0.0, le=1.0),
    start_date: str = Query(default="2024-01-01"),
    end_date:   str = Query(default="2024-12-31"),
    limit:      int = Query(default=100, le=500),
):
    """
    Returns retroactive audit results using 3 BigQuery analytical queries.

    Q1 — Monthly flagged trend (line chart)
    Q2 — Top 5 most biased districts (bar chart)
    Q3 — Feature-level bias distribution percentiles (box plot)
    + Flagged cases list + Gemini compliance report
    """
    threshold = gender_proxy_threshold
    cache_key = make_key("audit", str(threshold), start_date, end_date)

    # ── Q1: Monthly trend ─────────────────────────────────────────────────────
    timeline = bq.query_monthly_trend(threshold, start_date, end_date)

    # ── Q2: Top biased districts ──────────────────────────────────────────────
    top_districts = bq.query_top_biased_districts(threshold, start_date, end_date)

    # ── Q3: Feature distribution ──────────────────────────────────────────────
    feature_distribution = bq.query_feature_distribution(start_date, end_date)

    # ── Flagged cases ─────────────────────────────────────────────────────────
    flagged_cases = bq.query_flagged_cases(threshold, start_date, end_date, limit=limit)

    # Enrich top 10 with Firestore names (for human storytelling)
    top_ids = [c["decision_id"] for c in flagged_cases[:10]]
    named_records = get_decisions_batch(top_ids)
    named_map = {r["decision_id"]: r for r in named_records}

    remediation_queue = []
    for case in flagged_cases[:10]:
        did = case.get("decision_id", "")
        record = named_map.get(did, {})
        remediation_queue.append({
            "id":               did,
            "name":             record.get("applicant_name", case.get("applicant_name", "Unknown")),
            "district":         case.get("district", ""),
            "outcome":          case.get("outcome", "REJECTED"),
            "shap_gender_proxy": case.get("shap_gender_proxy", 0),
            "remediation_priority": "HIGH" if case.get("shap_gender_proxy", 0) > 0.40 else "MEDIUM",
        })

    # ── Gemini compliance report ──────────────────────────────────────────────
    audit_stats = {
        "total_audited":    sum(m["total"] for m in timeline),
        "total_flagged":    sum(m["flagged"] for m in timeline),
        "threshold":        threshold,
        "date_range":       f"{start_date} to {end_date}",
        "top_districts":    top_districts,
        "top_affected":     remediation_queue[:5],
        "timeline_summary": timeline,
    }

    gemini_result = await call_gemini_safe(
        prompt=build_audit_prompt(audit_stats),
        cache_key=cache_key,
        fallback_endpoint="audit",
        ttl=CACHE_TTL_AUDIT,
    )

    return {
        "flagged_count":          audit_stats["total_flagged"],
        "total_count":            audit_stats["total_audited"],
        "timeline":               timeline,
        "top_biased_districts":   top_districts,
        "feature_distribution":   feature_distribution,
        "flagged_cases":          flagged_cases,
        "remediation_queue":      remediation_queue,
        # Gemini outputs
        "executive_summary":      gemini_result.get("executive_summary", ""),
        "systemic_pattern":       gemini_result.get("systemic_pattern", ""),
        "legal_exposure":         gemini_result.get("legal_exposure", ""),
        "remediation_steps":      gemini_result.get("remediation_steps", []),
        "compliance_report":      gemini_result.get("report_text", ""),
        "_fallback":              gemini_result.get("_fallback", False),
    }
