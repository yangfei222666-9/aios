#!/usr/bin/env python3
"""P2: Analyze Bug_Hunter timeout root cause"""

import json
from pathlib import Path
from datetime import datetime

def analyze_bug_hunter_timeouts():
    exec_file = Path('agent_executions.jsonl')
    if not exec_file.exists():
        print('agent_executions.jsonl not found')
        return
    
    # Collect Bug_Hunter timeout records
    timeouts = []
    with open(exec_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get('agent_id') == 'Bug_Hunter' and record.get('status') == 'timeout':
                timeouts.append(record)
    
    # Sort by time, get recent 3
    timeouts.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    recent_3 = timeouts[:3]
    
    print(f'Total Bug_Hunter timeouts: {len(timeouts)}')
    print(f'Recent 3 samples:\n')
    
    for i, record in enumerate(recent_3, 1):
        print(f'=== Sample {i} ===')
        print(f'Execution ID: {record.get("execution_id", "N/A")}')
        print(f'Start Time: {record.get("start_time", "N/A")}')
        print(f'End Time: {record.get("end_time", "N/A")}')
        print(f'Duration: {record.get("duration_seconds", "N/A")}s')
        
        task_input = record.get('task_input', 'N/A')
        if len(task_input) > 200:
            task_input = task_input[:200] + '...'
        print(f'Task Input: {task_input}')
        
        print(f'Error: {record.get("error", "N/A")}')
        
        metadata = record.get('metadata', {})
        print(f'Metadata: {json.dumps(metadata, indent=2, ensure_ascii=False)}')
        print()

if __name__ == '__main__':
    analyze_bug_hunter_timeouts()
