#!/usr/bin/env python3
"""
AIOS Task Executor - 从队列取任务并通过 sessions_spawn 真实执行

这个脚本由小九在 OpenClaw 主会话中调用，
读取 heartbeat 分发的任务，生成 spawn 指令。

用法（在 OpenClaw 中）:
  python task_executor.py          # 输出待执行任务的 JSON
  python task_executor.py --count  # 仅输出待执行数量
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
QUEUE_PATH = BASE_DIR / "task_queue.jsonl"
EXEC_LOG = BASE_DIR / "execution_log.jsonl"

# Agent prompt 模板
AGENT_PROMPTS = {
    "coder": "You are a coding expert. Complete this task:\n{desc}\n\nWrite clean, tested code. Save output to test_runs/.",
    "analyst": "You are a data analyst. Complete this task:\n{desc}\n\nProvide data-driven insights. Save report to test_runs/.",
    "monitor": "You are a system monitor. Complete this task:\n{desc}\n\nCheck system metrics and report status. Save to test_runs/.",
    "reactor": "You are an auto-fixer. Complete this task:\n{desc}\n\nDiagnose and fix the issue. Save results to test_runs/.",
    "researcher": "You are a researcher. Complete this task:\n{desc}\n\nSearch, analyze, and summarize findings. Save to test_runs/.",
    "designer": "You are an architect. Complete this task:\n{desc}\n\nDesign the solution with clear diagrams/specs. Save to test_runs/.",
    "evolution": "You are the evolution engine. Complete this task:\n{desc}\n\nEvaluate and suggest improvements. Save to test_runs/.",
    "security": "You are a security auditor. Complete this task:\n{desc}\n\nAudit for vulnerabilities and risks. Save to test_runs/.",
    "automation": "You are an automation specialist. Complete this task:\n{desc}\n\nAutomate the process efficiently. Save to test_runs/.",
    "document": "You are a document processor. Complete this task:\n{desc}\n\nExtract, summarize, or generate documentation. Save to test_runs/.",
    "tester": "You are a test engineer. Complete this task:\n{desc}\n\nWrite comprehensive tests. Save to test_runs/.",
    "game-dev": "You are a game developer. Complete this task:\n{desc}\n\nCreate a fun, playable game. Save to test_runs/.",
}

SPAWN_CONFIG = {
    "coder":      {"model": "claude-sonnet-4-6", "thinking": "medium", "timeout": 120},
    "analyst":    {"model": "claude-sonnet-4-6", "thinking": "low",    "timeout": 90},
    "monitor":    {"model": "claude-sonnet-4-6",                       "timeout": 60},
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


def get_pending_tasks():
    """获取待执行任务（status=running，已被 heartbeat 分发）"""
    if not QUEUE_PATH.exists():
        return []
    tasks = []
    for line in QUEUE_PATH.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                t = json.loads(line)
                if t.get("status") == "running":
                    tasks.append(t)
            except json.JSONDecodeError:
                continue
    return tasks


def generate_spawn_commands(tasks):
    """生成 spawn 命令列表"""
    commands = []
    for task in tasks:
        agent_id = task["agent_id"]
        config = SPAWN_CONFIG.get(agent_id, {"model": "claude-sonnet-4-6", "timeout": 90})
        prompt_template = AGENT_PROMPTS.get(agent_id, "Complete this task:\n{desc}")
        prompt = prompt_template.format(desc=task["description"])

        cmd = {
            "task": prompt,
            "label": f"agent-{agent_id}",
            "model": config.get("model", "claude-sonnet-4-6"),
            "runTimeoutSeconds": config.get("timeout", 90),
        }
        if config.get("thinking"):
            cmd["thinking"] = config["thinking"]

        commands.append({
            "task_id": task["id"],
            "agent_id": agent_id,
            "spawn": cmd,
        })
    return commands


def mark_tasks_dispatched(task_ids):
    """标记任务为已分发"""
    if not QUEUE_PATH.exists():
        return
    lines = QUEUE_PATH.read_text(encoding="utf-8").strip().split("\n")
    new_lines = []
    for line in lines:
        if line.strip():
            try:
                t = json.loads(line)
                if t.get("id") in task_ids:
                    t["status"] = "dispatched"
                    t["dispatched_at"] = datetime.now(timezone.utc).isoformat()
                new_lines.append(json.dumps(t, ensure_ascii=False))
            except json.JSONDecodeError:
                new_lines.append(line)
    QUEUE_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main():
    if "--count" in sys.argv:
        tasks = get_pending_tasks()
        print(len(tasks))
        return

    tasks = get_pending_tasks()
    if not tasks:
        print(json.dumps({"status": "empty", "tasks": []}, ensure_ascii=False))
        return

    commands = generate_spawn_commands(tasks)

    # 输出 JSON（供 OpenClaw 读取）
    output = {
        "status": "ready",
        "count": len(commands),
        "commands": commands,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    # 标记为已分发
    mark_tasks_dispatched([t["id"] for t in tasks])


if __name__ == "__main__":
    main()
