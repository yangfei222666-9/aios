#!/usr/bin/env python3
"""
Phase 2: 为 agents.json 中的每个 Agent 增加 agent_type 字段
"""

import json
from pathlib import Path

AGENTS_FILE = Path('agents.json')

def classify_agent(agent):
    """根据 Agent 的配置和统计数据，自动推断 agent_type"""
    
    # 1. disabled
    if not agent.get('enabled', False) or agent.get('mode') == 'disabled':
        return 'disabled'
    
    # 2. shadow
    if agent.get('mode') == 'shadow':
        return 'shadow'
    
    # 3. standby_emergency
    # 条件：production_ready: false, tasks_total == 0, 有条件触发逻辑
    if (not agent.get('production_ready', False) and 
        agent.get('stats', {}).get('tasks_total', 0) == 0 and
        agent.get('name') in ['Bug_Hunter', 'Error_Analyzer']):
        return 'standby_emergency'
    
    # 4. degraded
    # 条件：失败率 >= 20%
    success_rate = agent.get('stats', {}).get('success_rate', 1.0)
    if success_rate < 0.8:
        return 'degraded'
    
    # 5. active_routable
    # 条件：production_ready: true, tasks_total > 0, 最近有执行
    if (agent.get('production_ready', False) and 
        agent.get('stats', {}).get('tasks_total', 0) > 0):
        return 'active_routable'
    
    # 6. schedulable_idle
    # 条件：tasks_total > 0, 但最近无执行（这里简化为 tasks_total > 0）
    if agent.get('stats', {}).get('tasks_total', 0) > 0:
        return 'schedulable_idle'
    
    # 默认：shadow（未分类）
    return 'shadow'

def update_agents_json():
    """更新 agents.json，为每个 Agent 增加 agent_type 字段"""
    
    if not AGENTS_FILE.exists():
        print(f'Error: {AGENTS_FILE} not found')
        return
    
    # 读取
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 更新
    updated_count = 0
    for agent in data['agents']:
        agent_type = classify_agent(agent)
        agent['agent_type'] = agent_type
        updated_count += 1
        print(f'  {agent["name"]}: {agent_type}')
    
    # 写回
    with open(AGENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'\n✓ Updated {updated_count} agents')
    
    # 统计
    type_counts = {}
    for agent in data['agents']:
        agent_type = agent.get('agent_type', 'unknown')
        type_counts[agent_type] = type_counts.get(agent_type, 0) + 1
    
    print('\nAgent Type Distribution:')
    for agent_type, count in sorted(type_counts.items()):
        print(f'  {agent_type}: {count}')

if __name__ == '__main__':
    print('Phase 2: Updating agents.json with agent_type field\n')
    update_agents_json()
