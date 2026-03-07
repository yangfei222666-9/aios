import json
from pathlib import Path
import lancedb

v4 = Path('experience_db_v4.jsonl')
entries = [json.loads(l) for l in v4.read_text(encoding='utf-8').splitlines() if l.strip()]

by_type = {}
for e in entries:
    et = str(e.get('error_type', '?'))
    s = e.get('strategy', '?')
    if et not in by_type:
        by_type[et] = []
    by_type[et].append(s)

print(f'experience_db_v4: {len(entries)} entries')
for et in sorted(by_type.keys()):
    print(f'  {et}: {by_type[et]}')

dep = by_type.get('dependency_error', [])
non_default = [s for s in dep if s != 'default_recovery']
print(f'\ndependency_error non-default strategies: {non_default}')
print(f'resource_exhausted strategies: {by_type.get("resource_exhausted", [])}')

db = lancedb.connect('experience_db.lance')
t = db.open_table('success_patterns')
print(f'\nLanceDB total: {t.count_rows()}')
df = t.to_pandas()
for _, r in df.iterrows():
    print(f'  {r["task_id"]} | {r["error_type"]} | {r["strategy_used"]} | conf={r["confidence"]}')
