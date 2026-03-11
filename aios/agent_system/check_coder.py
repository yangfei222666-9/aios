#!/usr/bin/env python3
"""检查 coder agent 配置和最近执行情况"""

import json
from pathlib import Path

# 1. 找 coder agent 配置
agents_file = Path("data/agents.json")
if agents_file.exists():
    with open(agents_file, 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
        agents = agents_data if isinstance(agents_data, list) else agents_data.get('agents', [])
        
        print("=" * 60)
        print("Coder Agent 配置")
        print("=" * 60)
        
        for agent in agents:
            if 'coder' in agent.get('id', '').lower():
                print(f"\nAgent ID: {agent['id']}")
                
                config = agent.get('config', {})
                print(f"超时设置: {config.get('timeout', 'N/A')}s")
                print(f"模型: {config.get('model', 'N/A')}")
                print(f"Thinking: {config.get('thinking', 'N/A')}")
                
                prompt = config.get('prompt', '')
                print(f"Prompt 长度: {len(prompt)} 字符")
                
                stats = agent.get('stats', {})
                print(f"统计:")
                print(f"  总任务: {stats.get('tasks_completed', 0) + stats.get('tasks_failed', 0)}")
                print(f"  成功: {stats.get('tasks_completed', 0)}")
                print(f"  失败: {stats.get('tasks_failed', 0)}")
                print(f"  成功率: {stats.get('success_rate', 0):.1%}")
                print(f"  平均耗时: {stats.get('avg_duration', 0):.1f}s")

# 2. 检查最近的 coder 执行记录
task_exec = Path("data/task_executions.jsonl")
if task_exec.exists():
    with open(task_exec, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    coder_tasks = []
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if 'coder' in record.get('agent_id', '').lower():
                coder_tasks.append(record)
        except:
            continue
    
    if coder_tasks:
        print("\n" + "=" * 60)
        print(f"Coder 最近执行记录（最近 5 条）")
        print("=" * 60)
        
        for task in coder_tasks[-5:]:
            print(f"\nTask ID: {task.get('task_id', 'N/A')}")
            print(f"状态: {task.get('status', 'N/A')}")
            print(f"耗时: {task.get('duration_ms', 0) / 1000:.1f}s")
            
            result = task.get('result', {})
            if 'error' in result:
                print(f"错误: {result['error']}")

# 3. 检查 coder-dispatcher 统计
print("\n" + "=" * 60)
print("Coder-Dispatcher 统计")
print("=" * 60)

for agent in agents:
    if agent.get('id') == 'coder-dispatcher':
        stats = agent.get('stats', {})
        print(f"总任务: {stats.get('tasks_completed', 0) + stats.get('tasks_failed', 0)}")
        print(f"成功: {stats.get('tasks_completed', 0)}")
        print(f"失败: {stats.get('tasks_failed', 0)}")
        print(f"成功率: {stats.get('success_rate', 0):.1%}")
        print(f"平均耗时: {stats.get('avg_duration', 0):.1f}s")
        break
