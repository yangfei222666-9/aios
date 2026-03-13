#!/usr/bin/env python3
"""
真实 Agent 执行器 - 通过 spawn_pending.jsonl 触发 sessions_spawn

替换 core/task_executor.py 中的 _simulate_execute
"""
import json
import time
from pathlib import Path
from datetime import datetime

SPAWN_PENDING = Path(__file__).parent / "data" / "spawn_pending.jsonl"


def real_execute(task: dict) -> dict:
    """
    真实执行：写入 spawn_pending.jsonl，等待 heartbeat 调用 sessions_spawn
    
    Returns:
        {success: bool, output: str, duration_s: float, spawn_requested: bool}
    """
    t0 = time.time()
    
    task_id = task.get("id") or task.get("task_id", "unknown")
    agent_id = task.get("agent_id", "unknown")
    desc = task.get("description", "")
    task_type = task.get("type", task.get("task_type", ""))
    
    # 构造 spawn 请求
    spawn_request = {
        "task_id": task_id,
        "agent_id": agent_id,
        "task": desc,
        "label": f"{agent_id}-{task_id[:8]}",
        "cleanup": "delete",
        "runTimeoutSeconds": 300,
        "created_at": datetime.now().isoformat(),
    }
    
    # 写入 spawn_pending.jsonl
    try:
        SPAWN_PENDING.parent.mkdir(parents=True, exist_ok=True)
        with SPAWN_PENDING.open("a", encoding="utf-8") as f:
            f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")
        
        duration_s = round(time.time() - t0, 3)
        return {
            "success": True,
            "output": f"Spawn request created for {agent_id} (task: {desc[:50]}...)",
            "duration_s": duration_s,
            "spawn_requested": True,
        }
    except Exception as e:
        duration_s = round(time.time() - t0, 3)
        return {
            "success": False,
            "output": f"Failed to create spawn request: {e}",
            "duration_s": duration_s,
            "spawn_requested": False,
            "error": str(e),
        }


if __name__ == "__main__":
    # 测试
    test_task = {
        "task_id": "test-001",
        "agent_id": "GitHub_Researcher",
        "description": "搜索 GitHub 上的 AIOS 项目",
        "type": "research",
    }
    
    result = real_execute(test_task)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 检查文件
    if SPAWN_PENDING.exists():
        print(f"\n✅ spawn_pending.jsonl 已创建")
        print(f"内容: {SPAWN_PENDING.read_text(encoding='utf-8')}")
