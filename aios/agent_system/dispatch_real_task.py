#!/usr/bin/env python3
"""派发真实任务给 GitHub_Researcher"""
import json
import time
from pathlib import Path
from datetime import datetime

task = {
    'task_id': f'task-{int(time.time()*1000)}-real',
    'type': 'research',
    'agent_id': 'GitHub_Researcher',
    'description': '搜索 GitHub 上最新的 AIOS / AI Agent 框架项目，输出 top 3 项目名称和核心特点',
    'priority': 'high',
    'status': 'pending',
    'created_at': datetime.now().isoformat()
}

queue_file = Path('data/task_queue.jsonl')
with queue_file.open('a', encoding='utf-8') as f:
    f.write(json.dumps(task, ensure_ascii=False) + '\n')

print('✅ 已写入任务:', task['task_id'])
print('📋 任务内容:', task['description'])
print('🎯 目标 Agent:', task['agent_id'])
