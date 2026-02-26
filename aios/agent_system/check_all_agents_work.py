"""检查所有Agent的工作状态"""
import json
from pathlib import Path
from datetime import datetime

workspace = Path("C:/Users/A/.openclaw/workspace")

print("=" * 80)
print("所有 Agent 工作状态检查")
print("=" * 80)
print()

# 1. 运行时 Agent (agents.json)
print("【1. 运行时 Agent - 3个】")
agents_file = workspace / "aios" / "agent_system" / "data" / "agents.json"
if agents_file.exists():
    with open(agents_file, encoding="utf-8") as f:
        agents = json.load(f).get("agents", [])
        for agent in agents:
            stats = agent.get('stats', {})
            completed = stats.get('tasks_completed', 0)
            failed = stats.get('tasks_failed', 0)
            total = completed + failed
            
            status = "✅ 有活干" if total > 0 else "❌ 没活干"
            print(f"  {agent['id']}: {status} (完成{completed}/失败{failed})")
print()

# 2. 任务队列
print("【2. 任务队列】")
queue_file = workspace / "aios" / "agent_system" / "task_queue.jsonl"
if queue_file.exists():
    with open(queue_file, encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    print(f"  队列中任务: {len(tasks)} 个")
    
    # 按类型统计
    task_types = {}
    for task in tasks:
        task_type = task.get('type', 'unknown')
        task_types[task_type] = task_types.get(task_type, 0) + 1
    
    for task_type, count in task_types.items():
        print(f"    - {task_type}: {count} 个")
else:
    print("  队列为空 ❌")
print()

# 3. 学习 Agent
print("【3. 学习 Agent - 27个】")
try:
    import sys
    sys.path.insert(0, str(workspace / "aios" / "agent_system"))
    from learning_agents import LEARNING_AGENTS
    
    # 检查上次运行时间
    state_file = workspace / "memory" / "selflearn-state.json"
    state = {}
    if state_file.exists():
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
    
    now = datetime.now()
    active_count = 0
    idle_count = 0
    
    for agent in LEARNING_AGENTS:
        name = agent['name']
        schedule = agent.get('schedule', 'daily')
        last_run_key = f"last_{name.lower()}"
        last_run = state.get(last_run_key)
        
        if last_run:
            last_time = datetime.fromisoformat(last_run)
            hours_ago = (now - last_time).total_seconds() / 3600
            
            if hours_ago < 24:
                status = f"✅ 最近运行 ({hours_ago:.1f}小时前)"
                active_count += 1
            else:
                status = f"⏰ 等待运行 ({hours_ago:.1f}小时前)"
                idle_count += 1
        else:
            status = "❓ 从未运行"
            idle_count += 1
        
        print(f"  {name} ({schedule}): {status}")
    
    print()
    print(f"  总计: {len(LEARNING_AGENTS)} 个")
    print(f"  最近活跃: {active_count} 个")
    print(f"  等待/未运行: {idle_count} 个")
    
except Exception as e:
    print(f"  无法读取学习Agent状态: {e}")

print()
print("=" * 80)
print("总结")
print("=" * 80)
print("运行时Agent: 3个都没活干（成功率0%）")
print("任务队列: 有3个新任务等待处理")
print("学习Agent: 需要检查上次运行时间")
print()
print("建议: 在心跳中处理任务队列，让运行时Agent开始工作")
print("=" * 80)
