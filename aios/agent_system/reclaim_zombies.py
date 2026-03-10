#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动回收僵尸任务，重置为 pending 以便重新执行"""
import json
import time

queue_file = 'data/task_queue.jsonl'

tasks = [json.loads(l) for l in open(queue_file,'r',encoding='utf-8') if l.strip()]

now = time.time()
reclaimed = 0
for t in tasks:
    if t.get('status') != 'running':
        continue
    updated = t.get('updated_at', 0)
    age = now - float(updated) if updated else 9999
    if age > 300:  # 超过 5 分钟
        retry = t.get('retry_count', 0)
        if retry < 2:
            t['status'] = 'pending'
            t['retry_count'] = retry + 1
            t['updated_at'] = now
            print(f"[RECLAIM] {t.get('task_id','?')[:40]} → pending (retry {retry+1})")
        else:
            t['status'] = 'failed'
            t['updated_at'] = now
            print(f"[FAIL] {t.get('task_id','?')[:40]} → failed (max retries)")
        reclaimed += 1

with open(queue_file,'w',encoding='utf-8') as f:
    for t in tasks:
        f.write(json.dumps(t, ensure_ascii=False) + '\n')

print(f"\nReclaimed: {reclaimed} tasks")
