"""更新 GitHub_Researcher 状态到 agents.json"""

import json
from datetime import datetime
from pathlib import Path

agents_file = Path('data/agents.json')

# 读取 agents.json
with open(agents_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找到 GitHub_Researcher
for agent in data['agents']:
    if agent['name'] == 'GitHub_Researcher':
        # 更新状态
        agent['production_ready'] = True
        agent['validation_status'] = 'validated'
        agent['validation_date'] = datetime.now().isoformat()
        agent['execution_script'] = 'run_github_researcher.py'
        agent['notes'] = '首个通过完整治理验收的 Learning Agent (2026-03-11)'
        
        print('✅ GitHub_Researcher 状态已更新')
        print(f'  production_ready: {agent["production_ready"]}')
        print(f'  validation_status: {agent["validation_status"]}')
        print(f'  validation_date: {agent["validation_date"]}')
        print(f'  execution_script: {agent["execution_script"]}')
        print(f'  notes: {agent["notes"]}')
        break

# 写回
with open(agents_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('\n✅ agents.json 已更新')
