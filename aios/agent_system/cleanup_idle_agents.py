"""清理闲置 Agent"""
import json
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(__file__).parent.parent.parent
agents_file = workspace / "aios" / "agent_system" / "data" / "agents.jsonl"

print("=== 清理闲置 Agent ===\n")

if not agents_file.exists():
    print("agents.jsonl 不存在")
    exit(0)

# 读取所有 Agent
agents = []
with open(agents_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            agents.append(json.loads(line))

# 找出需要归档的 Agent
now = datetime.now()
to_archive = []

for agent in agents:
    if agent.get('status') != 'active':
        continue
    
    # 检查是否闲置
    stats = agent.get('stats', {})
    total_tasks = stats.get('total_tasks', 0)
    
    # 检查创建时间
    created_at = agent.get('created_at')
    if created_at:
        created = datetime.fromisoformat(created_at)
        age_hours = (now - created).total_seconds() / 3600
    else:
        age_hours = 0
    
    # 归档条件：总任务数 = 0 且创建超过 1 小时
    if total_tasks == 0 and age_hours > 1:
        to_archive.append(agent)

print(f"找到 {len(to_archive)} 个闲置 Agent：")
for agent in to_archive:
    created_at = agent.get('created_at', 'N/A')[:19]
    print(f"  {agent['id']} (创建于 {created_at})")

if not to_archive:
    print("无需清理")
    exit(0)

print()
confirm = input(f"确认归档这 {len(to_archive)} 个 Agent？(y/n): ")
if confirm.lower() != 'y':
    print("已取消")
    exit(0)

# 归档
archived_count = 0
for agent in agents:
    if agent in to_archive:
        agent['status'] = 'archived'
        agent['archived_at'] = now.isoformat()
        agent['archived_reason'] = 'idle_cleanup'
        archived_count += 1

# 写回文件
with open(agents_file, 'w', encoding='utf-8') as f:
    for agent in agents:
        f.write(json.dumps(agent, ensure_ascii=False) + '\n')

print(f"\n✅ 已归档 {archived_count} 个 Agent")
