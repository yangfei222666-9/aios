from paths import SPAWN_PENDING
import json
from pathlib import Path

pending_file = SPAWN_PENDING
if pending_file.exists():
    lines = [l.strip() for l in pending_file.read_text(encoding='utf-8').splitlines() if l.strip()]
    print(f'Pending spawns: {len(lines)}')
    for line in lines:
        req = json.loads(line)
        tid = req.get('task_id', '')
        label = req.get('label', '')
        timeout = req.get('runTimeoutSeconds', 120)
        task_preview = req.get('task', '')[:80].strip()
        print(f'  task_id={tid} label={label} timeout={timeout}s')
        print(f'  task_preview={task_preview}...')
        print()
else:
    print('No spawn_pending.jsonl')


