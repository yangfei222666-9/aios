#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from agent_availability_classifier import classify_agent_availability

data = json.load(open('agents.json', encoding='utf-8'))
agents = [a for a in data['agents'] if a.get('group') == 'learning']
active = [a for a in agents if classify_agent_availability(a) == 'active_routable']

print(f'Active routable agents: {len(active)}')
for a in active:
    print(f"  - {a['name']}: {a.get('stats', {}).get('tasks_total', 0)} tasks")
    print(f"    enabled: {a.get('enabled')}, mode: {a.get('mode')}")
