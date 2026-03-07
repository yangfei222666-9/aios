#!/usr/bin/env python3
"""批量创建任务"""

import json
from datetime import datetime
from pathlib import Path

def create_batch_tasks():
    """批量创建8个任务"""
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    tasks = [
        {
            'task_id': f'task-{timestamp}-001',
            'type': 'analysis',
            'description': '分析最近7天的错误日志，找出高频问题',
            'priority': 'high',
            'agent': 'analyst-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-002',
            'type': 'monitor',
            'description': '检查所有 Agent 的健康度，生成报告',
            'priority': 'high',
            'agent': 'monitor-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-003',
            'type': 'code',
            'description': '优化 heartbeat_v5.py 的任务处理逻辑，减少重复代码',
            'priority': 'medium',
            'agent': 'coder-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-004',
            'type': 'analysis',
            'description': '评估 Self-Improving Loop v2.0 的效果，统计改进成功率',
            'priority': 'medium',
            'agent': 'analyst-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-005',
            'type': 'monitor',
            'description': '检查磁盘空间使用率，清理临时文件',
            'priority': 'low',
            'agent': 'monitor-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-006',
            'type': 'code',
            'description': '为 DataCollector 添加批量查询接口',
            'priority': 'medium',
            'agent': 'coder-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-007',
            'type': 'analysis',
            'description': '分析 GitHub 上最新的 AIOS 相关项目（最近7天）',
            'priority': 'low',
            'agent': 'analyst-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'task_id': f'task-{timestamp}-008',
            'type': 'monitor',
            'description': '检查所有 Learning Agent 的运行状态',
            'priority': 'medium',
            'agent': 'monitor-dispatcher',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
    ]
    
from paths import TASK_QUEUE
    
    # 写入任务队列
    queue_file = TASK_QUEUE
    with open(queue_file, 'a', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
    
    print(f'[OK] Batch created {len(tasks)} tasks')
    for i, task in enumerate(tasks, 1):
        print(f'  [{i}] {task["priority"].upper():6} | {task["type"]:8} | {task["description"]}')
    
    return len(tasks)

if __name__ == '__main__':
    create_batch_tasks()
