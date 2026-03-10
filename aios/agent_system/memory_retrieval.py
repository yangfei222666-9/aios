"""
AIOS Memory Retrieval System v1.0
LanceDB-based semantic memory: ingest 鈫?query 鈫?rerank 鈫?inject 鈫?feedback
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import lancedb
import numpy as np
from sentence_transformers import SentenceTransformer

# 鈹€鈹€ Config 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
DB_PATH = Path(__file__).parent / "lancedb_memory"
TABLE_NAME = "task_memory"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 10

# 鈹€鈹€ Singleton model (lazy load) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
_model: Optional[SentenceTransformer] = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _embed(text: str) -> list[float]:
    return _get_model().encode(text, normalize_embeddings=True).tolist()


# 鈹€鈹€ Schema 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# id, text, vector, task_type, outcome, timestamp, tags, helpfulness
# helpfulness: float 0.0~1.0, updated via feedback()

def _get_table():
    db = lancedb.connect(str(DB_PATH))
    tables_resp = db.list_tables()
    table_list = tables_resp.tables if hasattr(tables_resp, 'tables') else list(tables_resp)
    if TABLE_NAME in table_list:
        return db.open_table(TABLE_NAME)
    # Create with first dummy row (LanceDB needs schema inference)
    dummy = {
        "id": "__init__",
        "text": "init",
        "vector": _embed("init"),
        "task_type": "",
        "outcome": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tags": "[]",
        "helpfulness": 0.5,
    }
    tbl = db.create_table(TABLE_NAME, data=[dummy])
    # Remove dummy
    tbl.delete("id = '__init__'")
    return tbl


# 鈹€鈹€ Ingest 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def ingest(
    text: str,
    task_type: str = "",
    outcome: str = "success",
    tags: list[str] | None = None,
    record_id: str | None = None,
) -> str:
    """Write a task result into memory. Returns the record id."""
    rid = record_id or str(uuid.uuid4())
    row = {
        "id": rid,
        "text": text,
        "vector": _embed(text),
        "task_type": task_type,
        "outcome": outcome,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tags": json.dumps(tags or []),
        "helpfulness": 0.5,
    }
    tbl = _get_table()
    tbl.add([row])
    return rid


# 鈹€鈹€ Query 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def query(
    question: str,
    top_k: int = TOP_K,
    task_type: str | None = None,
    outcome_filter: str | None = None,
) -> list[dict]:
    """Semantic search. Returns reranked results."""
    tbl = _get_table()
    vec = _embed(question)

    results = tbl.search(vec).limit(top_k * 3).to_list()

    # Basic filter (skip empty task_type in records)
    if task_type:
        results = [r for r in results if not r.get("task_type") or r.get("task_type") == task_type]
    if outcome_filter:
        results = [r for r in results if r.get("outcome") == outcome_filter]

    # Rerank: score = similarity * time_decay * outcome_weight * helpfulness
    now_ts = time.time()
    reranked = []
    for r in results:
        sim = max(0.0, 1.0 - float(r.get("_distance", 1.0)) / 2.0)  # L2 dist 鈫?[0,1] sim
        # time decay: half-life ~7 days
        try:
            age_days = (now_ts - datetime.fromisoformat(r["timestamp"]).timestamp()) / 86400
        except Exception:
            age_days = 0
        decay = 0.5 ** (age_days / 7)
        outcome_w = 1.2 if r.get("outcome") == "success" else 0.7
        helpfulness = float(r.get("helpfulness", 0.5))
        score = sim * decay * outcome_w * (0.5 + helpfulness)
        reranked.append({**r, "_score": round(score, 4)})

    reranked.sort(key=lambda x: x["_score"], reverse=True)
    return reranked[:top_k]


# 鈹€鈹€ Inject context 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def build_context(question: str, top_k: int = 5, task_type: str | None = None) -> str:
    """Return a formatted context string to inject before task execution."""
    t0 = time.time()
    hits = query(question, top_k=top_k, task_type=task_type)
    elapsed_ms = round((time.time() - t0) * 1000, 1)

    if not hits:
        return f"[MEMORY] No relevant history found ({elapsed_ms}ms)"

    lines = [f"[MEMORY] Retrieved {len(hits)} relevant experiences ({elapsed_ms}ms):"]
    for i, h in enumerate(hits, 1):
        lines.append(
            f"  [{i}] [{h.get('outcome','?')}] score={h['_score']} | {h['text'][:120]}"
        )
    return "\n".join(lines)


# 鈹€鈹€ Feedback 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def feedback(record_id: str, helpful: bool) -> bool:
    """Update helpfulness score for a memory record."""
    tbl = _get_table()
    rows = tbl.search([0.0] * 384).limit(10000).to_list()
    target = next((r for r in rows if r.get("id") == record_id), None)
    if not target:
        return False
    new_h = min(1.0, target["helpfulness"] + 0.1) if helpful else max(0.0, target["helpfulness"] - 0.1)
    tbl.update(where=f"id = '{record_id}'", values={"helpfulness": new_h})
    return True


from paths import TASK_EXECUTIONS

# 鈹€鈹€ Bulk ingest from task_executions_v2.jsonl 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def ingest_from_executions(path: str | None = None, limit: int = 500) -> int:
    """Bootstrap: load existing task_executions_v2.jsonl into LanceDB."""
    p = Path(path or TASK_EXECUTIONS)
    if not p.exists():
        return 0

    tbl = _get_table()
    existing_ids = {r["id"] for r in tbl.search([0.0] * 384).limit(100000).to_list()}

    count = 0
    with open(p, encoding="utf-8") as f:
        for line in f:
            if count >= limit:
                break
            try:
                rec = json.loads(line.strip())
            except Exception:
                continue
            rid = rec.get("task_id", str(uuid.uuid4()))
            if rid in existing_ids:
                continue
            desc = rec.get("description") or rec.get("task", "") or ""
            # result can be dict or string
            result_raw = rec.get("result") or rec.get("output", "") or ""
            if isinstance(result_raw, dict):
                result_text = result_raw.get("output", "") or result_raw.get("error", "")
                is_success = result_raw.get("success", True)
            else:
                result_text = str(result_raw)
                is_success = rec.get("success", True)
            text = f"{desc} | {result_text}"[:512]
            if not text.strip() or text.strip() == "|":
                continue
            ingest(
                text=text,
                task_type=rec.get("task_type") or rec.get("type", ""),
                outcome="success" if is_success else "failed",
                tags=rec.get("tags", []),
                record_id=rid,
            )
            existing_ids.add(rid)
            count += 1
    return count


# 鈹€鈹€ CLI 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "ingest-all":
        n = ingest_from_executions()
        print(f"[OK] Ingested {n} records from task_executions_v2.jsonl")

    elif cmd == "query":
        q = " ".join(sys.argv[2:]) or "task failed timeout"
        results = query(q, top_k=5)
        print(f"Query: {q}")
        print(f"Results ({len(results)}):")
        for r in results:
            print(f"  score={r['_score']} [{r['outcome']}] {r['text'][:100]}")

    elif cmd == "context":
        q = " ".join(sys.argv[2:]) or "optimize code performance"
        print(build_context(q, top_k=5))

    elif cmd == "status":
        tbl = _get_table()
        rows = tbl.search([0.0] * 384).limit(100000).to_list()
        real = [r for r in rows if r.get("id") != "__init__"]
        print(f"[MEMORY] Table: {TABLE_NAME} | Records: {len(real)}")

    else:
        print("Usage: memory_retrieval.py [status|ingest-all|query <text>|context <text>]")

