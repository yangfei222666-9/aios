import json

stats = {}
total = 0
retried_tasks = []

with open('task_executions_v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            total += 1
            agent = rec.get('result', {}).get('agent', 'unknown')
            retry = rec.get('retry_count', 0)
            if agent not in stats:
                stats[agent] = {'total': 0, 'retried': 0}
            stats[agent]['total'] += 1
            if retry > 0:
                stats[agent]['retried'] += 1
                retried_tasks.append({
                    'task_id': rec.get('task_id'),
                    'agent': agent,
                    'retry_count': retry,
                    'total_attempts': rec.get('total_attempts', 1),
                    'desc': rec.get('description', '')[:60]
                })
        except Exception as e:
            pass

print(f"Total records: {total}")
for agent, s in stats.items():
    print(f"  {agent}: {s['total']} tasks, {s['retried']} retried")

print(f"\nRetried tasks ({len(retried_tasks)}):")
for t in retried_tasks:
    print(f"  [{t['retry_count']} retries / {t['total_attempts']} attempts] {t['agent']} - {t['desc']}")

