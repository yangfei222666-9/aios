#!/usr/bin/env python3
"""更新 selflearn-state.json"""

import json
from datetime import datetime
from pathlib import Path

base_dir = Path(__file__).parent.parent

with open(base_dir / 'memory/selflearn-state.json', 'r', encoding='utf-8') as f:
    state = json.load(f)

state['validated_learning_agents_count'] = 4
state['updated_at'] = datetime.now().isoformat()

with open(base_dir / 'memory/selflearn-state.json', 'w', encoding='utf-8') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print('✓ selflearn-state.json 已更新')
print(f'  已验证学习Agent: {state["validated_learning_agents_count"]}')
