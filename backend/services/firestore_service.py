"""
backend/services/firestore_service.py
Firestore operations with LOCAL mode fallback.
LOCAL mode: reads/writes ml/data/decisions.json
GCP mode:   uses real Firestore (requires GCP_PROJECT_ID + credentials)
"""

import json
from typing import Optional
from backend.config import USE_GCP, FIRESTORE_COLLECTION, LOCAL_DECISIONS


# ── Local mode storage ────────────────────────────────────────────────────────
_local_cache: Optional[dict] = None

def _load_local() -> dict:
    global _local_cache
    if _local_cache is None:
        if LOCAL_DECISIONS.exists():
            rows = json.loads(LOCAL_DECISIONS.read_text(encoding="utf-8"))
            _local_cache = {r["decision_id"]: r for r in rows}
        else:
            _local_cache = {}
    return _local_cache


# ── Firestore client (lazy) ───────────────────────────────────────────────────
_db = None

def _get_db():
    global _db
    if _db is None:
        from google.cloud import firestore
        _db = firestore.Client()
    return _db


# ── Public API ────────────────────────────────────────────────────────────────
def get_decision(decision_id: str) -> Optional[dict]:
    if not USE_GCP:
        return _load_local().get(decision_id)
    doc = _get_db().collection(FIRESTORE_COLLECTION).document(decision_id).get()
    return doc.to_dict() if doc.exists else None


def get_decisions_batch(decision_ids: list[str]) -> list[dict]:
    """Fetch multiple decisions. Returns list (skips missing)."""
    if not USE_GCP:
        store = _load_local()
        return [store[did] for did in decision_ids if did in store]
    db = _get_db()
    results = []
    for did in decision_ids:
        doc = db.collection(FIRESTORE_COLLECTION).document(did).get()
        if doc.exists:
            results.append(doc.to_dict())
    return results


def save_decision(decision: dict) -> None:
    """Save/update a decision record."""
    did = decision["decision_id"]
    if not USE_GCP:
        store = _load_local()
        store[did] = decision
        # Persist back to JSON
        LOCAL_DECISIONS.write_text(
            json.dumps(list(store.values()), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return
    _get_db().collection(FIRESTORE_COLLECTION).document(did).set(decision)


def seed_firestore(decisions: list[dict]) -> int:
    """Bulk seed — GCP mode only. Returns count written."""
    if not USE_GCP:
        print("LOCAL mode: Firestore seed skipped (data already in decisions.json)")
        return 0
    db = _get_db()
    batch = db.batch()
    count = 0
    for i, decision in enumerate(decisions):
        ref = db.collection(FIRESTORE_COLLECTION).document(decision["decision_id"])
        batch.set(ref, decision)
        count += 1
        if (i + 1) % 500 == 0:  # Firestore batch limit = 500
            batch.commit()
            batch = db.batch()
            print(f"  Committed {i+1} documents...")
    batch.commit()
    print(f"[OK] Seeded {count} documents to Firestore/{FIRESTORE_COLLECTION}")
    return count

