#!/usr/bin/env python3
"""
Memory Store - LanceDB 存储层 v1.0

核心功能：
1. upsert_memory(record) - 写入记忆
2. search_memories(query, filters) - 检索记忆

Schema:
- id: str
- text: str (用于 embedding)
- vector: list[float] (384维)
- memory_type: str (success_case | failure_pattern | fix_solution)
- task_type: str (可选)
- error_type: str (可选)
- status: str (可选，fix_solution 专用)
- tags: str (JSON array)
- timestamp: str (ISO 8601)
- metadata: str (JSON object)

作者：小九 | 2026-03-07
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import lancedb
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Config ──────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "lancedb_memory_v2"
TABLE_NAME = "memories"
MODEL_NAME = "all-MiniLM-L6-v2"

# ── Singleton model ─────────────────────────────────────────────────────────
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _embed(text: str) -> list[float]:
    return _get_model().encode(text, normalize_embeddings=True).tolist()


# ── Table ───────────────────────────────────────────────────────────────────
def _get_table():
    db = lancedb.connect(str(DB_PATH))
    try:
        tables_resp = db.list_tables()
        table_list = tables_resp.tables if hasattr(tables_resp, 'tables') else list(tables_resp)
    except Exception:
        table_list = []
    
    if TABLE_NAME in table_list:
        return db.open_table(TABLE_NAME)
    
    # 尝试直接 open（可能已存在但 list 失败）
    try:
        return db.open_table(TABLE_NAME)
    except Exception:
        pass
    
    # 创建表（需要 dummy row 推断 schema）
    dummy = {
        "id": "__init__",
        "text": "init",
        "vector": _embed("init"),
        "memory_type": "",
        "task_type": "",
        "error_type": "",
        "status": "",
        "tags": "[]",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": "{}",
    }
    tbl = db.create_table(TABLE_NAME, data=[dummy])
    tbl.delete("id = '__init__'")
    return tbl


# ── Upsert ──────────────────────────────────────────────────────────────────
def upsert_memory(record: dict) -> str:
    """
    写入记忆（幂等）
    
    Args:
        record: {
            "id": str (可选，自动生成),
            "text": str,
            "memory_type": str,
            "task_type": str (可选),
            "error_type": str (可选),
            "status": str (可选),
            "tags": list[str] (可选),
            "metadata": dict (可选),
        }
    
    Returns:
        记录 ID
    """
    tbl = _get_table()
    
    # 生成 ID
    rid = record.get("id") or str(uuid.uuid4())
    
    # 标准化
    row = {
        "id": rid,
        "text": record.get("text", ""),
        "vector": _embed(record.get("text", "")),
        "memory_type": record.get("memory_type", ""),
        "task_type": record.get("task_type", ""),
        "error_type": record.get("error_type", ""),
        "status": record.get("status", ""),
        "tags": json.dumps(record.get("tags", []), ensure_ascii=False),
        "timestamp": record.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "metadata": json.dumps(record.get("metadata", {}), ensure_ascii=False),
    }
    
    # 检查是否已存在
    existing = tbl.search([0.0] * 384).where(f"id = '{rid}'").limit(1).to_list()
    if existing:
        # 更新
        tbl.update(where=f"id = '{rid}'", values=row)
    else:
        # 插入
        tbl.add([row])
    
    return rid


# ── Search ──────────────────────────────────────────────────────────────────
def search_memories(
    query: str,
    memory_type: Optional[str] = None,
    task_type: Optional[str] = None,
    error_type: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[list[str]] = None,
    top_k: int = 10,
) -> list[dict]:
    """
    检索记忆
    
    Args:
        query: 查询文本
        memory_type: 过滤 memory_type
        task_type: 过滤 task_type
        error_type: 过滤 error_type
        status: 过滤 status
        tags: 过滤 tags（任意匹配）
        top_k: 返回结果数量
    
    Returns:
        [{"id": str, "text": str, "_score": float, ...}]
    """
    tbl = _get_table()
    vec = _embed(query)
    
    # 向量检索（多取一些，后面过滤）
    results = tbl.search(vec).limit(top_k * 5).to_list()
    
    # 过滤
    filtered = []
    for r in results:
        # memory_type 过滤
        if memory_type and r.get("memory_type") != memory_type:
            continue
        
        # task_type 过滤
        if task_type and r.get("task_type") != task_type:
            continue
        
        # error_type 过滤
        if error_type and r.get("error_type") != error_type:
            continue
        
        # status 过滤
        if status and r.get("status") != status:
            continue
        
        # tags 过滤（任意匹配）
        if tags:
            try:
                r_tags = json.loads(r.get("tags", "[]"))
                if not any(t in r_tags for t in tags):
                    continue
            except Exception:
                continue
        
        # 计算相似度分数（L2 距离 → 相似度）
        dist = r.get("_distance", 1.0)
        score = max(0.0, 1.0 - float(dist) / 2.0)
        
        # 解析 metadata
        try:
            metadata = json.loads(r.get("metadata", "{}"))
        except Exception:
            metadata = {}
        
        filtered.append({
            "id": r.get("id"),
            "text": r.get("text"),
            "memory_type": r.get("memory_type"),
            "task_type": r.get("task_type"),
            "error_type": r.get("error_type"),
            "status": r.get("status"),
            "tags": json.loads(r.get("tags", "[]")),
            "timestamp": r.get("timestamp"),
            "metadata": metadata,
            "_score": round(score, 4),
        })
    
    # 按分数排序
    filtered.sort(key=lambda x: x["_score"], reverse=True)
    return filtered[:top_k]


# ── Stats ───────────────────────────────────────────────────────────────────
def get_stats() -> dict:
    """获取存储统计"""
    tbl = _get_table()
    rows = tbl.search([0.0] * 384).limit(100000).to_list()
    
    # 按 memory_type 分组
    by_type = {}
    for r in rows:
        mt = r.get("memory_type", "unknown")
        by_type[mt] = by_type.get(mt, 0) + 1
    
    return {
        "total": len(rows),
        "by_type": by_type,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "upsert":
        # 测试写入
        record = {
            "text": "优化 Memory Manager 缓存策略 | Result: 引入 TTL + LRU 双层缓存",
            "memory_type": "success_case",
            "task_type": "code",
            "tags": ["optimization", "cache"],
        }
        rid = upsert_memory(record)
        print(f"[OK] Upserted: {rid}")
    
    elif cmd == "search":
        # 测试检索
        query = " ".join(sys.argv[2:]) or "优化缓存"
        results = search_memories(query, memory_type="success_case", top_k=3)
        print(f"Query: {query}")
        print(f"Results ({len(results)}):")
        for r in results:
            print(f"  score={r['_score']} [{r['memory_type']}] {r['text'][:80]}")
    
    elif cmd == "status":
        stats = get_stats()
        print(f"[MEMORY] Total: {stats['total']}")
        print(f"By type: {stats['by_type']}")
    
    else:
        print("Usage: memory_store.py [upsert|search <query>|status]")
