import json

with open('data/agents.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

agents = data['agents']
print(f"总 Agent 数: {len(agents)}")

active = [a for a in agents if a.get('lifecycle_state') == 'active']
print(f"Active 状态: {len(active)}")

shadow = [a for a in agents if a.get('lifecycle_state') == 'shadow']
print(f"Shadow 状态: {len(shadow)}")

disabled = [a for a in agents if a.get('lifecycle_state') == 'disabled']
print(f"Disabled 状态: {len(disabled)}")

print("\nActive Agents:")
for a in active:
    print(f"  - {a['name']} ({a.get('role', 'N/A')})")
