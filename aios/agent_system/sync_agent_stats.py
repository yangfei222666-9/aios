#!/usr/bin/env python3
"""
Agent 缁熻鍚屾宸ュ叿 - 浠?task_executions_v2.jsonl 鍚屾鐪熷疄鏁版嵁鍒?agents.json
"""
import json
from pathlib import Path
from collections import defaultdict
from paths import AGENTS_STATE, TASK_EXECUTIONS

AGENTS_FILE = AGENTS_STATE
EXECUTIONS_FILE = TASK_EXECUTIONS

def sync_agent_stats():
    """鍚屾 Agent 缁熻鏁版嵁"""
    # 1. 璇诲彇鐪熷疄鎵ц璁板綍
    agent_stats = defaultdict(lambda: {
        'tasks_completed': 0,
        'tasks_failed': 0,
        'tasks_total': 0,
        'total_duration': 0.0
    })
    
    if EXECUTIONS_FILE.exists():
        with open(EXECUTIONS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    # 鏂版牸寮忥細agent_id, status
                    agent = record.get('agent_id', 'unknown')
                    status = record.get('status', 'unknown')
                    
                    agent_stats[agent]['tasks_total'] += 1
                    if status == 'completed':
                        agent_stats[agent]['tasks_completed'] += 1
                    elif status == 'failed':
                        agent_stats[agent]['tasks_failed'] += 1
                    
                    # 鏂版牸寮忥細duration_ms锛堟绉掞級
                    duration_ms = record.get('duration_ms', 0)
                    agent_stats[agent]['total_duration'] += duration_ms / 1000.0  # 杞崲涓虹
                except:
                    continue
    
    # 2. 鏇存柊 agents.json
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated = 0
    for agent in data['agents']:
        agent_id = agent.get('id') or agent.get('name')
        
        # 灏濊瘯鍖归厤缁熻鏁版嵁
        stats = None
        if agent_id in agent_stats:
            stats = agent_stats[agent_id]
        elif agent_id and '-dispatcher' in agent_id:
            # coder-dispatcher -> coder
            base_name = agent_id.replace('-dispatcher', '')
            if base_name in agent_stats:
                stats = agent_stats[base_name]
        
        if stats and stats['tasks_total'] > 0:
            agent['stats'] = {
                'tasks_completed': stats['tasks_completed'],
                'tasks_failed': stats['tasks_failed'],
                'tasks_total': stats['tasks_total'],
                'success_rate': round(stats['tasks_completed'] / stats['tasks_total'] * 100, 1),
                'avg_duration': round(stats['total_duration'] / stats['tasks_total'], 1)
            }
            updated += 1
            print(f"[SYNC] {agent_id}: {stats['tasks_completed']}/{stats['tasks_total']} tasks")
    
    # 3. 淇濆瓨鏇存柊
    with open(AGENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Synced {updated} agents")
    return updated

if __name__ == '__main__':
    sync_agent_stats()

