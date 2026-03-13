import json

# 看所有任务的状态分布
stats = {}
recent = []
with open('task_executions.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            r = json.loads(line)
            s = r.get('status', 'unknown')
            stats[s] = stats.get(s, 0) + 1
            recent.append(r)
        except:
            pass

print('状态分布:', stats)
print(f'总记录数: {len(recent)}')
print('\n最近5条:')
for r in recent[-5:]:
    agent = r.get('agent_id', '?')
    status = r.get('status', '?')
    task = str(r.get('task', r.get('task_id', '')))[:60]
    print(f'  [{status}] {agent}: {task}')
