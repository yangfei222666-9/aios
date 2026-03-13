import json
from pathlib import Path

data = json.loads(Path('agents.json').read_text(encoding='utf-8'))
agents = data.get('agents', [])
zombies = [a for a in agents if a.get('stats', {}).get('tasks_completed', 0) == 0 and a.get('stats', {}).get('tasks_failed', 0) == 0]
failing = [a for a in agents if a.get('stats', {}).get('tasks_failed', 0) >= 3]

print(f'Zombies: {len(zombies)}')
print(f'Failing: {len(failing)}')

if zombies:
    print('\nZombie Agents:')
    for a in zombies[:5]:
        print(f"  - {a['name']}")

if failing:
    print('\nFailing Agents:')
    for a in failing[:5]:
        print(f"  - {a['name']} (failed {a['stats']['tasks_failed']})")
