#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIOS Health Check - Quick Metrics"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def calculate_health():
    base_dir = Path(__file__).parent
    
    # 1. Task Execution Stats
    exec_file = base_dir / "task_executions_v2.jsonl"
    if exec_file.exists() and exec_file.stat().st_size > 0:
        lines = exec_file.read_text(encoding='utf-8').strip().split('\n')
        execs = [json.loads(line) for line in lines if line.strip()]
        
        # 7-day window
        now = datetime.now()
        recent = []
        for e in execs:
            try:
                ts = datetime.fromisoformat(e.get('timestamp', '2020-01-01'))
                if (now - ts).days < 7:
                    recent.append(e)
            except:
                pass
        
        success = [e for e in recent if e.get('result', {}).get('success')]
        failed = [e for e in recent if not e.get('result', {}).get('success')]
        
        success_rate = (len(success) / len(recent) * 100) if recent else 0
        
        print(f"7-Day Success Rate: {success_rate:.1f}%")
        print(f"Recent Executions: {len(recent)}")
        print(f"Failed (7d): {len(failed)}")
    else:
        print("7-Day Success Rate: N/A")
        print("Recent Executions: 0")
        print("Failed (7d): 0")
        success_rate = 0
    
    # 2. Agent Stats
    agents_file = base_dir / "agents.json"
    if agents_file.exists():
        data = json.loads(agents_file.read_text(encoding='utf-8'))
        agents = data.get('agents', [])
        
        active = [a for a in agents if a.get('enabled', True) and a.get('mode') == 'active']
        shadow = [a for a in agents if a.get('enabled', True) and a.get('mode') == 'shadow']
        disabled = [a for a in agents if not a.get('enabled', True)]
        
        print(f"Total Agents: {len(agents)}")
        print(f"Active: {len(active)}")
        print(f"Shadow: {len(shadow)}")
        print(f"Disabled: {len(disabled)}")
    else:
        print("Total Agents: 0")
        print("Active: 0")
        print("Shadow: 0")
        print("Disabled: 0")
    
    # 3. Task Queue
    queue_file = base_dir / "task_queue.jsonl"
    if queue_file.exists() and queue_file.stat().st_size > 0:
        lines = queue_file.read_text(encoding='utf-8').strip().split('\n')
        tasks = [json.loads(line) for line in lines if line.strip()]
        
        pending = [t for t in tasks if t.get('status') == 'pending']
        completed = [t for t in tasks if t.get('status') == 'completed']
        failed = [t for t in tasks if t.get('status') == 'failed']
        
        print(f"Queue Pending: {len(pending)}")
        print(f"Queue Completed: {len(completed)}")
        print(f"Queue Failed: {len(failed)}")
    else:
        print("Queue Pending: 0")
        print("Queue Completed: 0")
        print("Queue Failed: 0")
    
    # 4. Lessons (Real Failures)
    lessons_file = base_dir / "lessons.json"
    if lessons_file.exists():
        data = json.loads(lessons_file.read_text(encoding='utf-8'))
        if isinstance(data, list):
            lessons = data
        else:
            lessons = data.get('lessons', [])
        
        real = [l for l in lessons if l.get('source') == 'real']
        print(f"Total Lessons: {len(lessons)}")
        print(f"Real Failures: {len(real)}")
    else:
        print("Total Lessons: 0")
        print("Real Failures: 0")
    
    # 5. Health Score
    health_score = success_rate
    print(f"Health Score: {health_score:.1f}/100")
    
    if health_score >= 80:
        status = "GOOD"
    elif health_score >= 60:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    print(f"Status: {status}")
    
    return health_score, status

if __name__ == '__main__':
    calculate_health()

