#!/usr/bin/env python3
"""查找 Documentation_Writer 超时的详细信息"""

import json
from pathlib import Path
from datetime import datetime

# 1. 从 task_queue.jsonl 找任务信息
task_queue = Path("data/task_queue.jsonl")
doc_writer_task = None

if task_queue.exists():
    with open(task_queue, 'r', encoding='utf-8') as f:
        for line in f:
            if 'Documentation_Writer' in line:
                doc_writer_task = json.loads(line)
                break

if doc_writer_task:
    print("=" * 60)
    print("任务基本信息")
    print("=" * 60)
    print(f"Task ID: {doc_writer_task['task_id']}")
    print(f"Agent: {doc_writer_task['agent_id']}")
    print(f"描述: {doc_writer_task['description']}")
    print(f"状态: {doc_writer_task['status']}")
    print(f"创建时间: {doc_writer_task['created_at']}")
    print(f"重试次数: {doc_writer_task['retry_count']}")
    
    result = doc_writer_task.get('result', {})
    print(f"\n错误信息: {result.get('error', 'N/A')}")
    print(f"实际执行 Agent: {result.get('agent', 'N/A')}")
    print(f"总尝试次数: {result.get('total_attempts', 'N/A')}")

# 2. 从 agents.json 找 Documentation_Writer 配置
agents_file = Path("data/agents.json")
if agents_file.exists():
    with open(agents_file, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
        agents = agents_data if isinstance(agents_data, list) else agents_data.get('agents', [])
        
        for agent in agents:
            if agent.get('id') == 'Documentation_Writer':
                print("\n" + "=" * 60)
                print("Agent 配置")
                print("=" * 60)
                print(f"ID: {agent['id']}")
                print(f"名称: {agent['name']}")
                print(f"模板: {agent.get('template', 'N/A')}")
                print(f"状态: {agent.get('status', 'N/A')}")
                
                config = agent.get('config', {})
                print(f"\n超时设置: {config.get('timeout', 'N/A')}s")
                print(f"模型: {config.get('model', 'N/A')}")
                
                prompt = config.get('prompt', '')
                print(f"\nPrompt 长度: {len(prompt)} 字符")
                print(f"Prompt 前 200 字符:\n{prompt[:200]}...")
                
                stats = agent.get('stats', {})
                print(f"\n统计:")
                print(f"  总任务: {stats.get('tasks_completed', 0) + stats.get('tasks_failed', 0)}")
                print(f"  成功: {stats.get('tasks_completed', 0)}")
                print(f"  失败: {stats.get('tasks_failed', 0)}")
                print(f"  成功率: {stats.get('success_rate', 0):.1%}")
                break

# 3. 检查是否有 spawn 记录
spawn_log = Path("data/spawn_requests.jsonl")
if spawn_log.exists():
    with open(spawn_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f.readlines() if 'Documentation_Writer' in l]
        if lines:
            print("\n" + "=" * 60)
            print(f"Spawn 请求记录（最近 {min(3, len(lines))} 条）")
            print("=" * 60)
            for line in lines[-3:]:
                record = json.loads(line)
                print(f"时间: {record.get('timestamp', 'N/A')}")
                print(f"任务: {record.get('task', 'N/A')[:100]}...")
                print(f"Agent: {record.get('agent_id', 'N/A')}")
                print()

print("\n" + "=" * 60)
print("结论")
print("=" * 60)
print("超时归属: 底层 coder agent 超时（60s）")
print("证据: result.agent = 'coder', error = 'Request timeout (60s)'")
print("说明: Documentation_Writer 调用了 coder agent，coder 在 60s 内未完成")
