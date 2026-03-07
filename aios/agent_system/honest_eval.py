#!/usr/bin/env python3
"""诚实评估 AIOS"""
import json
from pathlib import Path
from paths import TASK_QUEUE

tasks = []
with open(TASK_QUEUE, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            tasks.append(json.loads(line))

print('=== 诚实评估 ===\n')

# 检查最近完成的任务
completed = [t for t in tasks if t.get('status') == 'completed']
print(f'已完成任务: {len(completed)}\n')

print('最近5个任务的执行结果:')
for t in completed[-5:]:
    result = t.get('result', {})
    output = result.get('output', 'no output')
    agent = result.get('agent', 'unknown')
    desc = t.get('description', '')[:50]
    print(f'  - {desc}')
    print(f'    Agent: {agent}')
    print(f'    Output: {output}')
    print()

print('真相:')
print('  1. TaskExecutor 写入 spawn_requests.jsonl')
print('  2. 返回模拟结果: "Task completed by {agent} agent"')
print('  3. 没有真正调用 Claude API')
print('  4. 没有真正执行任何代码')
print('  5. 所有"成功"都是模拟的\n')

print('真实评分:')
print('  - 任务队列系统: 工作正常 (100%)')
print('  - 任务执行系统: 未实现 (0%)')
print('  - 整体评分: 50/100 (D级)\n')

print('下一步:')
print('  1. 实现真实的 Agent 执行（通过 sessions_spawn）')
print('  2. 或者集成 Claude API 直接调用')
print('  3. 验证任务真的产生了效果')
