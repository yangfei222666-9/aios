#!/usr/bin/env python3
"""太极OS 自我检查工具"""

import json
from pathlib import Path
from datetime import datetime

def main():
    print('=== 太极OS 自我检查 ===\n')

    # 1. 检查核心文件
    print('📁 核心文件状态:')
    core_files = {
        'agents.json': 'Agent 注册表',
        'task_queue.jsonl': '任务队列',
        'spawn_pending.jsonl': 'Spawn 待处理',
        'lessons.json': '经验教训',
        'memory/selflearn-state.json': '学习状态'
    }

    for file, desc in core_files.items():
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print(f'  ✓ {desc}: {size} bytes')
        else:
            print(f'  ✗ {desc}: 不存在')

    # 2. 检查任务队列
    print('\n📋 任务队列:')
    queue_path = Path('task_queue.jsonl')
    if queue_path.exists():
        content = queue_path.read_text(encoding='utf-8').strip()
        if content:
            tasks = [json.loads(line) for line in content.split('\n') if line]
            pending = [t for t in tasks if t.get('status') == 'pending']
            completed = [t for t in tasks if t.get('status') == 'completed']
            failed = [t for t in tasks if t.get('status') == 'failed']
            print(f'  待处理: {len(pending)}')
            print(f'  已完成: {len(completed)}')
            print(f'  失败: {len(failed)}')
        else:
            print('  ✓ 队列为空')
    else:
        print('  队列文件不存在')

    # 3. 检查 spawn_pending
    print('\n🚀 Spawn 待处理:')
    spawn_path = Path('spawn_pending.jsonl')
    if spawn_path.exists():
        content = spawn_path.read_text(encoding='utf-8').strip()
        if content:
            spawns = [json.loads(line) for line in content.split('\n') if line]
            print(f'  待处理: {len(spawns)} 个')
            for s in spawns[:3]:
                agent_id = s.get('agentId', 'unknown')
                task = s.get('task', 'no task')[:50]
                print(f'    - {agent_id}: {task}...')
        else:
            print('  ✓ 无待处理 spawn')
    else:
        print('  文件不存在')

    # 4. 检查 Agent 状态
    print('\n🤖 Agent 状态:')
    agents_path = Path('agents.json')
    if agents_path.exists():
        agents = json.load(agents_path.open(encoding='utf-8'))
        print(f'  注册 Agent: {len(agents)} 个')
        for name, info in list(agents.items())[:5]:
            stats = info.get('stats', {})
            completed = stats.get('tasks_completed', 0)
            failed = stats.get('tasks_failed', 0)
            print(f'    {name}: 成功={completed} 失败={failed}')
    else:
        print('  agents.json 不存在')

    # 5. 检查学习状态
    print('\n🧠 学习状态:')
    state_path = Path('memory/selflearn-state.json')
    if state_path.exists():
        state = json.load(state_path.open(encoding='utf-8'))
        print(f'  Evolution Score: {state.get("evolution_score", 0)}')
        print(f'  总事件: {state.get("total_events", 0)}')
        print(f'  最后更新: {state.get("last_update", "unknown")}')
    else:
        print('  学习状态文件不存在')

    # 6. 检查最近错误
    print('\n⚠️ 最近错误:')
    lessons_path = Path('lessons.json')
    if lessons_path.exists():
        lessons = json.load(lessons_path.open(encoding='utf-8'))
        recent_errors = [l for l in lessons.get('lessons', []) if l.get('type') == 'error'][-3:]
        if recent_errors:
            for err in recent_errors:
                ts = err.get('timestamp', 'unknown')
                desc = err.get('description', 'no desc')[:60]
                print(f'  - {ts}: {desc}...')
        else:
            print('  ✓ 无最近错误')
    else:
        print('  lessons.json 不存在')

    print('\n=== 检查完成 ===')

if __name__ == '__main__':
    main()
