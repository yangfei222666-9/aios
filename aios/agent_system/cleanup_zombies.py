#!/usr/bin/env python3
"""Clean up zombie tasks from queue"""
import json
from pathlib import Path
from datetime import datetime

def cleanup_zombies():
    queue_file = Path('data/task_queue.jsonl')
    archive_file = Path('archive/zombie_tasks_20260307.jsonl')
    archive_file.parent.mkdir(exist_ok=True)
    
    lines = queue_file.read_text(encoding='utf-8').strip().split('\n')
    zombies = []
    kept = []
    
    for line in lines:
        if not line.strip():
            continue
        task = json.loads(line)
        if task.get('status') == 'queued' and task.get('zombie_retries', 0) >= 1:
            task['status'] = 'failed'
            task['failed_at'] = datetime.now().isoformat()
            task['failure_reason'] = 'zombie_cleanup'
            zombies.append(task)
            print(f"Archived: {task['id']} - {task['description']}")
        else:
            kept.append(task)
    
    # Write back kept tasks
    queue_file.write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in kept) + '\n', encoding='utf-8')
    
    # Archive zombies
    if zombies:
        with archive_file.open('a', encoding='utf-8') as f:
            for z in zombies:
                f.write(json.dumps(z, ensure_ascii=False) + '\n')
    
    print(f'\nCleaned: {len(zombies)} zombies')
    print(f'Kept: {len(kept)} tasks')
    return len(zombies), len(kept)

if __name__ == '__main__':
    cleanup_zombies()
