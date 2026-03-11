#!/usr/bin/env python3
"""
手动触发 4 个文档 Agent 进行 smoke test

目标：验证拆分后的文档任务是否在 60s 内稳定通过
"""

import json
import time
from pathlib import Path
from datetime import datetime

# 4 个文档 Agent
DOCS_AGENTS = [
    {
        "name": "Docs_Unified_Writer",
        "task_desc": "统一 AIOS 主文档到 README.md（合并 INSTALL/API/TUTORIAL）"
    },
    {
        "name": "Docs_Demo_Writer",
        "task_desc": "撰写真实场景 demo 文档（文件监控、API 健康检查、日志分析）"
    },
    {
        "name": "Docs_QuickStart_Writer",
        "task_desc": "撰写 5 分钟快速开始指南"
    },
    {
        "name": "Docs_FAQ_Writer",
        "task_desc": "维护常见问题解答文档"
    }
]

def create_task(agent_name: str, task_desc: str) -> dict:
    """创建任务记录"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    task_id = f"smoke-{agent_name}-{timestamp}"
    
    task = {
        "task_id": task_id,
        "agent_id": agent_name,
        "type": "learning",
        "description": task_desc,
        "priority": "normal",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "retry_count": 0,
        "smoke_test": True  # 标记为 smoke test
    }
    
    return task

def main():
    """主函数"""
    print("=" * 60)
    print("文档 Agent Smoke Test")
    print("=" * 60)
    print(f"时间: {datetime.now().isoformat()}")
    print(f"目标: 验证 4 个文档子任务是否在 60s 内通过\n")
    
    # 创建任务队列文件路径
    queue_file = Path("data/task_queue.jsonl")
    
    # 读取现有队列
    existing_tasks = []
    if queue_file.exists():
        with open(queue_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing_tasks.append(json.loads(line))
    
    # 创建 4 个测试任务
    test_tasks = []
    for agent in DOCS_AGENTS:
        task = create_task(agent["name"], agent["task_desc"])
        test_tasks.append(task)
        print(f"✓ 创建任务: {agent['name']}")
        print(f"  描述: {agent['task_desc']}")
        print(f"  Task ID: {task['task_id']}\n")
    
    # 追加到队列
    with open(queue_file, 'a', encoding='utf-8') as f:
        for task in test_tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
    
    print("=" * 60)
    print(f"✅ 已创建 {len(test_tasks)} 个 smoke test 任务")
    print("=" * 60)
    print("\n下一步:")
    print("1. 运行 heartbeat 或 auto_dispatcher 触发任务执行")
    print("2. 观察 task_executions.jsonl 中的执行结果")
    print("3. 检查每个任务的耗时和成功率")
    print("\n手动触发命令:")
    print("  cd C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system")
    print("  python auto_dispatcher.py cron")

if __name__ == '__main__':
    main()
