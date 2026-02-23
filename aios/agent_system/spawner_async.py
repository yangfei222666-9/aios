"""
AIOS Agent Spawner (Async) - 异步批量创建 Agent
不等待完成，通过 subagents 工具异步查询结果
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


WORKSPACE = Path(__file__).parent.parent.parent
SPAWN_FILE = WORKSPACE / "aios" / "agent_system" / "spawn_requests.jsonl"
RESULTS_FILE = WORKSPACE / "aios" / "agent_system" / "spawn_results.jsonl"


def load_spawn_requests() -> List[Dict]:
    """加载待处理的 spawn 请求"""
    if not SPAWN_FILE.exists():
        return []
    
    requests = []
    with open(SPAWN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))
    
    return requests


def clear_spawn_requests():
    """清空请求文件"""
    SPAWN_FILE.write_text("", encoding="utf-8")


def record_spawn_result(task_id: str, label: str, model: str, 
                        session_key: str = None, error: str = None):
    """记录 spawn 结果"""
    result = {
        "task_id": task_id,
        "label": label,
        "model": model,
        "spawned_at": datetime.now().isoformat(),
        "session_key": session_key,
        "status": "spawned" if session_key else "error",
        "error": error
    }
    
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def spawn_batch_async(requests: List[Dict], spawn_fn) -> Dict:
    """
    批量异步创建 Agent
    
    Args:
        requests: spawn 请求列表
        spawn_fn: sessions_spawn 函数（由调用方传入）
    
    Returns:
        {"spawned": int, "failed": int, "details": [...]}
    """
    spawned = 0
    failed = 0
    details = []
    
    for req in requests:
        task_id = req["task_id"]
        label = req["label"]
        message = req["message"]
        model = req["model"]
        
        try:
            # 异步创建（不等待完成）
            result = spawn_fn(
                task=message,
                label=label,
                model=model,
                cleanup="keep",  # 保持会话，不自动删除
                runTimeoutSeconds=300
            )
            
            # 检查结果
            if result.get("status") == "spawned":
                session_key = result.get("sessionKey")
                record_spawn_result(task_id, label, model, session_key=session_key)
                spawned += 1
                details.append({
                    "task_id": task_id,
                    "label": label,
                    "status": "spawned",
                    "session_key": session_key
                })
            else:
                error = result.get("error", "unknown")
                record_spawn_result(task_id, label, model, error=error)
                failed += 1
                details.append({
                    "task_id": task_id,
                    "label": label,
                    "status": "error",
                    "error": error
                })
        
        except Exception as e:
            error = str(e)
            record_spawn_result(task_id, label, model, error=error)
            failed += 1
            details.append({
                "task_id": task_id,
                "label": label,
                "status": "error",
                "error": error
            })
    
    return {
        "spawned": spawned,
        "failed": failed,
        "total": len(requests),
        "details": details
    }


def check_agent_status(subagents_fn) -> Dict:
    """
    检查已创建的 Agent 状态
    
    Args:
        subagents_fn: subagents 函数（由调用方传入）
    
    Returns:
        {"active": int, "completed": int, "failed": int, "agents": [...]}
    """
    try:
        result = subagents_fn(action="list")
        
        if result.get("status") != "ok":
            return {"error": result.get("error", "unknown")}
        
        agents = result.get("subagents", [])
        
        active = sum(1 for a in agents if a.get("status") == "running")
        completed = sum(1 for a in agents if a.get("status") == "completed")
        failed = sum(1 for a in agents if a.get("status") == "failed")
        
        return {
            "active": active,
            "completed": completed,
            "failed": failed,
            "total": len(agents),
            "agents": agents
        }
    
    except Exception as e:
        return {"error": str(e)}


# 使用示例（在 OpenClaw 环境中）
"""
from aios.agent_system.spawner_async import (
    load_spawn_requests, 
    clear_spawn_requests,
    spawn_batch_async,
    check_agent_status
)

# 在心跳中调用
requests = load_spawn_requests()
if requests:
    clear_spawn_requests()
    
    # 批量创建（不等待）
    result = spawn_batch_async(requests, sessions_spawn)
    
    if result["spawned"] > 0:
        print(f"Spawned {result['spawned']} agents")
    
    if result["failed"] > 0:
        print(f"Failed {result['failed']} agents")

# 查询状态
status = check_agent_status(subagents)
print(f"Active: {status['active']}, Completed: {status['completed']}")
"""
