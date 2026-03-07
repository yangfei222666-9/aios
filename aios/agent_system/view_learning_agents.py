#!/usr/bin/env python3
"""查看学习 Agent 状态"""
import json
from pathlib import Path
from paths import AGENTS_STATE

agents_file = AGENTS_STATE
agents_data = json.loads(agents_file.read_text(encoding='utf-8'))

learning_agents = [a for a in agents_data['agents'] if a.get('type') == 'learning']

print(f"学习 Agent 总数: {len(learning_agents)}\n")
print("=" * 60)

for i, agent in enumerate(learning_agents, 1):
    state = agent.get('state', {})
    print(f"\n{i}. {agent['name']}")
    print(f"   ID: {agent.get('id', 'N/A')}")
    print(f"   状态: {state.get('status', 'unknown')}")
    print(f"   完成任务: {state.get('tasks_completed', 0)}")
    print(f"   失败任务: {state.get('tasks_failed', 0)}")
    
    if state.get('tasks_completed', 0) + state.get('tasks_failed', 0) > 0:
        success_rate = state.get('tasks_completed', 0) / (state.get('tasks_completed', 0) + state.get('tasks_failed', 0)) * 100
        print(f"   成功率: {success_rate:.1f}%")
    
    print(f"   最后活跃: {state.get('last_active', 'never')}")
    print(f"   模型: {agent.get('model', 'N/A')}")
