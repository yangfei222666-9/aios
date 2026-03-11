#!/usr/bin/env python3
"""
Bug_Hunter Agent 执行脚本
主动发现和修复 Bug，提升系统稳定性
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def run_bug_hunter():
    """执行 Bug Hunter 任务"""
    
    base_dir = Path(__file__).parent.parent
    
    print("=== Bug_Hunter Agent 执行 ===\n")
    
    # 1. 扫描错误日志
    print("1. 扫描错误日志...")
    error_log_path = base_dir / 'logs/dispatcher.log'
    
    bugs_found = []
    
    if error_log_path.exists():
        with open(error_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-100:]:  # 检查最近100行
                if 'ERROR' in line or 'Exception' in line:
                    bugs_found.append({
                        'source': 'dispatcher.log',
                        'line': line.strip(),
                        'severity': 'high' if 'Exception' in line else 'medium'
                    })
    
    # 2. 检查数据一致性
    print("2. 检查数据一致性...")
    
    # 检查 agents.json
    agents_path = base_dir / 'data/agents.json'
    if agents_path.exists():
        with open(agents_path, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
            
        # 检查 routable 但没有 timeout 的 Agent
        for agent in agents_data['agents']:
            if agent.get('routable') and not agent.get('timeout'):
                bugs_found.append({
                    'source': 'agents.json',
                    'issue': f"Agent {agent['name']} is routable but has no timeout",
                    'severity': 'low',
                    'fix': 'Add default timeout: 60'
                })
    
    # 3. 检查队列状态
    print("3. 检查队列状态...")
    
    queue_path = base_dir / 'data/task_queue.jsonl'
    if queue_path.exists():
        with open(queue_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 检查僵尸任务
        for line in lines:
            try:
                task = json.loads(line)
                if task.get('status') == 'queued':
                    created_at = task.get('created_at', '')
                    # 简单检查：如果任务描述中包含 zombie，标记为潜在问题
                    if 'zombie' in task.get('description', '').lower():
                        bugs_found.append({
                            'source': 'task_queue.jsonl',
                            'issue': f"Potential zombie task: {task.get('task_id')}",
                            'severity': 'medium',
                            'fix': 'Review task status and retry mechanism'
                        })
            except json.JSONDecodeError:
                pass
    
    # 4. 生成报告
    print("\n=== Bug Hunter 报告 ===\n")
    
    if not bugs_found:
        print("✓ 未发现明显Bug")
        result = {
            'success': True,
            'bugs_found': 0,
            'message': '系统状态良好，未发现明显Bug'
        }
    else:
        print(f"发现 {len(bugs_found)} 个潜在问题:\n")
        
        for i, bug in enumerate(bugs_found, 1):
            print(f"{i}. [{bug['severity'].upper()}] {bug.get('source', 'unknown')}")
            if 'issue' in bug:
                print(f"   问题: {bug['issue']}")
            if 'line' in bug:
                print(f"   日志: {bug['line'][:100]}...")
            if 'fix' in bug:
                print(f"   建议: {bug['fix']}")
            print()
        
        result = {
            'success': True,
            'bugs_found': len(bugs_found),
            'bugs': bugs_found,
            'message': f'发现 {len(bugs_found)} 个潜在问题'
        }
    
    # 5. 记录执行结果
    execution_record = {
        'agent_id': 'Bug_Hunter',
        'executed_at': datetime.now().isoformat(),
        'result': result
    }
    
    record_path = base_dir / 'data/agent_execution_record.jsonl'
    with open(record_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(execution_record, ensure_ascii=False) + '\n')
    
    print(f"\n执行记录已写入: {record_path}")
    
    return result

if __name__ == '__main__':
    try:
        result = run_bug_hunter()
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)
