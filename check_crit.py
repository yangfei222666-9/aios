import json
from datetime import datetime, timedelta

cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
events = []
try:
    with open('aios/agent_system/data/events.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

crit = [e for e in events if e.get('level') == 'CRIT' and e.get('timestamp', '') > cutoff]
print(f'CRIT_COUNT:{len(crit)}')
for e in crit[:5]:
    print(f"{e.get('timestamp', '')} {e.get('summary', e.get('message', ''))}")
