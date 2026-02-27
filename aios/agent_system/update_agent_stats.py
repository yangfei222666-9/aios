"""
Agent 状态更新器 - 回写执行结果到 agents.json
监听 OpenClaw 的 sessions 完成事件，更新 Agent 统计
"""
import json
from pathlib import Path
from datetime import datetime

AGENTS_FILE = Path(__file__).parent / "agents.json"
SPAWN_RESULTS = Path(__file__).parent / "spawn_results.jsonl"

def load_agents():
    """加载 agents.json"""
    if not AGENTS_FILE.exists():
        return {"agents": [], "metadata": {}}
    
    with open(AGENTS_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_agents(data):
    """保存 agents.json"""
    with open(AGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_agent_stats(agent_name: str, success: bool, duration_seconds: float = 0):
    """
    更新 Agent 统计
    
    Args:
        agent_name: Agent 名称
        success: 是否成功
        duration_seconds: 执行耗时（秒）
    """
    data = load_agents()
    
    # 查找 Agent
    agent = None
    for a in data["agents"]:
        if a.get("name") == agent_name:
            agent = a
            break
    
    if not agent:
        print(f"⚠️  Agent '{agent_name}' 不存在")
        return False
    
    # 初始化 state（如果不存在）
    if "state" not in agent:
        agent["state"] = {
            "status": "active",
            "tasks_completed": 0,
            "tasks_failed": 0,
            "last_active": None,
            "total_duration_seconds": 0,
            "avg_duration_seconds": 0
        }
    
    # 更新统计
    state = agent["state"]
    
    if success:
        state["tasks_completed"] = state.get("tasks_completed", 0) + 1
    else:
        state["tasks_failed"] = state.get("tasks_failed", 0) + 1
    
    state["last_active"] = datetime.now().isoformat()
    
    # 更新耗时统计
    if duration_seconds > 0:
        total_duration = state.get("total_duration_seconds", 0) + duration_seconds
        total_tasks = state["tasks_completed"] + state["tasks_failed"]
        state["total_duration_seconds"] = total_duration
        state["avg_duration_seconds"] = round(total_duration / total_tasks, 2) if total_tasks > 0 else 0
    
    # 保存
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    save_agents(data)
    
    print(f"✅ 已更新 {agent_name} 统计：")
    print(f"   完成: {state['tasks_completed']}, 失败: {state['tasks_failed']}")
    print(f"   平均耗时: {state.get('avg_duration_seconds', 0)}s")
    
    return True

def update_from_spawn_result(task_id: str, agent_id: str, success: bool, duration_seconds: float = 0):
    """
    从 spawn 结果更新 Agent 统计
    
    Args:
        task_id: 任务 ID
        agent_id: Agent ID
        success: 是否成功
        duration_seconds: 执行耗时
    """
    # 更新 spawn_results.jsonl
    result = {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": "completed" if success else "failed",
        "completed_at": datetime.now().isoformat(),
        "duration_seconds": duration_seconds
    }
    
    with open(SPAWN_RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    # 更新 agents.json
    return update_agent_stats(agent_id, success, duration_seconds)

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="更新 Agent 统计")
    parser.add_argument("--task-id", required=True, help="任务 ID")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--success", action="store_true", help="任务成功")
    parser.add_argument("--failed", action="store_true", help="任务失败")
    parser.add_argument("--duration", type=float, default=0, help="执行耗时（秒）")
    
    args = parser.parse_args()
    
    if not args.success and not args.failed:
        print("❌ 必须指定 --success 或 --failed")
        return
    
    success = args.success
    
    print("=" * 60)
    print("Agent 状态更新器")
    print("=" * 60)
    
    result = update_from_spawn_result(
        args.task_id,
        args.agent_id,
        success,
        args.duration
    )
    
    if result:
        print("\n✅ 更新成功")
    else:
        print("\n❌ 更新失败")

if __name__ == "__main__":
    main()
