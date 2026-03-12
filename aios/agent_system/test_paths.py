#!/usr/bin/env python3
"""快速验证 paths.TASK_EXECUTIONS 是否正确指向 v2"""
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
from paths import TASK_EXECUTIONS

print(f"TASK_EXECUTIONS = {TASK_EXECUTIONS}")
print(f"Exists: {TASK_EXECUTIONS.exists()}")

if TASK_EXECUTIONS.exists():
    import json
    records = [json.loads(line) for line in open(TASK_EXECUTIONS, encoding='utf-8') if line.strip()]
    print(f"Total records: {len(records)}")
    if records:
        print(f"Sample task_id: {records[0]['task_id']}")
        print(f"Sample agent_id: {records[0]['agent_id']}")
        print(f"Sample status: {records[0]['status']}")
