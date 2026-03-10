import json

# 要激活的 agents
to_activate = [
    'GitHub_Issue_Tracker',
    'Competitor_Tracker',
    'Documentation_Writer',
    'Quick_Win_Hunter'
]

with open('agents.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

activated = 0
for agent in data['agents']:
    if agent['name'] in to_activate and agent.get('mode') == 'shadow':
        agent['mode'] = 'active'
        activated += 1
        print(f"✓ Activated: {agent['name']}")

with open('agents.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nTotal activated: {activated}")
