"""查看 Agent 详细状态"""
import json
from pathlib import Path
from datetime import datetime

workspace = Path(__file__).parent.parent.parent
agents_file = workspace / "aios" / "agent_system" / "data" / "agents.jsonl"

print("=== Agent 详细状态 ===\n")

if not agents_file.exists():
    print("agents.jsonl 不存在")
    exit(0)

agents = []
with open(agents_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            agents.append(json.loads(line))

# 按状态分组
active = [a for a in agents if a.get('status') == 'active']
archived = [a for a in agents if a.get('status') == 'archived']
degraded = [a for a in agents if a.get('status') == 'degraded']

print(f"总计: {len(agents)} 个 Agent")
print(f"  活跃: {len(active)}")
print(f"  已归档: {len(archived)}")
print(f"  降级: {len(degraded)}")
print()

# 显示活跃 Agent 详情
if active:
    print("=== 活跃 Agent ===\n")
    for agent in active:
        print(f"ID: {agent['id']}")
        print(f"  状态: {agent['status']}")
        print(f"  类型: {agent.get('type', 'N/A')}")
        print(f"  环境: {agent.get('env', 'N/A')}")
        print(f"  创建时间: {agent.get('created_at', 'N/A')[:19]}")
        
        # 统计信息
        stats = agent.get('stats', {})
        if stats:
            print(f"  统计:")
            print(f"    总任务: {stats.get('total_tasks', 0)}")
            print(f"    成功: {stats.get('success_count', 0)}")
            print(f"    失败: {stats.get('failure_count', 0)}")
            if stats.get('total_tasks', 0) > 0:
                success_rate = stats.get('success_count', 0) / stats.get('total_tasks', 1) * 100
                print(f"    成功率: {success_rate:.1f}%")
        
        # 最后活动
        last_activity = agent.get('last_activity')
        if last_activity:
            print(f"  最后活动: {last_activity[:19]}")
        
        # 当前任务
        current_task = agent.get('current_task')
        if current_task:
            print(f"  当前任务: {current_task}")
        
        print()

# 显示已归档 Agent
if archived:
    print("=== 已归档 Agent ===\n")
    for agent in archived:
        print(f"ID: {agent['id']}")
        print(f"  创建时间: {agent.get('created_at', 'N/A')[:19]}")
        print(f"  归档原因: {agent.get('archived_reason', 'N/A')}")
        print()

# 显示降级 Agent
if degraded:
    print("=== 降级 Agent ===\n")
    for agent in degraded:
        print(f"ID: {agent['id']}")
        print(f"  降级原因: {agent.get('degraded_reason', 'N/A')}")
        print()
