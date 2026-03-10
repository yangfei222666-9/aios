#!/usr/bin/env python3
"""AIOS Agent 统计"""
import json
from pathlib import Path

agents_file = Path(__file__).parent / 'agents.json'
with open(agents_file, encoding='utf-8') as f:
    data = json.load(f)

agents = data.get('agents', [])
print(f'Total agents: {len(agents)}')
print(f'Enabled: {sum(1 for a in agents if a.get("enabled"))}')
print(f'Mode active: {sum(1 for a in agents if a.get("mode") == "active")}')
print(f'Production ready: {sum(1 for a in agents if a.get("production_ready"))}')

stats = [a.get('stats', {}) for a in agents if 'stats' in a]
total_tasks = sum(s.get('tasks_total', 0) for s in stats)
completed = sum(s.get('tasks_completed', 0) for s in stats)
failed = sum(s.get('tasks_failed', 0) for s in stats)

print(f'\nTask stats:')
print(f'  Total: {total_tasks}')
print(f'  Completed: {completed}')
print(f'  Failed: {failed}')
print(f'  Success rate: {round(completed/total_tasks*100, 1) if total_tasks > 0 else 0}%')
