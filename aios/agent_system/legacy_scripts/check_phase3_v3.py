import json, lancedb
from pathlib import Path

# 1. experience_db.lance 状态
db = lancedb.connect('experience_db.lance')
tables = db.table_names()
print(f'experience_db tables: {tables}')
for t in tables:
    tbl = db.open_table(t)
    cnt = tbl.count_rows()
    print(f'  {t}: {cnt} rows')
    if cnt > 0:
        df = tbl.to_pandas()
        print(f'  columns: {list(df.columns)}')
        for _, row in df.head(5).iterrows():
            tid = row.get('task_id', '?')
            etype = row.get('error_type', '?')
            strat = row.get('strategy_used', '?')
            conf = row.get('confidence', '?')
            print(f'    task_id={tid} error_type={etype} strategy={strat} confidence={conf}')

# 2. lancedb_memory 状态
db2 = lancedb.connect('lancedb_memory')
tables2 = db2.table_names()
print(f'\nlancedb_memory tables: {tables2}')
for t in tables2:
    tbl = db2.open_table(t)
    cnt = tbl.count_rows()
    print(f'  {t}: {cnt} rows')

# 3. experience_library.jsonl 详情
exp_file = Path('experience_library.jsonl')
if exp_file.exists():
    with open(exp_file, 'r', encoding='utf-8') as f:
        exps = [json.loads(l) for l in f if l.strip()]
    print(f'\nexperience_library: {len(exps)} entries')
    for e in exps:
        lid = e.get('lesson_id', '?')
        etype = e.get('error_type', '?')
        succ = e.get('success', '?')
        strat = e.get('strategy', {})
        actions = strat.get('actions', [])
        action_types = [a.get('type', '?') for a in actions]
        print(f'  {lid} | error={etype} | success={succ} | actions={action_types}')

# 4. lessons.json 详情
lessons_file = Path('lessons.json')
if lessons_file.exists():
    with open(lessons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lessons = data.get('lessons', [])
    print(f'\nlessons: {len(lessons)} entries')
    for l in lessons:
        lid = l.get('id', '?')
        etype = l.get('error_type', '?')
        desc = l.get('description', l.get('context', ''))[:60]
        print(f'  {lid} | error={etype} | desc={desc}')

# 5. spawn_requests 重生请求
spawn_file = Path('spawn_requests.jsonl')
if spawn_file.exists():
    with open(spawn_file, 'r', encoding='utf-8') as f:
        spawns = [json.loads(l) for l in f if l.strip()]
    regen = [s for s in spawns if s.get('regeneration')]
    print(f'\nspawn_requests (regen): {len(regen)} entries')
    for s in regen:
        tid = s.get('task_id', '?')
        ts = s.get('timestamp', '?')
        rec = s.get('recommendation', {})
        rec_strat = rec.get('strategy', 'N/A')
        rec_src = rec.get('source', 'N/A')
        print(f'  {tid} | ts={ts} | rec_strategy={rec_strat} | rec_source={rec_src}')
