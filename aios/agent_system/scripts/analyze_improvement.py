#!/usr/bin/env python3
"""
太极OS 自我改进分析脚本
分析当前系统状态，识别改进点，生成改进计划
"""

import json
from datetime import datetime
from pathlib import Path

def analyze_system():
    """分析系统状态并生成改进计划"""
    
    base_dir = Path(__file__).parent.parent
    
    # 读取当前状态
    with open(base_dir / 'data/agents.json', 'r', encoding='utf-8') as f:
        agents_data = json.load(f)
    
    with open(base_dir / 'memory/selflearn-state.json', 'r', encoding='utf-8') as f:
        selflearn_state = json.load(f)
    
    with open(base_dir / 'data/lessons.json', 'r', encoding='utf-8') as f:
        lessons_data = json.load(f)
    
    # 分析改进点
    print('=== 太极OS 自我改进分析 ===\n')
    
    # 1. Agent 状态分析
    agents = agents_data['agents']
    total = len(agents)
    routable = sum(1 for a in agents if a.get('routable', False))
    validated = sum(1 for a in agents if a.get('validation_status') == 'validated')
    production_ready = sum(1 for a in agents if a.get('production_ready', False))
    
    print(f'1. Agent 体系健康度')
    print(f'   总数: {total}')
    print(f'   可路由: {routable} ({routable/total*100:.1f}%)')
    print(f'   已验证: {validated} ({validated/total*100:.1f}%)')
    print(f'   生产就绪: {production_ready} ({production_ready/total*100:.1f}%)')
    print()
    
    # 2. 学习系统状态
    print(f'2. 学习系统状态')
    print(f'   状态: {selflearn_state["learning_loop_status"]}')
    print(f'   活跃学习Agent: {selflearn_state["active_learning_agents_count"]}')
    print(f'   已验证学习Agent: {selflearn_state["validated_learning_agents_count"]}')
    print(f'   待处理lessons: {selflearn_state["pending_lessons_count"]}')
    print(f'   已生成规则: {selflearn_state["rules_derived_count"]}')
    print()
    
    # 3. Lessons 分析
    lessons = lessons_data['lessons']
    pending_lessons = [l for l in lessons if l.get('regeneration_status') == 'pending']
    policy_lessons = [l for l in lessons if l.get('lesson_type', '').startswith('dispatch_')]
    
    print(f'3. Lessons 状态')
    print(f'   总数: {len(lessons)}')
    print(f'   待处理: {len(pending_lessons)}')
    print(f'   策略类: {len(policy_lessons)}')
    print()
    
    # 4. 识别改进点
    print('=== 识别的改进点 ===\n')
    
    improvements = []
    
    # 改进点1: 提升 Agent 验证率
    if validated < routable * 0.5:
        improvements.append({
            'priority': 'P1',
            'area': 'Agent治理',
            'issue': f'已验证Agent比例过低 ({validated}/{routable})',
            'action': '为未验证的可路由Agent补充验证流程',
            'impact': '提升系统可信度'
        })
    
    # 改进点2: 学习系统闭环
    if selflearn_state['validated_learning_agents_count'] == 0:
        improvements.append({
            'priority': 'P0',
            'area': '学习系统',
            'issue': '无已验证的学习Agent',
            'action': '完成至少3个学习Agent的验证',
            'impact': '建立真实学习闭环'
        })
    
    # 改进点3: Lessons 提炼
    if len(pending_lessons) > 0:
        improvements.append({
            'priority': 'P1',
            'area': 'Lessons系统',
            'issue': f'{len(pending_lessons)}条lessons待提炼',
            'action': '从pending lessons中提炼可复用规则',
            'impact': '将失败经验转化为系统能力'
        })
    
    # 改进点4: 策略规则应用
    if len(policy_lessons) > 0 and selflearn_state['rules_by_status']['applied'] == 0:
        improvements.append({
            'priority': 'P1',
            'area': '策略系统',
            'issue': f'{len(policy_lessons)}条策略lessons未应用',
            'action': '验证并应用策略改进规则',
            'impact': '优化任务路由和降级策略'
        })
    
    # 输出改进计划
    for i, imp in enumerate(improvements, 1):
        print(f'{i}. [{imp["priority"]}] {imp["area"]}')
        print(f'   问题: {imp["issue"]}')
        print(f'   行动: {imp["action"]}')
        print(f'   影响: {imp["impact"]}')
        print()
    
    # 生成改进计划
    improvement_plan = {
        'generated_at': datetime.now().isoformat(),
        'analysis_summary': {
            'total_agents': total,
            'routable_agents': routable,
            'validated_agents': validated,
            'learning_loop_status': selflearn_state['learning_loop_status'],
            'pending_lessons': len(pending_lessons),
            'policy_lessons': len(policy_lessons)
        },
        'improvements': improvements,
        'next_actions': [
            '1. 执行 Error_Analyzer 验证（已有执行脚本）',
            '2. 为 Bug_Hunter 补充执行脚本并验证',
            '3. 从 pending lessons 中提炼1条规则',
            '4. 验证并应用1条策略改进规则'
        ]
    }
    
    output_path = base_dir / 'data/self_improvement_plan.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(improvement_plan, f, indent=2, ensure_ascii=False)
    
    print(f'改进计划已生成: {output_path}')
    
    return improvement_plan

if __name__ == '__main__':
    analyze_system()
