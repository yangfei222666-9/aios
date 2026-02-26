#!/usr/bin/env python3
"""
AIOS Heartbeat v5.0 - Task Router Integration

v4.0 功能保留：
- 每小时评估系统健康度
- 每天生成完整报告

v5.0 新增：
- 自动从 task_queue 取任务
- 通过 task_router 路由到最佳 Agent
- 输出 spawn 命令供 OpenClaw 执行
- 任务执行统计

用法:
  python heartbeat_v5.py           # 完整心跳
  python heartbeat_v5.py dispatch  # 仅分发任务
  python heartbeat_v5.py status    # 查看状态
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from task_router import TaskRouter, QUEUE_PATH

STATE_FILE = BASE_DIR / "data" / "heartbeat_v5_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
DISPATCH_LOG = BASE_DIR / "dispatch_log.jsonl"

# 每次心跳最多分发的任务数
MAX_DISPATCH_PER_BEAT = 5

# Agent ID → spawn 配置
AGENT_SPAWN_CONFIG = {
    "coder":      {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 120},
    "analyst":    {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 90},
    "monitor":    {"model": "claude-sonnet-4-6", "thinking": "off",    "timeout": 60},
    "reactor":    {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 90},
    "researcher": {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 120},
    "designer":   {"model": "claude-sonnet-4-6", "thinking": "high",   "timeout": 120},
    "evolution":  {"model": "claude-sonnet-4-6", "thinking": "high",   "timeout": 90},
    "security":   {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 60},
    "automation": {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 90},
    "document":   {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 60},
    "tester":     {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 90},
    "game-dev":   {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 120},
}


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_health_check": None,
        "last_daily_report": None,
        "last_dispatch": None,
        "total_dispatched": 0,
        "total_completed": 0,
        "total_failed": 0,
    }


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def dispatch_tasks(router, state, max_tasks=MAX_DISPATCH_PER_BEAT):
    """从队列取任务并生成 spawn 命令"""
    queue = router.get_queue()
    if not queue:
        return []

    dispatched = []
    remaining = []

    # 取前 N 个任务
    to_dispatch = queue[:max_tasks]
    to_keep = queue[max_tasks:]

    for task in to_dispatch:
        agent_id = task["agent_id"]
        config = AGENT_SPAWN_CONFIG.get(agent_id, {"model": "claude-sonnet-4-6", "thinking": "low", "timeout": 90})

        spawn_cmd = {
            "task_id": task["id"],
            "agent_id": agent_id,
            "description": task["description"],
            "task_type": task["task_type"],
            "priority": task["priority"],
            "model": config["model"],
            "thinking": config["thinking"],
            "timeout": config["timeout"],
            "label": f"agent-{agent_id}",
        }

        # 标记为 running
        task["status"] = "running"
        task["started_at"] = datetime.now(timezone.utc).isoformat()

        dispatched.append(spawn_cmd)

        # 记录日志
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "dispatch",
            "task_id": task["id"],
            "agent_id": agent_id,
            "description": task["description"][:100],
        }
        with open(DISPATCH_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # 更新队列（移除已分发的，保留剩余的）
    # 重写队列文件（只保留未分发的 + 正在运行的）
    all_tasks = [t for t in to_dispatch] + to_keep  # running + remaining pending
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        for t in all_tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    state["last_dispatch"] = datetime.now(timezone.utc).isoformat()
    state["total_dispatched"] = state.get("total_dispatched", 0) + len(dispatched)

    return dispatched


def print_spawn_commands(dispatched):
    """输出 spawn 命令（供 OpenClaw 或人工执行）"""
    if not dispatched:
        print("  No tasks to dispatch.")
        return

    print(f"  Dispatching {len(dispatched)} tasks:\n")
    for cmd in dispatched:
        print(f"  [{cmd['priority']:>8}] {cmd['agent_id']:>12} | {cmd['description'][:50]}")
        print(f"           model={cmd['model']} thinking={cmd['thinking']} timeout={cmd['timeout']}s")
        print(f"           label={cmd['label']}")
        print()


def check_health_simple():
    """简化版健康检查（不依赖 SelfImprovingLoop）"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("C:\\").percent
        return {
            "cpu": round(cpu, 1),
            "memory": round(mem, 1),
            "disk": round(disk, 1),
            "status": "warning" if mem > 90 or cpu > 90 or disk > 90 else "ok"
        }
    except ImportError:
        # Fallback without psutil
        return {"status": "unknown", "note": "psutil not installed"}


def heartbeat_v5(mode="full"):
    """Heartbeat v5.0 主函数"""
    state = load_state()
    router = TaskRouter()

    if mode == "status":
        stats = router.get_stats()
        print("AIOS Heartbeat v5.0 Status\n")
        print(f"  Total Dispatched: {state.get('total_dispatched', 0)}")
        print(f"  Total Completed:  {state.get('total_completed', 0)}")
        print(f"  Total Failed:     {state.get('total_failed', 0)}")
        print(f"  Queue Pending:    {stats.get('queue_pending', 0)}")
        print(f"  Agents Active:    {stats.get('agents_active', 0)}/{stats.get('agents_total', 0)}")
        print(f"  Last Dispatch:    {state.get('last_dispatch', 'never')}")
        return

    print("AIOS Heartbeat v5.0\n")

    results = []

    # 1. 任务分发（核心功能）
    print("[1] Task Dispatch")
    dispatched = dispatch_tasks(router, state)
    if dispatched:
        print_spawn_commands(dispatched)
        results.append(f"DISPATCHED:{len(dispatched)}")
    else:
        print("  Queue empty, nothing to dispatch.")
    print()

    # 2. 健康检查（每小时）
    if mode == "full":
        last_hc = state.get("last_health_check")
        should_check = not last_hc or (
            datetime.now(timezone.utc) - datetime.fromisoformat(last_hc)
        ) > timedelta(hours=1)

        if should_check:
            print("[2] Health Check")
            health = check_health_simple()
            if health.get("status") == "ok":
                print(f"  CPU: {health['cpu']}% | MEM: {health['memory']}% | DISK: {health['disk']}%")
                print("  Status: OK")
                results.append("HEALTH_OK")
            elif health.get("status") == "warning":
                print(f"  CPU: {health['cpu']}% | MEM: {health['memory']}% | DISK: {health['disk']}%")
                print("  Status: WARNING")
                results.append("HEALTH_WARNING")
            else:
                print(f"  Status: {health.get('status', 'unknown')}")
            state["last_health_check"] = datetime.now(timezone.utc).isoformat()
            print()

    # 3. 路由统计
    stats = router.get_stats()
    print(f"[Stats] Routed: {stats.get('total_routed', 0)} | Queue: {stats.get('queue_pending', 0)} | Agents: {stats.get('agents_active', 0)}/{stats.get('agents_total', 0)}")

    save_state(state)

    if not results:
        print("\nHEARTBEAT_OK (no actions)")
    else:
        print(f"\nHEARTBEAT_OK ({', '.join(results)})")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    heartbeat_v5(mode)
