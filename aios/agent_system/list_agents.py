import json
from paths import AGENTS_STATE
d = json.load(open(AGENTS_STATE, encoding='utf-8'))
agents = d.get('agents', [])
print(f'Total agents: {len(agents)}')
print('\nAll agents:')
for i, a in enumerate(agents, 1):
    print(f'{i}. {a.get("name")} ({a.get("type", "?")})')
