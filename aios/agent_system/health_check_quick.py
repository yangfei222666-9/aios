#!/usr/bin/env python3
"""AIOS 快速健康检查"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

def main():
    base_dir = Path(__file__).parent
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'health_score': 0,
        'status': 'UNKNOWN',
        'metrics': {},
        'agents': {},
        'errors': [],
        'alerts': []
    }
    
    # 1. 检查核心文件
    state_file = base_dir / 'memory' / 'selflearn-state.json'
    agents_file = base_dir / 'agents.json'
    events_file = base_dir / 'events.jsonl'
    lessons_file = base_dir / 'memory' / 'lessons.json'
    
    if not state_file.exists():
        result['errors'].append('selflearn-state.json missing')
    if not agents_file.exists():
        result['errors'].append('agents.json missing')
    
    # 2. 读取 Agent 状态
    if agents_file.exists():
        try:
            with open(agents_file, 'r', encoding='utf-8') as f:
                agents_data = json.load(f)
                agents = agents_data.get('agents', [])
                result['agents']['total'] = len(agents)
                # 修正：只统计 mode=active 且 enabled=true 的 routable agent
                result['agents']['active'] = sum(
                    1 for a in agents 
                    if a.get('mode') == 'active' and a.get('enabled') is True
                )
                result['agents']['shadow'] = sum(
                    1 for a in agents if a.get('mode') == 'shadow'
                )
                result['agents']['disabled'] = sum(
                    1 for a in agents if a.get('mode') == 'disabled'
                )
        except Exception as e:
            result['errors'].append(f'Failed to read agents.json: {e}')
    
    # 3. 统计事件
    if events_file.exists():
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                events = [json.loads(line) for line in f if line.strip()]
                result['metrics']['total_events'] = len(events)
                
                # 最近24小时的事件
                now = datetime.now()
                recent = [
                    e for e in events 
                    if datetime.fromisoformat(e.get('timestamp', '2000-01-01')) > now - timedelta(hours=24)
                ]
                result['metrics']['events_24h'] = len(recent)
                
                # 错误率
                errors = [e for e in recent if e.get('type') == 'error']
                result['metrics']['errors_24h'] = len(errors)
                result['metrics']['error_rate'] = round(
                    len(errors) / len(recent) * 100, 2
                ) if recent else 0
        except Exception as e:
            result['errors'].append(f'Failed to read events.jsonl: {e}')
    
    # 4. 读取经验教训
    if lessons_file.exists():
        try:
            with open(lessons_file, 'r', encoding='utf-8') as f:
                lessons = json.load(f)
                result['metrics']['total_lessons'] = len(lessons.get('lessons', []))
                result['metrics']['rules_derived'] = len(lessons.get('rules_derived', []))
        except Exception as e:
            result['errors'].append(f'Failed to read lessons.json: {e}')
    
    # 5. 计算健康分数
    score = 100
    if result['errors']:
        score -= len(result['errors']) * 20
    if result['metrics'].get('error_rate', 0) > 10:
        score -= 20
    if result['metrics'].get('error_rate', 0) > 30:
        score -= 30
    # 修正：只有 routable agent (mode=active + enabled=true) 为 0 才扣分
    if result['agents'].get('active', 0) == 0:
        score -= 30
    
    result['health_score'] = max(0, score)
    
    # 6. 判断状态
    if result['health_score'] >= 80:
        result['status'] = 'GOOD'
    elif result['health_score'] >= 60:
        result['status'] = 'WARNING'
    else:
        result['status'] = 'CRITICAL'
    
    # 7. 生成告警
    if result['health_score'] < 60:
        result['alerts'].append(f'Health score below threshold: {result["health_score"]}/100')
    if result['metrics'].get('error_rate', 0) > 30:
        result['alerts'].append(f'High error rate: {result["metrics"]["error_rate"]}%')
    # 修正：只有 routable agent 为 0 才告警
    if result['agents'].get('active', 0) == 0:
        result['alerts'].append('No active routable agents')
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
