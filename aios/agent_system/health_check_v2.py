#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 健康检查脚本 v2.0

Phase 1 迁移：完全基于新状态词表工作

变更：
1. 不再直接读取 agents.json 的 production_ready 字段
2. 通过 agent_status.py 的统一接口判断状态
3. 引入 no-sample 和 not-evaluable 的正确处理
4. 支持 Agent/Skill/Task/Lesson 四类对象
"""

import json
from pathlib import Path
from datetime import datetime
from agent_status import (
    ReadinessStatus,
    RunStatus,
    HealthStatus,
    validate_status_object,
    is_production_ready,
    is_healthy,
    needs_attention,
    get_status_summary
)
from state_vocabulary_adapter import get_agents_states

def load_agents_with_status_mapping(agents_file: Path) -> list:
    """
    读取 agents.json 并通过统一适配层推导状态
    
    Phase 2 迁移：使用 state_vocabulary_adapter 统一推导逻辑
    """
    with open(agents_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        agents = data.get('agents', [])
    
    # 使用统一适配层推导状态
    agents_with_states = get_agents_states(agents)
    
    # 映射到 health_check 需要的字段格式
    mapped_agents = []
    for agent in agents_with_states:
        mapped = agent.copy()
        state = agent.get('state', {})
        
        # 映射三维状态到旧字段名
        mapped['readiness_status'] = state.get('readiness', 'unknown')
        mapped['run_status'] = state.get('run', 'unknown')
        mapped['health_status'] = state.get('health', 'unknown')
        
        mapped_agents.append(mapped)
    
    return mapped_agents

def main():
    base_path = Path('C:/Users/A/.openclaw/workspace/aios/agent_system')

    # 读取 agents.json（带状态映射）
    agents_file = base_path / 'data' / 'agents.json'
    agents = load_agents_with_status_mapping(agents_file)

    # ========================================================================
    # 统计 Agent 状态（基于新词表）
    # ========================================================================
    total_agents = len(agents)
    enabled_agents = sum(1 for a in agents if a.get('enabled', False))
    
    # 使用新词表判断 production_ready
    production_ready_agents = [a for a in agents if is_production_ready(a)]
    production_ready_count = len(production_ready_agents)
    
    # 统计各 readiness_status 分布
    readiness_dist = {}
    for agent in agents:
        status = agent.get('readiness_status', 'unknown')
        readiness_dist[status] = readiness_dist.get(status, 0) + 1
    
    # 统计各 run_status 分布
    run_dist = {}
    for agent in agents:
        status = agent.get('run_status', 'unknown')
        run_dist[status] = run_dist.get(status, 0) + 1
    
    # 统计各 health_status 分布
    health_dist = {}
    for agent in agents:
        status = agent.get('health_status', 'unknown')
        health_dist[status] = health_dist.get(status, 0) + 1

    # ========================================================================
    # 统计任务执行情况
    # ========================================================================
    total_tasks = sum(a.get('stats', {}).get('tasks_total', 0) for a in agents)
    completed_tasks = sum(a.get('stats', {}).get('tasks_completed', 0) for a in agents)
    failed_tasks = sum(a.get('stats', {}).get('tasks_failed', 0) for a in agents)

    # 找出需要关注的 Agent（基于新词表）
    attention_agents = []
    for agent in agents:
        if needs_attention(agent):
            attention_agents.append({
                'name': agent.get('name'),
                'readiness': agent.get('readiness_status'),
                'run': agent.get('run_status'),
                'health': agent.get('health_status'),
                'reason': _get_attention_reason(agent)
            })

    # ========================================================================
    # 检查任务队列
    # ========================================================================
    queue_file = base_path / 'data' / 'task_queue.jsonl'
    pending_tasks = 0
    queued_tasks = 0
    if queue_file.exists():
        with open(queue_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    status = task.get('status', task.get('run_status', 'unknown'))
                    if status == 'pending':
                        pending_tasks += 1
                    elif status == 'queued':
                        queued_tasks += 1

    # ========================================================================
    # 检查 spawn_pending
    # ========================================================================
    spawn_file = base_path / 'data' / 'spawn_pending.jsonl'
    pending_spawns = 0
    if spawn_file.exists():
        with open(spawn_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    pending_spawns += 1

    # ========================================================================
    # 检查 Lesson 状态
    # ========================================================================
    lessons_file = base_path / 'data' / 'lessons.json'
    lesson_stats = {
        'total': 0,
        'pending': 0,
        'rule_derived': 0,
        'not_evaluable': 0
    }
    if lessons_file.exists():
        with open(lessons_file, 'r', encoding='utf-8') as f:
            lessons_data = json.load(f)
            lessons = lessons_data.get('lessons', [])
            lesson_stats['total'] = len(lessons)
            
            for lesson in lessons:
                # 支持旧字段 regeneration_status 和新字段 derivation_status
                status = lesson.get('derivation_status', lesson.get('regeneration_status', 'unknown'))
                if status == 'pending':
                    lesson_stats['pending'] += 1
                elif status == 'rule-derived':
                    lesson_stats['rule_derived'] += 1
                elif status == 'not-evaluable':
                    lesson_stats['not_evaluable'] += 1

    # ========================================================================
    # 计算健康分数（基于新词表）
    # ========================================================================
    score = 100

    # Agent 可用性（-10 if < 50% enabled）
    if total_agents > 0 and enabled_agents / total_agents < 0.5:
        score -= 10

    # 生产就绪度（-15 if < 3 production ready）
    if production_ready_count < 3:
        score -= 15

    # 任务成功率（-20 if < 70%）
    if total_tasks > 0:
        success_rate = completed_tasks / total_tasks
        if success_rate < 0.7:
            score -= 20

    # 需要关注的 Agent（-10 per agent, max -30）
    score -= min(len(attention_agents) * 10, 30)

    # 待处理任务积压（-15 if > 10）
    if pending_tasks + queued_tasks > 10:
        score -= 15

    # 待处理 spawn 积压（-10 if > 5）
    if pending_spawns > 5:
        score -= 10

    # Lesson 提炼率（-10 if < 30%）
    if lesson_stats['total'] > 0:
        derivation_rate = lesson_stats['rule_derived'] / lesson_stats['total']
        if derivation_rate < 0.3:
            score -= 10

    health_score = max(0, score)

    # ========================================================================
    # 输出报告
    # ========================================================================
    print('=== AIOS 健康检查报告 v2.0 ===')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'状态词表: v1.0')
    print()
    
    print('【系统概览】')
    print(f'  总 Agent 数: {total_agents}')
    print(f'  已启用: {enabled_agents}')
    print(f'  生产就绪: {production_ready_count}')
    print()
    
    print('【Agent 就绪状态分布】')
    for status, count in sorted(readiness_dist.items()):
        print(f'  {status}: {count}')
    print()
    
    print('【Agent 运行状态分布】')
    for status, count in sorted(run_dist.items()):
        marker = '⚠️' if status in ['failed', 'timeout', 'zombie'] else ''
        print(f'  {marker}{status}: {count}')
    print()
    
    print('【Agent 健康状态分布】')
    for status, count in sorted(health_dist.items()):
        marker = '⚠️' if status in ['warning', 'critical'] else ''
        print(f'  {marker}{status}: {count}')
    print()
    
    print('【任务执行】')
    print(f'  总任务数: {total_tasks}')
    print(f'  已完成: {completed_tasks}')
    print(f'  失败: {failed_tasks}')
    if total_tasks > 0:
        print(f'  成功率: {round(completed_tasks/total_tasks*100, 1)}%')
    print()
    
    print('【队列状态】')
    print(f'  待处理任务: {pending_tasks}')
    print(f'  排队中任务: {queued_tasks}')
    print(f'  待处理 spawn: {pending_spawns}')
    print()
    
    print('【Lesson 提炼状态】')
    print(f'  总 Lesson 数: {lesson_stats["total"]}')
    print(f'  待提炼: {lesson_stats["pending"]}')
    print(f'  已提炼规则: {lesson_stats["rule_derived"]}')
    print(f'  不可评估: {lesson_stats["not_evaluable"]}')
    if lesson_stats['total'] > 0:
        derivation_rate = lesson_stats['rule_derived'] / lesson_stats['total']
        print(f'  提炼率: {round(derivation_rate*100, 1)}%')
    print()
    
    if attention_agents:
        print('【需要关注的 Agent】')
        for agent in attention_agents:
            print(f'  ⚠️ {agent["name"]}')
            print(f'      状态: {agent["readiness"]} / {agent["run"]} / {agent["health"]}')
            print(f'      原因: {agent["reason"]}')
        print()
    
    print('【健康分数】')
    print(f'  分数: {health_score}/100')
    if health_score >= 80:
        status = '✅ 良好'
    elif health_score >= 60:
        status = '⚠️ 警告'
    else:
        status = '🚨 严重'
    print(f'  状态: {status}')
    print()
    
    if health_score < 60:
        print('【告警】健康分数低于 60，需要立即关注！')
        print()

    # ========================================================================
    # Self-Learning Status
    # ========================================================================
    selflearn_file = base_path / 'data' / 'selflearn-state.json'
    if selflearn_file.exists():
        try:
            with open(selflearn_file, 'r', encoding='utf-8') as f:
                selflearn = json.load(f)
            
            print('【Self-Learning Status】')
            print(f'  最近运行: {selflearn.get("last_run", "未知")}')
            print(f'  最近成功: {selflearn.get("last_success", "未知")}')
            print(f'  已激活学习 Agent: {len(selflearn.get("activated_agents", []))}')
            print(f'  待提炼 lesson: {selflearn.get("pending_lessons", 0)}')
            print(f'  已提炼规则: {selflearn.get("rules_derived_count", 0)}')
            
            activated = selflearn.get('activated_agents', [])
            if activated:
                print(f'  激活列表: {", ".join(activated)}')
            print()
        except Exception as e:
            print(f'【Self-Learning Status】读取失败: {e}')
            print()

    # ========================================================================
    # 生产就绪 Agent 列表
    # ========================================================================
    if production_ready_agents:
        print('【生产就绪 Agent】')
        for agent in production_ready_agents:
            name = agent.get('name')
            run = agent.get('run_status')
            health = agent.get('health_status')
            stats = agent.get('stats', {})
            completed = stats.get('tasks_completed', 0)
            
            # 根据 run_status 调整显示
            if run == RunStatus.NO_SAMPLE.value:
                status_text = f'{run} / {health} (已验证，未运行)'
            else:
                status_text = f'{run} / {health} (完成 {completed} 个任务)'
            
            print(f'  ✅ {name} — {status_text}')
        print()

    return health_score

def _get_attention_reason(agent: dict) -> str:
    """生成需要关注的原因"""
    reasons = []
    
    health = agent.get('health_status')
    if health == HealthStatus.CRITICAL.value:
        reasons.append('健康度严重')
    elif health == HealthStatus.WARNING.value:
        reasons.append('健康度警告')
    
    run = agent.get('run_status')
    if run == RunStatus.FAILED.value:
        reasons.append('最近执行失败')
    elif run == RunStatus.TIMEOUT.value:
        reasons.append('最近执行超时')
    elif run == RunStatus.ZOMBIE.value:
        reasons.append('僵尸任务')
    
    return ', '.join(reasons) if reasons else '未知'

if __name__ == '__main__':
    score = main()
    exit(0 if score >= 60 else 1)
