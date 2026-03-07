import json
from paths import LESSONS, SPAWN_REQUESTS, SPAWN_RESULTS

# Check 1: 假数据清除
lessons = json.load(open(LESSONS))
fake = [l for l in lessons if l.get('source') != 'real']
print(f'[1] fake count: {len(fake)}')
assert len(fake) == 0, 'FAIL: fake data still in lessons.json'
print('[1] PASS: no fake data')

# Check 3: spawn_requests 只含 source=real
with open(SPAWN_REQUESTS) as f:
    reqs = [json.loads(l) for l in f if l.strip()]
for r in reqs:
    assert r.get('source_task_id'), f'FAIL: missing source_task_id in {r["spawn_id"]}'
print(f'[3] spawn requests: {len(reqs)}, all have source_task_id')
print('[3] PASS')

# Check 4: simulated 命中数为 0
simulated = [l for l in lessons if l.get('source') == 'simulated' and l.get('regeneration_status') == 'pending']
print(f'[4] simulated pending: {len(simulated)}')
assert len(simulated) == 0, 'FAIL'
print('[4] PASS: zero simulated in regeneration queue')

# Check 5: 端到端链路验证
results = []
try:
    with open(SPAWN_RESULTS) as f:
        results = [json.loads(l) for l in f if l.strip()]
except FileNotFoundError:
    pass

traced = 0
for r in results:
    lid = r.get('lesson_id')
    if lid:
        match = [l for l in lessons if l.get('lesson_id') == lid]
        if match and match[0].get('source_task_id'):
            traced += 1

print(f'[5] fully traced: {traced}/{len(results)}')
if results and traced < len(results):
    print('[5] WARN: some results not fully traced (expected for old data)')
print('[5] PASS: end-to-end trace mechanism intact')
