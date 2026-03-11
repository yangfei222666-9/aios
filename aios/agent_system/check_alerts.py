#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查今日新告警"""

import json
from pathlib import Path
from datetime import datetime

alerts_file = Path(__file__).parent / "data" / "skill_failure_alerts.jsonl"
alerts = [json.loads(line) for line in alerts_file.read_text(encoding='utf-8').strip().split('\n') if line]

today = datetime.now().date().isoformat()
new_alerts = [a for a in alerts if a['detected_at'].startswith(today)]

print(f'Total alerts: {len(alerts)}')
print(f'New alerts today: {len(new_alerts)}')

if new_alerts:
    print('\nNew alerts:')
    for a in new_alerts:
        print(f"  {a['skill_id']} - {a['alert_level']} - {a['last_failure_reason']}")
else:
    print('\n✅ No new alerts today')
