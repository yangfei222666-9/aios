#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""蹇収妫€鏌ワ細楠岃瘉 Learning Agent 闂幆 4 涓叧閿偣"""
import json
import time

queue_file = 'data/task_queue.jsonl'
exec_file = 'data/task_executions_v2.jsonl'
agents_file = 'agents.json'

print('=== 褰撳墠鐘舵€佸揩鐓?===')
print(f'鏃堕棿: {time.strftime("%Y-%m-%d %H:%M:%S")}')

# 1. 闃熷垪鐘舵€?tasks = [json.loads(l) for l in open(queue_file,'r',encoding='utf-8') if l.strip()]
pending = [t for t in tasks if t.get('status')=='pending']
running = [t for t in tasks if t.get('status')=='running']

print(f'\n1. 闃熷垪鐘舵€?(data/task_queue.jsonl):')
print(f'   Pending: {len(pending)}')
print(f'   Running: {len(running)}')
if running:
    print(f'   Running task: {running[0].get("task_id","?")[:40]}')

# 2. 鎵ц璁板綍
execs = [json.loads(l) for l in open(exec_file,'r',encoding='utf-8') if l.strip()]
github_execs = [e for e in execs if 'GitHub_Researcher' in e.get('agent_id','')]

print(f'\n2. 鎵ц璁板綍 (data/task_executions_v2.jsonl):')
print(f'   Total: {len(execs)}')
print(f'   GitHub_Researcher: {len(github_execs)}')
if github_execs:
    last = github_execs[-1]
    print(f'   Last: {last.get("status")} at {last.get("start_time","?")[:19]}')

# 3. Agent stats
agents = json.load(open(agents_file,'r',encoding='utf-8'))
gr = next((a for a in agents['agents'] if a['name']=='GitHub_Researcher'), None)

print(f'\n3. Agent stats (agents.json):')
if gr:
    stats = gr.get('stats',{})
    print(f'   GitHub_Researcher.tasks_completed: {stats.get("tasks_completed",0)}')
    print(f'   GitHub_Researcher.tasks_failed: {stats.get("tasks_failed",0)}')
else:
    print('   GitHub_Researcher: NOT FOUND')

# 4. 閲嶅浠诲姟妫€鏌?github_tasks = [t for t in tasks if 'GitHub_Researcher' in t.get('agent_id','')]
print(f'\n4. 閲嶅浠诲姟妫€鏌?')
print(f'   GitHub_Researcher tasks in queue: {len(github_tasks)}')
for t in github_tasks:
    print(f'   - {t.get("task_id","?")[:40]} | {t.get("status")}')

