"""
rebuild_selflearn_state.py - 重建 selflearn-state.json

从现有数据源重建 selflearn-state.json：
- agent_execution_record.jsonl
- lessons.json
- state_index.json

即使文件丢失，也能恢复。

Version: 1.0
Created: 2026-03-11
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

from selflearn_state import save_state, get_default_state


DATA_DIR = Path(__file__).parent / "data"
EXECUTION_RECORD = DATA_DIR / "agent_execution_record.jsonl"
LESSONS_FILE = DATA_DIR / "lessons.json"
STATE_INDEX = DATA_DIR / "state_index.json"


def load_execution_records() -> list:
    """加载所有执行记录"""
    records = []
    if not EXECUTION_RECORD.exists():
        return records
    
    with open(EXECUTION_RECORD, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return records


def load_lessons() -> list:
    """加载所有 lessons"""
    if not LESSONS_FILE.exists():
        return []
    
    try:
        with open(LESSONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("lessons", [])
    except Exception:
        return []


def load_state_index() -> dict:
    """加载 state_index"""
    if not STATE_INDEX.exists():
        return {}
    
    try:
        with open(STATE_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def rebuild_state() -> dict:
    """从数据源重建 state"""
    
    print("=== 重建 selflearn-state.json ===")
    print()
    
    # 1. 加载数据源
    print("[1/4] 加载数据源...")
    records = load_execution_records()
    lessons = load_lessons()
    state_index = load_state_index()
    
    print(f"  执行记录: {len(records)} 条")
    print(f"  Lessons: {len(lessons)} 条")
    print(f"  State Index: {len(state_index)} 个 Agent")
    print()
    
    # 2. 分析执行记录
    print("[2/4] 分析执行记录...")
    
    # 学习 Agent 列表（从 state_index 或硬编码）
    learning_agents = {
        "GitHub_Researcher",
        "Code_Reviewer",
        "Error_Analyzer",
        "Bug_Hunter",
        "Performance_Optimizer",
        "Documentation_Writer",
        "Test_Generator",
        "Refactoring_Advisor",
        "Security_Auditor",
        "Dependency_Analyzer",
    }
    
    # 筛选学习 Agent 的执行记录
    learning_records = [
        r for r in records
        if r.get("agent_name") in learning_agents
    ]
    
    print(f"  学习 Agent 执行记录: {len(learning_records)} 条")
    
    # 找最后一次运行
    last_run_at = None
    last_success_at = None
    last_agent = None
    
    if learning_records:
        # 按时间排序
        sorted_records = sorted(
            learning_records,
            key=lambda r: r.get("end_time") or r.get("start_time") or "",
            reverse=True
        )
        
        last_record = sorted_records[0]
        last_run_at = last_record.get("end_time") or last_record.get("start_time")
        last_agent = last_record.get("agent_name")
        
        # 找最后一次成功
        success_records = [r for r in sorted_records if r.get("outcome") == "success"]
        if success_records:
            last_success_at = success_records[0].get("end_time") or success_records[0].get("start_time")
    
    print(f"  最后运行: {last_run_at or 'N/A'}")
    print(f"  最后成功: {last_success_at or 'N/A'}")
    print(f"  最后 Agent: {last_agent or 'N/A'}")
    print()
    
    # 3. 统计 Agent 状态
    print("[3/4] 统计 Agent 状态...")
    
    # 已验证的学习 Agent（从 state_index 中找 validated 状态）
    validated_agents = set()
    for agent_id, agent_state in state_index.items():
        if agent_id in learning_agents:
            status = agent_state.get("status", "")
            if "validated" in status or "production" in status:
                validated_agents.add(agent_id)
    
    # 活跃的学习 Agent（近 7 天有运行）
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    active_agents = set()
    for r in learning_records:
        run_time = r.get("end_time") or r.get("start_time")
        if run_time and run_time >= seven_days_ago:
            active_agents.add(r.get("agent_name"))
    
    print(f"  已验证的学习 Agent: {len(validated_agents)}")
    print(f"  活跃的学习 Agent: {len(active_agents)}")
    print()
    
    # 4. 统计 lessons
    print("[4/4] 统计 lessons...")
    
    pending_lessons = [l for l in lessons if l.get("status") == "pending"]
    rules_derived = sum(
        len(l.get("rules_derived", []))
        for l in lessons
        if l.get("rules_derived")
    )
    
    print(f"  待处理 lessons: {len(pending_lessons)}")
    print(f"  已提炼规则: {rules_derived}")
    print()
    
    # 5. 判断学习循环状态
    print("[5/5] 判断学习循环状态...")
    
    # 简单规则：
    # - 如果最近 7 天有成功运行 → healthy
    # - 如果最近 7 天有运行但无成功 → degraded
    # - 如果最近 7 天无运行 → blocked
    # - 其他 → unknown
    
    learning_loop_status = "unknown"
    
    if last_success_at and last_success_at >= seven_days_ago:
        learning_loop_status = "healthy"
    elif last_run_at and last_run_at >= seven_days_ago:
        learning_loop_status = "degraded"
    elif last_run_at:
        learning_loop_status = "blocked"
    
    print(f"  学习循环状态: {learning_loop_status}")
    print()
    
    # 6. 构建 state
    state = get_default_state()
    state.update({
        "updated_at": datetime.now().isoformat(),
        "last_run_at": last_run_at,
        "last_success_at": last_success_at,
        "last_agent": last_agent,
        "learning_loop_status": learning_loop_status,
        "validated_learning_agents_count": len(validated_agents),
        "active_learning_agents_count": len(active_agents),
        "pending_lessons_count": len(pending_lessons),
        "rules_derived_count": rules_derived,
    })
    
    return state


if __name__ == "__main__":
    state = rebuild_state()
    
    print("=== 重建结果 ===")
    print(json.dumps(state, indent=2, ensure_ascii=False))
    print()
    
    # 保存
    print("保存到 memory/selflearn-state.json...")
    if save_state(state):
        print("✅ 重建成功")
    else:
        print("❌ 保存失败")
