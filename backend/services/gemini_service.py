"""
backend/services/gemini_service.py
Single interface for all Gemini calls. Supports:
  - Google AI Studio (GOOGLE_API_KEY)
  - Vertex AI (GCP_PROJECT_ID)
Auto-selects based on config. Wraps all calls with timeout + fallback.
"""

import asyncio
import json
import re
from typing import Callable

import backend.config as cfg
from backend.middleware.cache_middleware import get_cached, set_cached, make_key
from backend.middleware.fallback_middleware import get_fallback

# ── Client initialisation ─────────────────────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client

    if cfg.USE_VERTEX_AI:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        vertexai.init(project=cfg.GCP_PROJECT_ID, location=cfg.GCP_LOCATION)
        _client = GenerativeModel(cfg.GEMINI_MODEL)
    else:
        import google.generativeai as genai
        genai.configure(api_key=cfg.GOOGLE_API_KEY)
        _client = genai.GenerativeModel(cfg.GEMINI_MODEL)

    return _client


# ── Core safe-call wrapper ────────────────────────────────────────────────────
async def call_gemini_safe(
    prompt: str,
    cache_key: str,
    fallback_endpoint: str,
    ttl: int = 3600,
    parse_json: bool = True,
    fallback_key: str = None,
) -> dict:
    """
    Cache-first → live Gemini call (with timeout) → pre-computed fallback.
    Never raises — always returns a valid dict.
    """
    # 1. Cache hit
    cached = get_cached(cache_key, ttl=ttl)
    if cached:
        return cached

    # 2. Live call
    try:
        result = await asyncio.wait_for(
            _call_gemini(prompt, parse_json=parse_json),
            timeout=cfg.GEMINI_TIMEOUT,
        )
        set_cached(cache_key, result)
        return result
    except (asyncio.TimeoutError, Exception) as e:
        print(f"[WARN]  Gemini call failed ({type(e).__name__}): {e}. Using fallback.")
        return get_fallback(fallback_endpoint, key=fallback_key)



async def _call_gemini(prompt: str, parse_json: bool = True) -> dict:
    """Raw async Gemini call. Runs blocking SDK in a thread pool."""
    loop = asyncio.get_event_loop()
    client = _get_client()

    def _sync_call():
        response = client.generate_content(prompt)
        return response.text

    raw_text = await loop.run_in_executor(None, _sync_call)

    if not parse_json:
        return {"text": raw_text}

    return _extract_json(raw_text)


def _extract_json(text: str) -> dict:
    """
    Robustly extract JSON from Gemini response.
    Handles markdown code fences (```json ... ```) and bare JSON.
    """
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in response
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        # Last resort: return raw text
        return {"raw_response": text, "_parse_error": True}


# ── Prompt builders ───────────────────────────────────────────────────────────

BIAS_OUTPUT_SCHEMA = {
    "top_risky_features": [
        {
            "feature": "string",
            "risk_score": "float (use precomputed value exactly)",
            "risk_band": "LOW|MODERATE|HIGH",
            "pearson_r": "float",
            "discriminator_type": "DIRECT|PROXY",
            "explanation_en": "string — plain language, 2 sentences",
            "legal_exposure": "string — cite specific DPDPA section or Article 14",
            "regulator_quote": "string — one quotable sentence for a district collector",
        }
    ],
    "intersectional_finding": "string — describe gender × geography pattern",
    "overall_risk_level": "LOW|MODERATE|HIGH|CRITICAL",
    "executive_summary": "string — 3 sentences for a non-technical audience",
}


