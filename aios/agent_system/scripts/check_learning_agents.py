#!/usr/bin/env python3
"""检查学习Agent状态"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent

with open(base_dir / 'data/agents.json', 'r', encoding='utf-8') as f:
    agents_data = json.load(f)

learning_agents = [a for a in agents_data['agents'] if a.get('group') == 'learning' and a.get('routable', False)]

print('可路由的学习Agent:\n')
for agent in learning_agents:
    validated = agent.get('validation_status') == 'validated'
    has_script = agent.get('execution_script') is not None
    status = '✓' if validated else '✗'
    script_status = '✓' if has_script else '✗'
    name = agent['name']
    print(f'{status} {name:30} | 脚本:{script_status} | 验证:{validated}')
