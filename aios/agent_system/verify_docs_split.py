#!/usr/bin/env python3
"""验证文档 Agent 拆分"""

from learning_agents import LEARNING_AGENTS

# 查找所有文档相关 Agent
docs_agents = [a for a in LEARNING_AGENTS if 'Docs_' in a.get('name', '') or 'Documentation' in a.get('name', '')]

print(f"找到 {len(docs_agents)} 个文档 Agent:\n")

for agent in docs_agents:
    print(f"名称: {agent['name']}")
    print(f"角色: {agent['role']}")
    print(f"目标: {agent['goal']}")
    print(f"任务数: {len(agent['tasks'])}")
    print(f"调度: {agent['schedule']} (每 {agent['interval_hours']}h)")
    print(f"优先级: {agent['priority']}")
    print()

# 检查是否还有旧的 Documentation_Writer
old_doc = [a for a in LEARNING_AGENTS if a.get('name') == 'Documentation_Writer']
if old_doc:
    print("⚠️  警告：仍存在旧的 Documentation_Writer")
else:
    print("✅ 旧的 Documentation_Writer 已移除")

print(f"\n总 Learning Agent 数: {len(LEARNING_AGENTS)}")
