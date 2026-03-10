import json
with open('task_queue.jsonl', 'r', encoding='utf-8') as f:
    tasks = [json.loads(l) for l in f if l.strip()]
print(f'Queue: {len(tasks)} tasks')
for t in tasks[-3:]:
    print(f"  {t['task_id'][:50]} | {t['agent_id']} | {t['status']}")
