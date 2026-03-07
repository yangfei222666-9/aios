#!/usr/bin/env python3
"""分析 Agent 分布"""
import json
from paths import AGENTS_STATE

with open(AGENTS_STATE, encoding='utf-8') as f:
    data = json.load(f)

# 处理两种格式
if isinstance(data, dict) and 'agents' in data:
    agents = data['agents']
else:
    agents = data

# 按类型分组
by_type = {}
for agent in agents:
    if isinstance(agent, str):
        continue
    agent_type = agent.get('type', 'unknown')
    agent_id = agent.get('id') or agent.get('name', 'unknown')
    if agent_type not in by_type:
        by_type[agent_type] = []
    by_type[agent_type].append(agent_id)

# 输出统计
print("=== Agent 分布统计 ===\n")
for agent_type, agent_list in sorted(by_type.items()):
    print(f"{agent_type}: {len(agent_list)}")
    for agent_id in agent_list:
        print(f"  - {agent_id}")
    print()

print(f"总计: {len(agents)} 个 Agent")

# 核心 Agent 判断
core_types = ['core', 'dispatcher']
core_agents = [a for a in agents if a.get('type') in core_types]
print(f"\n核心 Agent（长期运行）: {len(core_agents)}")
for agent in core_agents:
    print(f"  - {agent['id']}")
