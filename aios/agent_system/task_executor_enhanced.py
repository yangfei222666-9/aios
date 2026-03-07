#!/usr/bin/env python3
"""
Enhanced Task Executor with TimeoutManager Integration
集成智能超时管理，解决 lesson-001 超时问题
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from task_executor import (
    get_pending_tasks,
    mark_tasks_dispatched,
    build_memory_context,
    _log_memory_event,
    AGENT_PROMPTS,
    SPAWN_CONFIG,
)

# 导入 TimeoutManager
try:
    from timeout_manager import TimeoutManager
    TIMEOUT_MANAGER_AVAILABLE = True
except ImportError:
    TIMEOUT_MANAGER_AVAILABLE = False
    print("[WARN] TimeoutManager not available, using default timeouts", file=sys.stderr)


def generate_spawn_commands_enhanced(tasks):
    """
    增强版 spawn 命令生成器
    
    改进点:
    1. 集成 TimeoutManager 动态超时
    2. 根据任务复杂度调整超时
    3. 记录超时决策日志
    """
    # 初始化 TimeoutManager
    timeout_mgr = None
    if TIMEOUT_MANAGER_AVAILABLE:
        try:
            timeout_mgr = TimeoutManager()
        except Exception as e:
            print(f"[WARN] Failed to init TimeoutManager: {e}", file=sys.stderr)
    
    commands = []
    for task in tasks:
        agent_id = task["agent_id"]
        desc = task["description"]
        task_type = task.get("type", "")
        task_id = task["id"]
        
        # ── 1. 检索记忆 ──────────────────────────────────────────────────────
        mem_ctx = build_memory_context(desc, task_type)
        _log_memory_event(task_id, mem_ctx, "BUILD")
        
        # ── 2. 智能超时决策 ──────────────────────────────────────────────────
        config = SPAWN_CONFIG.get(agent_id, {"model": "claude-sonnet-4-6", "timeout": 120})
        
        if timeout_mgr:
            # 使用 TimeoutManager 获取动态超时
            timeout = timeout_mgr.get_timeout(
                agent_id=agent_id,
                agent_type=task_type or agent_id,
                route=task.get("route", "claude")
            )
            print(f"  [TIMEOUT] {agent_id} | type={task_type} | timeout={timeout}s (dynamic)", flush=True)
        else:
            # 回退到配置文件超时
            timeout = config.get("timeout", 120)
            
            # 根据任务复杂度调整（简单启发式）
            if any(keyword in desc.lower() for keyword in ["complex", "large", "comprehensive", "detailed"]):
                timeout = int(timeout * 1.5)
                print(f"  [TIMEOUT] {agent_id} | detected complex task | timeout={timeout}s (adjusted)", flush=True)
            else:
                print(f"  [TIMEOUT] {agent_id} | timeout={timeout}s (default)", flush=True)
        
        # ── 3. 构建 prompt（注入 memory_hints）──────────────────────────────
        prompt_template = AGENT_PROMPTS.get(agent_id, "Complete this task:\n{desc}")
        base_prompt = prompt_template.format(desc=desc)
        
        if mem_ctx["memory_hints"]:
            hints_text = "\n".join(f"  {i+1}. {h}" for i, h in enumerate(mem_ctx["memory_hints"]))
            injected_prompt = (
                f"[MEMORY] Relevant past experiences:\n{hints_text}\n\n"
                f"{base_prompt}"
            )
        else:
            injected_prompt = base_prompt
        
        # ── 4. 生成 spawn 命令 ──────────────────────────────────────────────
        cmd = {
            "task": injected_prompt,
            "label": f"agent-{agent_id}",
            "model": config.get("model", "claude-sonnet-4-6"),
            "runTimeoutSeconds": timeout,  # 使用动态超时
        }
        if config.get("thinking"):
            cmd["thinking"] = config["thinking"]
        
        commands.append({
            "task_id": task_id,
            "agent_id": agent_id,
            "model_used": config.get("model", "claude-sonnet-4-6"),
            "timeout_used": timeout,
            "timeout_source": "dynamic" if timeout_mgr else "config",
            "spawn": cmd,
            "memory_context": mem_ctx,
        })
    
    return commands


def main():
    """主入口"""
    if "--count" in sys.argv:
        tasks = get_pending_tasks()
        print(len(tasks))
        return
    
    tasks = get_pending_tasks()
    if not tasks:
        print(json.dumps({"status": "empty", "tasks": []}, ensure_ascii=False))
        return
    
    # 使用增强版命令生成器
    commands = generate_spawn_commands_enhanced(tasks)
    
    # 输出 JSON
    output = {
        "status": "ready",
        "count": len(commands),
        "commands": commands,
        "enhancements": {
            "timeout_manager": TIMEOUT_MANAGER_AVAILABLE,
            "memory_retrieval": True,
        }
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    # 标记为已分发
    mark_tasks_dispatched([t["id"] for t in tasks])


if __name__ == "__main__":
    main()
