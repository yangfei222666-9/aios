import json
from pathlib import Path

data_dir = Path(r'C:\Users\A\.openclaw\workspace\aios\agent_system\data')

lf = data_dir / 'lessons.json'
if lf.exists():
    with open(lf, encoding='utf-8') as f:
        lessons = json.load(f)
    ls = lessons.get('lessons', [])
    print(f'lessons.json: {len(ls)} 条')
    for l in ls[:5]:
        lid = l.get('lesson_id', '?')
        title = l.get('title', l.get('summary', ''))[:60]
        print(f'  - {lid} | {title}')
else:
    print('lessons.json: 不存在')

rf = data_dir / 'rules.json'
if rf.exists():
    with open(rf, encoding='utf-8') as f:
        rules = json.load(f)
    rs = rules.get('rules', [])
    print(f'rules.json: {len(rs)} 条')
    for r in rs[:5]:
        rid = r.get('rule_id', '?')
        title = r.get('title', r.get('description', ''))[:60]
        print(f'  - {rid} | {title}')
else:
    print('rules.json: 不存在')
