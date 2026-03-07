#!/usr/bin/env python3
"""
Memory Retrieval - 双检索链 v1.0

核心接口：
1. retrieve_for_task_start(task) - 任务启动时召回历史成功方案
2. retrieve_for_failure(error) - 失败时召回修复建议

检索策略：
- task_start: filter=success_case, rerank=score+recency
- failure: filter=fix_solution, rerank=fix_success_rate+score

作者：小九 | 2026-03-07
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
RETRIEVAL_LOG = BASE_DIR / "memory_retrieval_log.jsonl"


def _log_retrieval(query: str, memory_type: str, hits: int, elapsed_ms: float):
    """记录检索日志"""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "memory_type": memory_type,
        "hits": hits,
        "elapsed_ms": round(elapsed_ms, 2),
    }
    with open(RETRIEVAL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── 检索链 1: 任务启动召回 ──────────────────────────────────────────────────
def retrieve_for_task_start(
    task: dict,
    top_k: int = 5,
) -> list[dict]:
    """
    任务启动时召回历史成功方案
    
    Args:
        task: {"description": str, "task_type": str, "tags": list}
        top_k: 返回结果数量
    
    Returns:
        [{"id": str, "text": str, "score": float, ...}]
    """
    from memory_v2.memory_store import search_memories
    
    t0 = time.time()
    
    # 构建查询文本
    query = task.get("description", "")
    task_type = task.get("task_type", "")
    tags = task.get("tags", [])
    
    # 检索：filter=success_case
    results = search_memories(
        query=query,
        memory_type="success_case",
        task_type=task_type if task_type else None,
        tags=tags if tags else None,
        top_k=top_k * 2,  # 多取一些，后面 rerank
    )
    
    # Rerank: score + recency
    now_ts = time.time()
    reranked = []
    for r in results:
        base_score = r.get("_score", 0.0)
        
        # 时间衰减（半衰期 7 天）
        try:
            ts = datetime.fromisoformat(r.get("timestamp", ""))
            age_days = (now_ts - ts.timestamp()) / 86400
        except Exception:
            age_days = 0
        recency_weight = 0.5 ** (age_days / 7)
        
        # 最终分数
        final_score = base_score * (0.7 + 0.3 * recency_weight)
        reranked.append({**r, "_final_score": round(final_score, 4)})
    
    reranked.sort(key=lambda x: x["_final_score"], reverse=True)
    results = reranked[:top_k]
    
    elapsed_ms = (time.time() - t0) * 1000
    _log_retrieval(query, "success_case", len(results), elapsed_ms)
    
    return results


# ── 检索链 2: 失败召回修复建议 ──────────────────────────────────────────────
def retrieve_for_failure(
    error: dict,
    top_k: int = 5,
) -> list[dict]:
    """
    失败时召回修复建议
    
    Args:
        error: {"description": str, "error_type": str, "error_message": str}
        top_k: 返回结果数量
    
    Returns:
        [{"id": str, "text": str, "score": float, "fix_success_rate": float, ...}]
    """
    from memory_v2.memory_store import search_memories
    
    t0 = time.time()
    
    # 构建查询文本
    error_desc = error.get("description", "")
    error_msg = error.get("error_message", "")
    query = f"{error_desc} {error_msg}"
    error_type = error.get("error_type", "")
    
    # 检索：filter=fix_solution + status=fixed
    results = search_memories(
        query=query,
        memory_type="fix_solution",
        error_type=error_type if error_type else None,
        status="fixed",  # 只要已修复的
        top_k=top_k * 2,
    )
    
    # Rerank: fix_success_rate + score
    reranked = []
    for r in results:
        base_score = r.get("_score", 0.0)
        fix_rate = r.get("metadata", {}).get("fix_success_rate", 0.5)
        
        # 最终分数：fix_rate 权重更高
        final_score = base_score * 0.4 + fix_rate * 0.6
        reranked.append({**r, "_final_score": round(final_score, 4)})
    
    reranked.sort(key=lambda x: x["_final_score"], reverse=True)
    results = reranked[:top_k]
    
    elapsed_ms = (time.time() - t0) * 1000
    _log_retrieval(query, "fix_solution", len(results), elapsed_ms)
    
    return results


# ── 格式化输出 ──────────────────────────────────────────────────────────────
def format_context(results: list[dict], context_type: str = "task_start") -> str:
    """
    格式化检索结果为可注入的上下文
    
    Args:
        results: 检索结果
        context_type: "task_start" | "failure"
    
    Returns:
        格式化的上下文字符串
    """
    if not results:
        return f"[MEMORY] No relevant {context_type} history found"
    
    lines = [f"[MEMORY] Retrieved {len(results)} relevant experiences:"]
    for i, r in enumerate(results, 1):
        score = r.get("_final_score", r.get("_score", 0))
        text = r.get("text", "")[:120]
        lines.append(f"  [{i}] score={score:.3f} | {text}")
    
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if cmd == "task":
        # 测试任务启动召回
        task = {
            "description": " ".join(sys.argv[2:]) or "优化代码性能",
            "task_type": "code",
            "tags": ["optimization"],
        }
        results = retrieve_for_task_start(task, top_k=3)
        print(format_context(results, "task_start"))
    
    elif cmd == "failure":
        # 测试失败召回
        error = {
            "description": " ".join(sys.argv[2:]) or "任务超时",
            "error_type": "timeout",
            "error_message": "Task execution timeout after 60s",
        }
        results = retrieve_for_failure(error, top_k=3)
        print(format_context(results, "failure"))
    
    else:
        print("Usage:")
        print("  memory_retrieval.py task <description>")
        print("  memory_retrieval.py failure <error_description>")
