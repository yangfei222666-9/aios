import json
with open('agents.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
learning = [a for a in data['agents'] if a.get('group') == 'learning']
active = [a for a in learning if a.get('mode') == 'active']
shadow = [a for a in learning if a.get('mode') == 'shadow']
print(f'Active: {len(active)}')
print(f'Shadow: {len(shadow)}')
print('\nShadow agents (high priority):')
for a in shadow:
    if a.get('priority') == 'high':
        print(f"  {a['name']} - {a['role']}")
