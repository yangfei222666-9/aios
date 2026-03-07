import json
from pathlib import Path

# lessons.json 结构
with open('lessons.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'lessons.json type: {type(data)}')
if isinstance(data, dict):
    keys = list(data.keys())[:10]
    print(f'keys: {keys}')
    for k in keys[:3]:
        v = data[k]
        print(f'  {k}: {type(v).__name__} = {str(v)[:100]}')
elif isinstance(data, list):
    print(f'length: {len(data)}')
    if data:
        first = data[0]
        print(f'first item type: {type(first).__name__}')
        print(f'first item: {str(first)[:200]}')

# task_executions 状态字段
with open('task_executions.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(l) for l in f if l.strip()]
statuses = set()
for e in lines[-20:]:
    statuses.add(e.get('status', 'MISSING'))
print(f'\ntask_executions 最近状态值: {statuses}')
print(f'最近5条:')
for e in lines[-5:]:
    tid = e.get('task_id', '?')
    aid = e.get('agent_id', '?')
    st = e.get('status', '?')
    res = str(e.get('result', ''))[:60]
    print(f'  {tid} | agent={aid} | status={st} | result={res}')

# experience_library
exp_file = Path('experience_library.jsonl')
if exp_file.exists():
    with open(exp_file, 'r', encoding='utf-8') as f:
        exps = [json.loads(l) for l in f if l.strip()]
    print(f'\n经验库: {len(exps)} 条')
    for e in exps[-3:]:
        tid = e.get('task_id', '?')
        stype = e.get('strategy', {}).get('type', 'N/A')
        succ = e.get('success', '?')
        print(f'  {tid} | strategy={stype} | success={succ}')
else:
    print('\n经验库不存在')

# LanceDB 相关文件
print('\nLance相关文件:')
for p in Path('.').rglob('*lance*'):
    print(f'  {p}')
