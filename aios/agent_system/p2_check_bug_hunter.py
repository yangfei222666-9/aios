#!/usr/bin/env python3
"""Check Bug_Hunter execution records"""

import json
from pathlib import Path

def check_bug_hunter():
    exec_file = Path('task_executions.jsonl')
    if not exec_file.exists():
        print('task_executions.jsonl not found')
        return
    
    # Collect all Bug_Hunter records
    all_records = []
    timeout_records = []
    
    with open(exec_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                agent_id = record.get('agent_id', '')
                status = record.get('status', '')
                
                if 'Bug_Hunter' in agent_id:
                    all_records.append(record)
                    if status == 'timeout':
                        timeout_records.append(record)
            except Exception as e:
                print(f'Error parsing line: {e}')
                continue
    
    print(f'Total Bug_Hunter records: {len(all_records)}')
    print(f'Total Bug_Hunter timeouts: {len(timeout_records)}')
    print()
    
    if len(all_records) > 0:
        print('Recent 5 Bug_Hunter records:')
        for i, record in enumerate(all_records[-5:], 1):
            print(f'{i}. {record.get("agent_id", "N/A")} - {record.get("status", "N/A")} - {record.get("start_time", "N/A")}')
    
    if len(timeout_records) > 0:
        print()
        print('Timeout records:')
        for i, record in enumerate(timeout_records, 1):
            print(f'{i}. {record.get("execution_id", "N/A")} - {record.get("start_time", "N/A")}')

if __name__ == '__main__':
    check_bug_hunter()
