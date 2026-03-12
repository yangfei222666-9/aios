#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4 类样本回归测试
验证"状态 / 分桶 / 建议"三者一致性
"""
import json
from agent_availability_classifier import classify_agent_availability

data = json.load(open('agents.json', encoding='utf-8'))
agents = [a for a in data['agents'] if a.get('group') == 'learning']

# 找 4 类样本
samples = {}
for a in agents:
    bucket = classify_agent_availability(a)
    if bucket not in samples:
        samples[bucket] = a

print('=== 4 类样本回归测试 ===\n')
for bucket in ['active_routable', 'schedulable_idle', 'shadow', 'disabled']:
    if bucket in samples:
        a = samples[bucket]
        print(f'[{bucket.upper()}]')
        print(f'  Name: {a["name"]}')
        print(f'  enabled: {a.get("enabled")}')
        print(f'  mode: {a.get("mode")}')
        print(f'  tasks_total: {a.get("stats", {}).get("tasks_total", 0)}')
        print(f'  Classification: {classify_agent_availability(a)}')
        print()
