#!/usr/bin/env python3
"""
Task Manager CLI - 任务队列管理工具

Usage:
    python task_manager.py list [--status pending|completed|failed]
    python task_manager.py cancel <task_id>
    python task_manager.py retry <task_id>
    python task_manager.py clear [completed|failed|all]
    python task_manager.py stats
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from paths import TASK_QUEUE as _TASK_QUEUE

QUEUE_FILE = _TASK_QUEUE

def load_tasks():
    """加载所有任务"""
    if not QUEUE_FILE.exists():
        return []
    
    tasks = []
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks

def save_tasks(tasks):
    """保存任务队列"""
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')

def list_tasks(status_filter=None):
    """列出任务"""
    tasks = load_tasks()
    
    if status_filter:
        tasks = [t for t in tasks if t.get('status') == status_filter]
    
    if not tasks:
        print(f"No tasks found" + (f" with status '{status_filter}'" if status_filter else ""))
        return
    
    # 按优先级和状态分组
    by_priority = defaultdict(list)
    for task in tasks:
        priority = task.get('priority', 'normal')
        by_priority[priority].append(task)
    
    # 优先级排序
    priority_order = ['urgent', 'high', 'medium', 'normal', 'low']
    
    total = len(tasks)
    print(f"\n=== Task Queue ({total} tasks) ===\n")
    
    for priority in priority_order:
        if priority not in by_priority:
            continue
        
        tasks_in_priority = by_priority[priority]
        print(f"[{priority.upper()}] ({len(tasks_in_priority)} tasks)")
        
        for task in tasks_in_priority:
            task_id = task.get('task_id') or task.get('id', 'unknown')
            task_type = task.get('type', 'unknown')
            status = task.get('status', 'unknown')
            desc = task.get('description', 'No description')
            
            # 状态图标
            status_icon = {
                'pending': '[ ]',
                'processing': '[~]',
                'completed': '[+]',
                'failed': '[x]'
            }.get(status, '[?]')
            
            # 截断描述
            if len(desc) > 60:
                desc = desc[:57] + '...'
            
            print(f"  {status_icon} {task_id[:20]:20} | {task_type:8} | {desc}")
        
        print()

def cancel_task(task_id):
    """取消任务"""
    tasks = load_tasks()
    
    found = False
    for task in tasks:
        tid = task.get('task_id') or task.get('id')
        if tid == task_id:
            if task.get('status') == 'completed':
                print(f"[ERROR] Task {task_id} is already completed, cannot cancel")
                return
            
            task['status'] = 'cancelled'
            task['updated_at'] = datetime.now().isoformat()
            found = True
            break
    
    if not found:
        print(f"[ERROR] Task {task_id} not found")
        return
    
    save_tasks(tasks)
    print(f"[OK] Task {task_id} cancelled")

def retry_task(task_id):
    """重试任务"""
    tasks = load_tasks()
    
    found = False
    for task in tasks:
        tid = task.get('task_id') or task.get('id')
        if tid == task_id:
            if task.get('status') not in ['failed', 'cancelled']:
                print(f"[ERROR] Task {task_id} is not failed/cancelled, cannot retry")
                return
            
            task['status'] = 'pending'
            task['updated_at'] = datetime.now().isoformat()
            if 'result' in task:
                del task['result']
            found = True
            break
    
    if not found:
        print(f"[ERROR] Task {task_id} not found")
        return
    
    save_tasks(tasks)
    print(f"[OK] Task {task_id} reset to pending")

def clear_tasks(target='completed'):
    """清理任务"""
    tasks = load_tasks()
    original_count = len(tasks)
    
    if target == 'all':
        tasks = []
    elif target == 'completed':
        tasks = [t for t in tasks if t.get('status') != 'completed']
    elif target == 'failed':
        tasks = [t for t in tasks if t.get('status') != 'failed']
    else:
        print(f"[ERROR] Invalid target: {target}")
        return
    
    removed = original_count - len(tasks)
    save_tasks(tasks)
    print(f"[OK] Removed {removed} {target} tasks")

def show_stats():
    """显示统计信息"""
    tasks = load_tasks()
    
    if not tasks:
        print("No tasks in queue")
        return
    
    # 统计
    by_status = defaultdict(int)
    by_type = defaultdict(int)
    by_priority = defaultdict(int)
    
    for task in tasks:
        by_status[task.get('status', 'unknown')] += 1
        by_type[task.get('type', 'unknown')] += 1
        by_priority[task.get('priority', 'normal')] += 1
    
    print("\n=== Task Queue Statistics ===\n")
    
    print("By Status:")
    for status, count in sorted(by_status.items()):
        print(f"  {status:12} : {count:3}")
    
    print("\nBy Type:")
    for task_type, count in sorted(by_type.items()):
        print(f"  {task_type:12} : {count:3}")
    
    print("\nBy Priority:")
    priority_order = ['urgent', 'high', 'medium', 'normal', 'low']
    for priority in priority_order:
        if priority in by_priority:
            print(f"  {priority:12} : {by_priority[priority]:3}")
    
    print(f"\nTotal: {len(tasks)} tasks")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        status_filter = None
        if len(sys.argv) > 2 and sys.argv[2] == '--status':
            status_filter = sys.argv[3] if len(sys.argv) > 3 else None
        list_tasks(status_filter)
    
    elif command == 'cancel':
        if len(sys.argv) < 3:
            print("[ERROR] Usage: task_manager.py cancel <task_id>")
            sys.exit(1)
        cancel_task(sys.argv[2])
    
    elif command == 'retry':
        if len(sys.argv) < 3:
            print("[ERROR] Usage: task_manager.py retry <task_id>")
            sys.exit(1)
        retry_task(sys.argv[2])
    
    elif command == 'clear':
        target = sys.argv[2] if len(sys.argv) > 2 else 'completed'
        clear_tasks(target)
    
    elif command == 'stats':
        show_stats()
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
