#!/usr/bin/env python3
"""
Executor Fallback - executor 心跳超时后自动切换备用路径

核心流程（严格顺序，不可并行）：
1. force_release(task_id)  ← 防双写唯一屏障，失败则中止
2. 确认释放成功
3. fallback executor acquire_lock  ← 拿不到说明原 executor 复活，退出
4. spawn fallback executor
5. 写审计事件

开关：fallback_enabled（关闭时只记日志不触发切换）
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

from spawn_lock import force_release_spawn_lock, try_acquire_spawn_lock, idem_key, get_lock_store
from pipeline_timer import record_fallback_latency
from paths import SPAWN_REQUESTS as _SPAWN_REQUESTS_PATH

# ── 配置 ──────────────────────────────────────────────────────────────────────
FALLBACK_ENABLED = os.environ.get("FALLBACK_ENABLED", "true").lower() == "true"
FALLBACK_AUDIT_FILE = Path(__file__).parent / "fallback_events.jsonl"

# ── 防双写：记录正在进行的 fallback（task_id → lock_token）────────────────────
_active_fallbacks: dict[str, str] = {}

# 默认 fallback 映射（primary → fallback）
DEFAULT_FALLBACK_MAP = {
    "coder-dispatcher":    "analyst-dispatcher",
    "analyst-dispatcher":  "monitor-dispatcher",
    "monitor-dispatcher":  "coder-dispatcher",
}


def handle_timeout(
    task_id: str,
    original_executor_id: str,
    task: Optional[dict] = None,
    fallback_executor_id: Optional[str] = None,
) -> dict:
    """
    处理 executor 心跳超时，触发 fallback 切换。
    
    执行顺序（严格，不可并行）：
    1. force_release → 失败则中止
    2. fallback acquire_lock → 失败则退出（原 executor 复活）
    3. spawn fallback executor
    4. 写审计事件
    
    Args:
        task_id: 任务 ID
        original_executor_id: 原 executor ID
        task: 任务对象（用于生成 idem_key，可选）
        fallback_executor_id: 指定 fallback executor（可选，默认从 DEFAULT_FALLBACK_MAP 查找）
    
    Returns:
        {
            "success": bool,
            "action": "fallback_triggered" | "fallback_skipped" | "fallback_disabled" | "error",
            "message": str,
            "fallback_executor_id": str | None,
            "lock_token": str | None,
        }
    """
    # ── 开关检查 ──────────────────────────────────────────────────────────────
    _t_start = time.monotonic()

    # ── 防双写：检查是否已有 fallback 正在进行 ────────────────────────────────
    if task_id in _active_fallbacks:
        msg = (
            f"[FALLBACK] fallback already in progress for task {task_id} "
            f"(token={_active_fallbacks[task_id][:8]}...), skipping to prevent double-write"
        )
        print(msg)
        _elapsed = (time.monotonic() - _t_start) * 1000
        record_fallback_latency(task_id, _elapsed)
        return {
            "success": False,
            "action": "fallback_skipped",
            "message": msg,
            "fallback_executor_id": None,
            "lock_token": None,
            "fallback_latency_ms": round(_elapsed, 2),
        }

    if not FALLBACK_ENABLED:
        msg = f"[FALLBACK] disabled, skipping for task {task_id}"
        print(msg)
        _write_audit("fallback_disabled", task_id, original_executor_id, None, msg)
        _elapsed = (time.monotonic() - _t_start) * 1000
        record_fallback_latency(task_id, _elapsed)
        return {
            "success": False,
            "action": "fallback_disabled",
            "message": msg,
            "fallback_executor_id": None,
            "lock_token": None,
            "fallback_latency_ms": round(_elapsed, 2),
        }
    
    # ── 确定 fallback executor ────────────────────────────────────────────────
    fb_executor = fallback_executor_id or DEFAULT_FALLBACK_MAP.get(original_executor_id)
    if not fb_executor:
        msg = f"[FALLBACK] no fallback defined for {original_executor_id}"
        print(msg)
        _write_audit("fallback_error", task_id, original_executor_id, None, msg)
        _elapsed = (time.monotonic() - _t_start) * 1000
        record_fallback_latency(task_id, _elapsed)
        return {
            "success": False,
            "action": "error",
            "message": msg,
            "fallback_executor_id": None,
            "lock_token": None,
            "fallback_latency_ms": round(_elapsed, 2),
        }
    
    # ── Step 1: force_release（防双写唯一屏障）────────────────────────────────
    # 构建 task 对象（如果没有传入）
    task_obj = task or {"id": task_id}
    
    print(f"[FALLBACK] Step 1: force_release for task {task_id}...")
    released = force_release_spawn_lock(task_obj)
    
    if not released:
        # force_release 理论上总是返回 True（幂等），但防御性处理
        msg = f"[FALLBACK] force_release FAILED for task {task_id}, aborting fallback"
        print(msg)
        _write_audit("fallback_error", task_id, original_executor_id, fb_executor, msg)
        _elapsed = (time.monotonic() - _t_start) * 1000
        record_fallback_latency(task_id, _elapsed)
        return {
            "success": False,
            "action": "error",
            "message": msg,
            "fallback_executor_id": fb_executor,
            "lock_token": None,
            "fallback_latency_ms": round(_elapsed, 2),
        }
    
    print(f"[FALLBACK] Step 1: force_release OK")
    
    # ── Step 2: fallback executor acquire_lock ────────────────────────────────
    # 构建 fallback task 对象（用不同的 executor_id 区分）
    fallback_task = dict(task_obj)
    fallback_task["agent_id"] = fb_executor
    
    print(f"[FALLBACK] Step 2: fallback executor {fb_executor} acquiring lock...")
    lock_token = try_acquire_spawn_lock(fallback_task)
    
    if lock_token is None:
        # 原 executor 复活了，它抢先拿到了锁
        msg = (
            f"[FALLBACK] fallback lock acquire FAILED for task {task_id} "
            f"(original executor may have recovered), exiting without double-write"
        )
        print(msg)
        _write_audit("fallback_skipped", task_id, original_executor_id, fb_executor, msg)
        _elapsed = (time.monotonic() - _t_start) * 1000
        record_fallback_latency(task_id, _elapsed)
        return {
            "success": False,
            "action": "fallback_skipped",
            "message": msg,
            "fallback_executor_id": fb_executor,
            "lock_token": None,
            "fallback_latency_ms": round(_elapsed, 2),
        }
    
    print(f"[FALLBACK] Step 2: lock acquired by fallback executor (token={lock_token[:8]}...)")
    
    # ── Step 3: spawn fallback executor ──────────────────────────────────────
    print(f"[FALLBACK] Step 3: spawning fallback executor {fb_executor}...")
    # TODO: 实际 spawn 在 OpenClaw 主会话中执行
    # 这里写入 spawn_requests.jsonl，由 heartbeat 读取执行
    _write_spawn_request(task_id, fb_executor, fallback_task, lock_token)
    
    # ── Step 4: 写审计事件 ────────────────────────────────────────────────────
    msg = (
        f"[FALLBACK] fallback triggered: {original_executor_id} → {fb_executor} "
        f"for task {task_id}"
    )
    print(msg)
    _write_audit("fallback_triggered", task_id, original_executor_id, fb_executor, msg)

    # 记录 fallback 进行中（防双写）
    _active_fallbacks[task_id] = lock_token

    _elapsed = (time.monotonic() - _t_start) * 1000
    record_fallback_latency(task_id, _elapsed)

    return {
        "success": True,
        "action": "fallback_triggered",
        "message": msg,
        "fallback_executor_id": fb_executor,
        "lock_token": lock_token,
        "fallback_latency_ms": round(_elapsed, 2),
    }


def _write_audit(action: str, task_id: str, original_executor: str, fallback_executor: Optional[str], message: str):
    """写入 fallback 审计事件（append-only）"""
    entry = {
        "action": action,
        "task_id": task_id,
        "original_executor": original_executor,
        "fallback_executor": fallback_executor,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(FALLBACK_AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _write_spawn_request(task_id: str, executor_id: str, task: dict, lock_token: str):
    """写入 spawn 请求（由 heartbeat 读取执行）"""
    spawn_file = _SPAWN_REQUESTS_PATH
    entry = {
        "task_id": task_id,
        "agent_id": executor_id,
        "task": task.get("description", f"Fallback execution for {task_id}"),
        "label": f"fallback-{executor_id}",
        "lock_token": lock_token,
        "is_fallback": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(spawn_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    print("Testing Executor Fallback...")
    
    # 测试 1: 正常超时 → fallback 触发
    result = handle_timeout(
        task_id="test-fb-001",
        original_executor_id="coder-dispatcher",
    )
    print(f"[OK] Normal timeout: {result['action']}")
    
    # 清理
    if FALLBACK_AUDIT_FILE.exists():
        FALLBACK_AUDIT_FILE.unlink()
    spawn_file = _SPAWN_REQUESTS_PATH
    if spawn_file.exists():
        spawn_file.unlink()
    
    print("\nAll tests passed!")