def build_bias_prompt(computed_metrics: dict, sample_rows: str) -> str:
    return f"""You are an AI fairness auditor. Statistical analysis has already been run on this dataset.
Your job is to INTERPRET these computed findings and assign legal risk — not to discover patterns.

## Pre-computed Statistical Results
{json.dumps(computed_metrics, indent=2, ensure_ascii=False)}

Risk scores are PRECOMPUTED using formula: risk = min(1.0, |r| × 2.2)
DO NOT modify risk_score values. Use them exactly as provided.

## Dataset Context (first 20 rows)
{sample_rows}

## Your Task
For each feature in top_risky_features:
1. Explain WHY this feature is discriminatory in the Indian lending context
2. Use the precomputed risk_score exactly — do not invent or modify
3. Identify legal exposure: cite DPDPA 2023 Section 4, 12, or Article 14 specifically
4. State DIRECT or PROXY discriminator
5. Write one sentence a non-technical regulator can quote in a report

IMPORTANT: pin_code in Indian lending is a documented proxy for caste and religion
(RBI Fair Practices Code 2015). If pin_code correlation > 0.25, label as PROXY — HIGH.

Describe the intersectional pattern (gender × geography matrix provided in metrics).

Write a 3-sentence executive summary for a non-technical government official.

Return ONLY valid JSON matching this exact schema:
{json.dumps(BIAS_OUTPUT_SCHEMA, indent=2)}"""


EXPLAIN_OUTPUT_SCHEMA = {
    "explanation_hi": "string — full Hindi explanation in Devanagari, 10th-grade level, 3-4 sentences",
    "explanation_en": "string — English equivalent, same length",
    "top_factors": [
        {"feature": "string", "direction": "approval|rejection", "plain_name": "string — human name for feature"}
    ],
    "legal_note": "string — cite DPDPA Section 12(2) if gender_proxy > 0.30, else general rights note",
    "action_advice": "string — one concrete step the citizen can take",
}


def build_explain_prompt(
    shap_values: dict,
    outcome: str,
    confidence: float,
    gender_proxy: float,
    applicant_context: dict,
    top_factors: list,
    language: str = "hi",
) -> str:
    legal_trigger = gender_proxy > 0.30

    return f"""You are a legal-rights advocate explaining an AI credit decision to an Indian citizen.
You have received SHAP feature attribution scores — mathematical values showing exactly what drove the decision.

## Decision Details
Outcome: {outcome}
Model confidence: {confidence * 100:.0f}%

## SHAP Feature Attribution (computed by SHAP LinearExplainer — not AI-generated)
{json.dumps(shap_values, indent=2)}
Positive = pushed toward APPROVAL. Negative = pushed toward REJECTION.

## Gender Proxy Score: {gender_proxy:.4f}
{"[WARN] ABOVE THRESHOLD (0.30) — legal note MUST reference DPDPA Section 12(2)" if legal_trigger else "Below threshold."}

## Top Contributing Factors
{json.dumps(top_factors, indent=2)}

## Applicant Context
{json.dumps(applicant_context, indent=2)}

## Your Task
Generate a plain-language explanation at 10th-grade reading level.
{"Primary language: HINDI (Devanagari script). Also provide English." if language == "hi" else "Language: English."}

Rules:
- DO NOT use technical terms like "SHAP" or "logistic regression"
- Say what drove the decision in everyday language
- If pin_code was a top factor, mention that location was factored in (do not mention caste directly)
- {"Include legal note citing DPDPA Section 12(2) right to explanation and right to contest" if legal_trigger else "Include general note about data rights under DPDPA"}
- Provide one concrete action step

Return ONLY valid JSON:
{json.dumps(EXPLAIN_OUTPUT_SCHEMA, indent=2)}"""


COMPLIANCE_OUTPUT_SCHEMA = {
    "executive_summary": "string",
    "systemic_pattern": "string — describe what the data shows",
    "legal_exposure": "string — DPDPA + Article 14 specific citations",
    "remediation_steps": ["string"],
    "report_text": "string — full formatted compliance report with sections",
}


def build_audit_prompt(audit_stats: dict) -> str:
    return f"""You are a DPDPA compliance officer generating a formal audit report.
The following statistics were computed by BigQuery over the decisions database.

## Audit Statistics
{json.dumps(audit_stats, indent=2, ensure_ascii=False)}

Generate a formal compliance report including:
1. Executive summary (3 sentences)
2. Description of the systemic bias pattern detected
3. Legal exposure under DPDPA 2023 Section 12, Section 44, and Article 14
4. 4 specific remediation steps
5. Full formatted report text with numbered sections

LIMITATION STATEMENT TO INCLUDE:
"NYAYA detects statistical bias patterns — it does not determine legal guilt.
These findings are inputs to institutional review, not replacements for it."

Return ONLY valid JSON:
{json.dumps(COMPLIANCE_OUTPUT_SCHEMA, indent=2)}"""

