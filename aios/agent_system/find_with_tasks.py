#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

data = json.load(open('agents.json', encoding='utf-8'))
agents = [a for a in data['agents'] if a.get('group') == 'learning']
with_tasks = [a for a in agents if a.get('stats', {}).get('tasks_total', 0) > 0]

print(f'Agents with tasks: {len(with_tasks)}')
for a in with_tasks:
    print(f"  - {a['name']}: {a.get('stats', {}).get('tasks_total', 0)} tasks")
    print(f"    enabled={a.get('enabled')}, mode={a.get('mode')}")
