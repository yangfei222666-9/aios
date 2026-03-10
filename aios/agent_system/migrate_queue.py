#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate task_queue.jsonl from root to data/ directory
"""
import json

# 读取根目录队列（新）
with open('task_queue.jsonl','r',encoding='utf-8') as f:
    new_tasks = [json.loads(l) for l in f if l.strip()]

# 读取 data 队列（旧）
with open('data/task_queue.jsonl','r',encoding='utf-8') as f:
    old_tasks = [json.loads(l) for l in f if l.strip()]

# 合并（去重）
task_ids = {t.get('task_id') or t.get('id') for t in old_tasks}
merged = old_tasks.copy()
for t in new_tasks:
    tid = t.get('task_id') or t.get('id')
    if tid not in task_ids:
        merged.append(t)
        print(f'Migrated: {tid}')

# 写回 data 队列
with open('data/task_queue.jsonl','w',encoding='utf-8') as f:
    for t in merged:
        f.write(json.dumps(t, ensure_ascii=False) + '\n')

print(f'\nTotal tasks in data/task_queue.jsonl: {len(merged)}')
print(f'Pending: {sum(1 for t in merged if t.get("status")=="pending")}')
