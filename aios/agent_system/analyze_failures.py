#!/usr/bin/env python3
"""分析失败任务"""
import json
from pathlib import Path
from collections import defaultdict
from paths import TASK_QUEUE

# 1. 查看失败任务详情
tasks = []
with open(TASK_QUEUE, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            tasks.append(json.loads(line))

failed = [t for t in tasks if t.get('status') == 'failed']
print(f'=== 1. Failed Tasks ({len(failed)}) ===\n')
for i, t in enumerate(failed, 1):
    tid = t.get('task_id') or t.get('id', 'unknown')
    err = t.get('result', {}).get('error', 'unknown') if t.get('result') else 'no result'
    agent = t.get('result', {}).get('agent', 'unknown') if t.get('result') else 'unknown'
    print(f'[{i}] {tid}')
    print(f'    Type: {t.get("type")} | Priority: {t.get("priority")} | Agent: {agent}')
    print(f'    Desc: {t.get("description", "")}')
    print(f'    Error: {err}\n')

# 2. 分析失败原因
print('=== 2. Failure Analysis ===\n')
error_types = defaultdict(int)
agent_failures = defaultdict(int)

for t in failed:
    err = t.get('result', {}).get('error', 'unknown') if t.get('result') else 'no result'
    agent = t.get('result', {}).get('agent', 'unknown') if t.get('result') else 'unknown'
    error_types[err] += 1
    agent_failures[agent] += 1

print('By Error Type:')
for err, count in sorted(error_types.items(), key=lambda x: -x[1]):
    print(f'  {err}: {count}')

print('\nBy Agent:')
for agent, count in sorted(agent_failures.items(), key=lambda x: -x[1]):
    print(f'  {agent}: {count}')

# 3. 优化建议
print('\n=== 3. Optimization Suggestions ===\n')

# 检查是否都是模拟失败
simulated = sum(1 for t in failed if t.get('result', {}).get('error') == 'Simulated failure')
if simulated == len(failed):
    print('[INFO] All failures are simulated (test data)')
    print('       Real system is working fine!')
    print('\nAction: Clear test data')
    print('  python task_manager.py clear failed')
else:
    print('Real failures detected:')
    real_failures = [t for t in failed if t.get('result', {}).get('error') != 'Simulated failure']
    for t in real_failures:
        print(f'  - {t.get("description", "")}: {t.get("result", {}).get("error", "")}')
    
    print('\nSuggested fixes:')
    if 'coder' in agent_failures:
        print('  1. Review coder agent timeout settings')
        print('  2. Check code generation prompts')
    if 'analyst' in agent_failures:
        print('  1. Review analyst agent data access')
        print('  2. Check analysis prompts')
