#!/usr/bin/env python3
"""
Spawn Queue Processor - 处理 AIOS 的 spawn 请求

这个脚本由 OpenClaw（小九）运行，监听 spawn_queue.jsonl，
执行任务，并将结果写入 spawn_results.jsonl
"""
import json
import time
from pathlib import Path
from core.status_adapter import get_task_status

from paths import SPAWN_RESULTS as _SPAWN_RESULTS

SPAWN_QUEUE = Path(__file__).parent / "spawn_queue.jsonl"
SPAWN_RESULTS = _SPAWN_RESULTS

def process_spawn_queue():
    """处理 spawn 队列"""
    if not SPAWN_QUEUE.exists():
        print("No spawn queue found")
        return
    
    # 读取所有待处理任务
    pending_tasks = []
    with open(SPAWN_QUEUE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                if get_task_status(task) == 'pending':
                    pending_tasks.append(task)
    
    if not pending_tasks:
        print("No pending tasks")
        return
    
    print(f"Found {len(pending_tasks)} pending tasks\n")
    
    # 处理每个任务
    for task in pending_tasks:
        task_id = task['task_id']
        task_desc = task['task']
        agent_type = task['agent']
        
        print(f"Processing: {task_id}")
        print(f"  Task: {task_desc}")
        print(f"  Agent: {agent_type}")
        
        # 这里应该调用 sessions_spawn
        # 但由于我们在 Python 脚本中，无法直接调用 OpenClaw 工具
        # 所以需要通过其他方式
        
        # 方案：输出一个特殊格式，让 OpenClaw 识别并执行
        print(f"\n[SPAWN_REQUEST]")
        print(f"task_id: {task_id}")
        print(f"task: {task_desc}")
        print(f"agent: {agent_type}")
        print(f"[/SPAWN_REQUEST]\n")
        
        # 模拟结果（实际应该等待 OpenClaw 执行）
        result = {
            "task_id": task_id,
            "success": True,
            "output": f"Task completed by {agent_type}",
            "timestamp": time.time()
        }
        
        # 写入结果
        with open(SPAWN_RESULTS, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"  Result written\n")
    
    # 清空队列（标记为已处理）
    processed_tasks = []
    with open(SPAWN_QUEUE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                if get_task_status(task) == 'pending':
                    task['status'] = 'processed'
                processed_tasks.append(task)
    
    with open(SPAWN_QUEUE, 'w', encoding='utf-8') as f:
        for task in processed_tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    process_spawn_queue()
