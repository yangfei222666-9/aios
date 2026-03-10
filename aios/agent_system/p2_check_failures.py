#!/usr/bin/env python3
"""Check recent failures in last 24h"""

import json
from datetime import datetime, timedelta
from pathlib import Path

exec_file = Path('task_executions.jsonl')
if not exec_file.exists():
    print('task_executions.jsonl not found')
    exit(0)

cutoff = (datetime.now() - timedelta(hours=24)).isoformat()

failures = []
with open(exec_file, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            timestamp = r.get('timestamp', 0)
            if isinstance(timestamp, (int, float)):
                ts = datetime.fromtimestamp(timestamp).isoformat()
            else:
                ts = timestamp
            
            if ts >= cutoff and r.get('status') == 'failed':
                failures.append(r)
        except Exception as e:
            pass

print(f'Recent 24h failures: {len(failures)}')
if len(failures) > 0:
    print('\nRecent failures:')
    for i, f in enumerate(failures[-5:], 1):
        agent_id = f.get('agent_id', 'N/A')
        task_id = f.get('task_id', 'N/A')
        print(f'{i}. {agent_id} - {task_id}')
