#!/usr/bin/env python3
"""
Memory Queue - 异步写入系统 v1.0

核心职责：
1. 主流程只 enqueue（非阻塞）
2. worker 常驻循环消费
3. embedding/upsert 失败不影响主任务
4. 失败落日志，不静默吞掉

作者：小九 | 2026-03-07
"""

import json
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
QUEUE_LOG = BASE_DIR / "memory_queue.log"
FAILED_WRITES = BASE_DIR / "memory_queue_failed.jsonl"

# ── Global Queue ────────────────────────────────────────────────────────────
_queue: Optional[queue.Queue] = None
_worker_thread: Optional[threading.Thread] = None
_worker_running = False


def _log(msg: str):
    """写入队列日志"""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}\n"
    with open(QUEUE_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _log_failed(event: dict):
    """记录失败的写入请求"""
    with open(FAILED_WRITES, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ── Worker ──────────────────────────────────────────────────────────────────
def _worker_loop():
    """常驻消费者线程"""
    global _worker_running
    _log("[WORKER] Started")
    
    while _worker_running:
        try:
            # 阻塞等待，超时1秒检查退出标志
            event = _queue.get(timeout=1.0)
        except queue.Empty:
            continue
        
        # 处理事件
        try:
            _process_event(event)
            _queue.task_done()
        except Exception as e:
            _log(f"[ERROR] Failed to process event: {e}")
            _log_failed(event)
            _queue.task_done()
    
    _log("[WORKER] Stopped")


def _process_event(event: dict):
    """处理单个事件：标准化 → embedding → upsert"""
    event_type = event.get("event")
    payload = event.get("payload", {})
    
    if event_type == "task_completed":
        _handle_task_completed(payload)
    elif event_type == "task_failed":
        _handle_task_failed(payload)
    else:
        _log(f"[WARN] Unknown event type: {event_type}")


def _handle_task_completed(payload: dict):
    """处理任务成功事件"""
    from memory_v2.memory_store import upsert_memory
    
    # 标准化文本
    task_desc = payload.get("description", "")
    result = payload.get("result", "")
    text = f"{task_desc} | Result: {result}"[:512]
    
    # 构建记录
    record = {
        "id": payload.get("task_id", "unknown"),
        "text": text,
        "memory_type": "success_case",
        "task_type": payload.get("task_type", ""),
        "tags": payload.get("tags", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "agent_id": payload.get("agent_id", ""),
            "duration_ms": payload.get("duration_ms", 0),
        }
    }
    
    # Upsert（可能失败，但不影响主流程）
    try:
        upsert_memory(record)
        _log(f"[OK] Upserted success_case: {record['id']}")
    except Exception as e:
        _log(f"[ERROR] Upsert failed for {record['id']}: {e}")
        raise  # 重新抛出，让外层记录到 failed.jsonl


def _handle_task_failed(payload: dict):
    """处理任务失败事件"""
    from memory_v2.memory_store import upsert_memory
    
    # 标准化文本
    task_desc = payload.get("description", "")
    error = payload.get("error", "")
    text = f"{task_desc} | Error: {error}"[:512]
    
    # 构建记录
    record = {
        "id": payload.get("task_id", "unknown"),
        "text": text,
        "memory_type": "failure_pattern",
        "error_type": payload.get("error_type", "unknown"),
        "tags": payload.get("tags", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "agent_id": payload.get("agent_id", ""),
            "retry_count": payload.get("retry_count", 0),
        }
    }
    
    # Upsert
    try:
        upsert_memory(record)
        _log(f"[OK] Upserted failure_pattern: {record['id']}")
    except Exception as e:
        _log(f"[ERROR] Upsert failed for {record['id']}: {e}")
        raise


# ── Public API ──────────────────────────────────────────────────────────────
def start_worker():
    """启动异步写入 worker"""
    global _queue, _worker_thread, _worker_running
    
    if _worker_running:
        return  # 已启动
    
    _queue = queue.Queue(maxsize=1000)
    _worker_running = True
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
    _worker_thread.start()
    _log("[QUEUE] Worker started")


def stop_worker():
    """停止 worker（优雅关闭）"""
    global _worker_running
    
    if not _worker_running:
        return
    
    _worker_running = False
    if _worker_thread:
        _worker_thread.join(timeout=5.0)
    _log("[QUEUE] Worker stopped")


def enqueue(event_type: str, payload: dict):
    """
    入队（非阻塞）
    
    Args:
        event_type: "task_completed" | "task_failed"
        payload: 任务数据
    """
    if not _worker_running:
        start_worker()
    
    event = {
        "event": event_type,
        "payload": payload,
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
    }
    
    try:
        _queue.put_nowait(event)
    except queue.Full:
        _log(f"[WARN] Queue full, dropping event: {event_type}")
        _log_failed(event)


def get_stats() -> dict:
    """获取队列统计"""
    if not _queue:
        return {"queue_size": 0, "worker_running": False}
    
    return {
        "queue_size": _queue.qsize(),
        "worker_running": _worker_running,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "start":
        start_worker()
        print("[OK] Worker started")
        time.sleep(2)
        print(f"Stats: {get_stats()}")
    
    elif cmd == "test":
        start_worker()
        # 模拟入队
        for i in range(5):
            enqueue("task_completed", {
                "task_id": f"test-{i}",
                "description": f"Test task {i}",
                "result": f"Success {i}",
                "task_type": "test",
            })
        print(f"[OK] Enqueued 5 events")
        time.sleep(3)
        print(f"Stats: {get_stats()}")
        stop_worker()
    
    elif cmd == "status":
        print(f"Stats: {get_stats()}")
    
    else:
        print("Usage: memory_queue.py [start|test|status]")
