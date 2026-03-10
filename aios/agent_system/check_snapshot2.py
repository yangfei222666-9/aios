#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鎵╁睍蹇収锛氭鏌ユ墍鏈?learning agent 鐨勬墽琛岃褰?""
import json
import time

queue_file = 'data/task_queue.jsonl'
exec_file = 'data/task_executions_v2.jsonl'

tasks = [json.loads(l) for l in open(queue_file,'r',encoding='utf-8') if l.strip()]
execs = [json.loads(l) for l in open(exec_file,'r',encoding='utf-8') if l.strip()]

print('=== 闃熷垪鐘舵€?===')
for t in tasks:
    tid = t.get('task_id') or t.get('id','?')
    if 'learning' in tid:
        updated = t.get('updated_at',0)
        age = int((time.time() - float(updated))/60) if updated else -1
        print(f"  {tid[:45]} | {t.get('status')} | zombie={t.get('zombie_retries',0)} | {age}min ago")

print('\n=== 鏈€鏂?5 鏉℃墽琛岃褰?===')
for e in execs[-5:]:
    print(f"  {e.get('start_time','?')[:19]} | {e.get('agent_id','?')} | {e.get('status','?')}")

print('\n=== Learning Agent 鎵ц璁板綍 ===')
learning_agents = ['GitHub_Researcher','Documentation_Writer','GitHub_Issue_Tracker']
for agent in learning_agents:
    agent_execs = [e for e in execs if agent in e.get('agent_id','')]
    print(f"  {agent}: {len(agent_execs)} records")

