#!/usr/bin/env python3
"""获取真实系统状态 - 无模拟"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 1. 读取真实 Agent 状态
with open('data/agents.json', encoding='utf-8') as f:
    agents_data = json.load(f)

print('=== Agent 状态（真实数据）===')
enabled_agents = [a for a in agents_data['agents'] if a.get('enabled')]
print(f'启用的 Agent: {len(enabled_agents)}')
for a in enabled_agents:
    stats = a.get('stats', {})
    print(f"  {a['name']}: {stats.get('tasks_completed', 0)}/{stats.get('tasks_total', 0)} 成功, {stats.get('success_rate', 0):.0f}% 成功率")

# 2. 读取真实 Trace 数据
traces = [json.loads(l) for l in open('data/traces/agent_traces.jsonl', encoding='utf-8')]
print(f'\n=== Trace 记录（真实数据）===')
print(f'总记录数: {len(traces)}')

agent_counts = Counter(t['agent_id'] for t in traces)
print('\nTop 5 活跃 Agent:')
for agent, count in sorted(agent_counts.items(), key=lambda x: -x[1])[:5]:
    successes = sum(1 for t in traces if t['agent_id'] == agent and t.get('success'))
    print(f'  {agent}: {count} 次任务, {successes} 次成功 ({100*successes//count if count else 0}%)')

# 3. 最近 24h 的真实任务
now = datetime.now()
recent = []
for t in traces:
    if 'timestamp' in t:
        try:
            ts = datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00'))
            if ts > now - timedelta(hours=24):
                recent.append(t)
        except:
            pass

print(f'\n=== 最近 24h 任务（真实数据）===')
print(f'任务数: {len(recent)}')
if recent:
    success_count = sum(1 for t in recent if t.get('success'))
    print(f'成功: {success_count}, 失败: {len(recent)-success_count}')
    print(f'成功率: {100*success_count//len(recent)}%')

# 4. 失败任务详情
failures = [t for t in traces if not t.get('success') and t.get('error')]
print(f'\n=== 失败任务（真实数据）===')
print(f'总失败数: {len(failures)}')
if failures:
    error_types = Counter(t.get('error', 'unknown')[:50] for t in failures)
    print('\nTop 3 失败原因:')
    for error, count in error_types.most_common(3):
        print(f'  {error}: {count} 次')

# 5. Memory Server 状态
import requests
try:
    resp = requests.get('http://127.0.0.1:7788/status', timeout=2)
    if resp.status_code == 200:
        data = resp.json()
        print(f'\n=== Memory Server（真实状态）===')
        print(f'状态: 运行中')
        print(f'响应时间: {resp.elapsed.total_seconds()*1000:.2f}ms')
        print(f'模型: {data.get("model", "unknown")}')
except Exception as e:
    print(f'\n=== Memory Server（真实状态）===')
    print(f'状态: 离线 ({str(e)[:50]})')
