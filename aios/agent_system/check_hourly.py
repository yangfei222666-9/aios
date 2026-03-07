import json
from paths import AGENTS_STATE

agents = json.load(open(AGENTS_STATE, encoding='utf-8'))['agents']
hourly = [a for a in agents if a.get('schedule') == 'hourly']

print(f'Hourly agents: {len(hourly)}')
for a in hourly:
    print(f'  - {a.get("id")} ({a.get("priority")})')
