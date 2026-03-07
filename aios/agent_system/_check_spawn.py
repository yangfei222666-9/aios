from paths import SPAWN_REQUESTS
import json
from pathlib import Path

f = SPAWN_REQUESTS
lines = [l.strip() for l in f.read_text(encoding='utf-8').splitlines() if l.strip()]
print(f'Total spawn requests: {len(lines)}')
for line in lines[-5:]:
    d = json.loads(line)
    ts = d.get('timestamp','')[:19]
    tid = d.get('task_id','')
    label = d.get('label','')
    print(f'  {ts} | {tid} | {label}')


