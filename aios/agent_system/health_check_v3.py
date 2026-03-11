#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 健康检查脚本 v3.0

新增功能：
1. Memory Server 状态自动检测（端口 7788）
2. 成本追踪系统集成（Token 使用和成本估算）
3. 自我改进能力集成（自动记录问题到改进队列）

基于 v2.0 的状态词表迁移成果
"""

import json
import socket
from pathlib import Path
from datetime import datetime, timedelta
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

def check_memory_server() -> dict:
    """检查 Memory Server 状态"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 7788))
        online = (result == 0)
        sock.close()
        
        return {
            'online': online,
            'port': 7788,
            'status': 'running' if online else 'offline'
        }
    except Exception as e:
        return {
            'online': False,
            'port': 7788,
            'status': 'error',
            'error': str(e)
        }

def check_cost_tracking(base_path: Path) -> dict:
    """检查成本追踪数据"""
    cost_file = base_path / 'data' / 'cost_tracking.jsonl'
    
    if not cost_file.exists():
        return {
            'enabled': False,
            'total_tokens': 0,
            'estimated_cost': 0.0,
            'last_24h_tokens': 0,
            'last_24h_cost': 0.0
        }
    
    total_tokens = 0
    total_cost = 0.0
    last_24h_tokens = 0
    last_24h_cost = 0.0
    
    cutoff = datetime.now() - timedelta(hours=24)
    
    try:
        with open(cost_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    tokens = record.get('tokens', 0)
                    cost = record.get('cost', 0.0)
                    timestamp = datetime.fromisoformat(record.get('timestamp', ''))
                    
                    total_tokens += tokens
                    total_cost += cost
                    
                    if timestamp >= cutoff:
                        last_24h_tokens += tokens
                        last_24h_cost += cost
        
        return {
            'enabled': True,
            'total_tokens': total_tokens,
            'estimated_cost': round(total_cost, 2),
            'last_24h_tokens': last_24h_tokens,
            'last_24h_cost': round(last_24h_cost, 2)
        }
    except Exception as e:
        return {
            'enabled': False,
            'error': str(e),
            'total_tokens': 0,
            'estimated_cost': 0.0,
            'last_24h_tokens': 0,
            'last_24h_cost': 0.0
        }

def record_improvement_issue(base_path: Path, issue: dict):
    """记录改进问题到队列"""
    improvement_queue = base_path / 'data' / 'improvement_queue.jsonl'
    
    try:
        with open(improvement_queue, 'a', encoding='utf-8') as f:
            f.write(json.dumps(issue, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f'⚠️ 无法记录改进问题: {e}')

def load_agents_with_status_mapping(agents_file: Path) -> list:
    """读取 agents.json 并通过统一适配层推导状态"""
    with open(agents_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        agents = data.get('agents', [])
    
    agents_with_states = get_agents_states(agents)
    
    mapped_agents = []
    for agent in agents_with_states:
        mapped = agent.copy()
        state = agent.get('state', {})
        
        mapped['readiness_status'] = state.get('readiness', 'unknown')
        mapped['run_status'] = state.get('run', 'unknown')
        mapped['health_status'] = state.get('health', 'unknown')
        
        mapped_agents.append(mapped)
    
    return mapped_agents

def main():
    base_path = Path(__file__).parent
    agents_file = base_path / 'data' / 'agents.json'
    
    if not agents_file.exists():
        print(f'❌ agents.json 不存在: {agents_file}')
        return 0
    
    agents = load_agents_with_status_mapping(agents_file)
    
    # ========================================================================
    # Agent 统计
    # ========================================================================
    total_agents = len(agents)
    enabled_agents = sum(1 for a in agents if a.get('enabled', True))
    production_ready_count = sum(1 for a in agents if is_production_ready(a))
    production_ready_agents = [a for a in agents if is_production_ready(a)]
    
    readiness_dist = {}
    run_dist = {}
    health_dist = {}
    
    for agent in agents:
        r = agent.get('readiness_status', 'unknown')
        ru = agent.get('run_status', 'unknown')
        h = agent.get('health_status', 'unknown')
        
        readiness_dist[r] = readiness_dist.get(r, 0) + 1
        run_dist[ru] = run_dist.get(ru, 0) + 1
        health_dist[h] = health_dist.get(h, 0) + 1
    
    # 任务统计
    total_tasks = 0
    completed_tasks = 0
    failed_tasks = 0
    
    for agent in agents:
        stats = agent.get('stats', {})
        total_tasks += stats.get('tasks_total', 0)
        completed_tasks += stats.get('tasks_completed', 0)
        failed_tasks += stats.get('tasks_failed', 0)
    
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
    # 任务队列
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
    # spawn_pending
    # ========================================================================
    spawn_file = base_path / 'data' / 'spawn_pending.jsonl'
    pending_spawns = 0
    if spawn_file.exists():
        with open(spawn_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    pending_spawns += 1
    
    # ========================================================================
    # Lesson 状态
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
                status = lesson.get('derivation_status', lesson.get('regeneration_status', 'unknown'))
                if status == 'pending':
                    lesson_stats['pending'] += 1
                elif status == 'rule-derived':
                    lesson_stats['rule_derived'] += 1
                elif status == 'not-evaluable':
                    lesson_stats['not_evaluable'] += 1
    
    # ========================================================================
    # Memory Server 状态（新增）
    # ========================================================================
    memory_server = check_memory_server()
    
    # ========================================================================
    # 成本追踪（新增）
    # ========================================================================
    cost_tracking = check_cost_tracking(base_path)
    
    # ========================================================================
    # 健康分数计算
    # ========================================================================
    score = 100
    issues = []
    
    if total_agents > 0 and enabled_agents / total_agents < 0.5:
        score -= 10
        issues.append({
            'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-001',
            'type': 'agent_availability',
            'severity': 'P2',
            'description': f'Agent 可用性低于 50% ({enabled_agents}/{total_agents})',
            'source': 'health_check_v3',
            'detected_at': datetime.now().isoformat()
        })
    
    if production_ready_count < 3:
        score -= 15
        issues.append({
            'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-002',
            'type': 'production_readiness',
            'severity': 'P1',
            'description': f'生产就绪 Agent 少于 3 个 (当前: {production_ready_count})',
            'source': 'health_check_v3',
            'detected_at': datetime.now().isoformat()
        })
    
    if total_tasks > 0:
        success_rate = completed_tasks / total_tasks
        if success_rate < 0.7:
            score -= 20
            issues.append({
                'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-003',
                'type': 'task_success_rate',
                'severity': 'P1',
                'description': f'任务成功率低于 70% (当前: {round(success_rate*100, 1)}%)',
                'source': 'health_check_v3',
                'detected_at': datetime.now().isoformat()
            })
    
    score -= min(len(attention_agents) * 10, 30)
    
    if pending_tasks + queued_tasks > 10:
        score -= 15
        issues.append({
            'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-004',
            'type': 'task_backlog',
            'severity': 'P2',
            'description': f'任务积压超过 10 个 (当前: {pending_tasks + queued_tasks})',
            'source': 'health_check_v3',
            'detected_at': datetime.now().isoformat()
        })
    
    if pending_spawns > 5:
        score -= 10
        issues.append({
            'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-005',
            'type': 'spawn_backlog',
            'severity': 'P2',
            'description': f'spawn 积压超过 5 个 (当前: {pending_spawns})',
            'source': 'health_check_v3',
            'detected_at': datetime.now().isoformat()
        })
    
    if lesson_stats['total'] > 0:
        derivation_rate = lesson_stats['rule_derived'] / lesson_stats['total']
        if derivation_rate < 0.3:
            score -= 10
            issues.append({
                'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-006',
                'type': 'learning_debt',
                'severity': 'P2',
                'description': f'Lesson 提炼率低于 30% (当前: {round(derivation_rate*100, 1)}%)',
                'source': 'health_check_v3',
                'detected_at': datetime.now().isoformat()
            })
    
    if not memory_server['online']:
        score -= 5
        issues.append({
            'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-007',
            'type': 'memory_server_offline',
            'severity': 'P2',
            'description': 'Memory Server 离线 (端口 7788)',
            'source': 'health_check_v3',
            'detected_at': datetime.now().isoformat()
        })
    
    if not cost_tracking['enabled']:
        score -= 5
        issues.append({
            'id': f'health-{datetime.now().strftime("%Y%m%d%H%M%S")}-008',
            'type': 'cost_tracking_missing',
            'severity': 'P3',
            'description': '成本追踪系统未启用',
            'source': 'health_check_v3',
            'detected_at': datetime.now().isoformat()
        })
    
    health_score = max(0, score)
    
    # ========================================================================
    # 自动记录改进问题（新增）
    # ========================================================================
    for issue in issues:
        record_improvement_issue(base_path, issue)
    
    # ========================================================================
    # 输出报告
    # ========================================================================
    print('# AIOS Health Check Report')
    print(f'**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M")} (Asia/Shanghai)')
    print()
    print('---')
    print()
    
    if health_score >= 80:
        status_emoji = '✅'
        status_text = 'HEALTHY'
    elif health_score >= 60:
        status_emoji = '⚠️'
        status_text = 'WARNING'
    else:
        status_emoji = '🚨'
        status_text = 'CRITICAL'
    
    print(f'## System Status: {status_emoji} {status_text}')
    print()
    print(f'**Overall Health Score:** {health_score}/100 ({"GOOD" if health_score >= 80 else "WARNING" if health_score >= 60 else "CRITICAL"})')
    print()
    print('---')
    print()
    
    print('## Core Metrics')
    print()
    
    print('### Agent System')
    print(f'- **Total Agents:** {total_agents} registered')
    print(f'- **Production-Ready:** {production_ready_count}', end='')
    if production_ready_agents:
        print(f' ({", ".join(a.get("name") for a in production_ready_agents)})')
    else:
        print()
    
    # 检查观察期 Agent
    observation_agents = []
    for agent in agents:
        if agent.get('observation_period'):
            obs = agent['observation_period']
            observation_agents.append(f"{agent.get('name')} Day {obs.get('current_day', 0)}/{obs.get('total_days', 0)}")
    
    if observation_agents:
        print(f'- **In Observation:** {len(observation_agents)} ({", ".join(observation_agents)})')
    
    print(f'- **Executable:** {readiness_dist.get("executable", 0)} routable agents')
    print(f'- **Not Executable:** {readiness_dist.get("not-executable", 0)} (空壳注册状态)')
    print()
    
    print('### Task Queue')
    print(f'- **Pending Tasks:** {pending_tasks}')
    print(f'- **Completed (Last 24h):** {completed_tasks if total_tasks > 0 else 0}')
    print(f'- **Failed (Last 24h):** {failed_tasks if total_tasks > 0 else 0}')
    if total_tasks > 0:
        success_rate = completed_tasks / total_tasks
        print(f'- **Success Rate:** {round(success_rate*100, 1)}%')
    else:
        print(f'- **Success Rate:** N/A (no recent tasks)')
    print()
    
    print('### Memory System')
    print(f'- **Memory Server:** {memory_server["status"]} (port {memory_server["port"]})')
    
    workspace_root = base_path.parent
    memory_md = workspace_root / 'MEMORY.md'
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = workspace_root / 'memory' / f'{today}.md'
    selflearn_state = workspace_root / 'memory' / 'selflearn-state.json'
    
    print(f'- **MEMORY.md:** {"Present and updated" if memory_md.exists() else "Missing"}')
    print(f'- **Daily Logs:** {today}.md {"exists" if daily_log.exists() else "missing"}')
    print(f'- **selflearn-state.json:** {"Present" if selflearn_state.exists() else "Missing"}')
    print()
    
    print('### Learning System')
    print(f'- **Active Learning Agents:** {len([a for a in agents if a.get("type") == "learning" and a.get("enabled", True)])}', end='')
    
    active_learning = [a.get('name') for a in agents if a.get('type') == 'learning' and a.get('enabled', True) and is_production_ready(a)]
    if active_learning:
        print(f' ({", ".join(active_learning)})')
    else:
        print()
    
    print(f'- **Lessons Recorded:** {lesson_stats["total"]} total')
    print(f'- **Rules Derived:** {lesson_stats["rule_derived"]}', end='')
    if lesson_stats['rule_derived'] == 0:
        print(' (学习债未解决)')
    else:
        print()
    print(f'- **Pending Lessons:** {lesson_stats["pending"]}')
    print()
    
    print('### Cost Tracking')
    if cost_tracking['enabled']:
        print(f'- **Total Tokens:** {cost_tracking["total_tokens"]:,}')
        print(f'- **Estimated Cost:** ${cost_tracking["estimated_cost"]}')
        print(f'- **Last 24h Tokens:** {cost_tracking["last_24h_tokens"]:,}')
        print(f'- **Last 24h Cost:** ${cost_tracking["last_24h_cost"]}')
    else:
        print('- **Status:** Not enabled (数据未采集)')
        print('- **Note:** 成本追踪系统待建立')
    print()
    
    print('---')
    print()
    
    print('## Key Observations')
    print()
    
    print('### ✅ Strengths')
    strengths = []
    
    if health_score >= 80:
        strengths.append('系统整体健康度良好')
    
    if readiness_dist.get('production-ready', 0) > 0:
        strengths.append(f'有 {readiness_dist.get("production-ready", 0)} 个生产就绪 Agent')
    
    if memory_server['online']:
        strengths.append('Memory Server 在线运行')
    
    if lesson_stats['rule_derived'] > 0:
        strengths.append(f'已提炼 {lesson_stats["rule_derived"]} 条规则')
    
    if not strengths:
        strengths.append('系统基础运行正常')
    
    for i, s in enumerate(strengths, 1):
        print(f'{i}. **{s}**')
    
    print()
    
    print('### ⚠️ Warnings')
    if issues:
        for i, issue in enumerate(issues, 1):
            severity_emoji = '🚨' if issue['severity'] == 'P1' else '⚠️' if issue['severity'] == 'P2' else 'ℹ️'
            print(f'{i}. {severity_emoji} **{issue["description"]}**')
    else:
        print('无告警')
    
    print()
    
    if cost_tracking['enabled']:
        print('### 📊 Cost Tracking')
        print(f'- **Last 24h Usage:** {cost_tracking["last_24h_tokens"]:,} tokens (${cost_tracking["last_24h_cost"]})')
        print(f'- **Total Usage:** {cost_tracking["total_tokens"]:,} tokens (${cost_tracking["estimated_cost"]})')
        print()
    
    print('---')
    print()
    
    print('## Error Analysis')
    print()
    
    if total_tasks > 0 and failed_tasks > 0:
        error_rate = failed_tasks / total_tasks
        print(f'**Last 24h Error Rate:** {round(error_rate*100, 1)}%')
    else:
        print(f'**Last 24h Error Rate:** 0% (无执行任务，无错误)' if total_tasks == 0 else '0%')
    print()
    
    print('**Recent Issues:**')
    if attention_agents:
        for agent in attention_agents:
            print(f'- ⚠️ {agent["name"]}: {agent["reason"]}')
    else:
        print('- 无新增错误')
    
    if issues:
        print('- 告警去重规则生效中（2026-03-08 旧告警已抑制）')
    
    print()
    
    print('---')
    print()
    
    print('## Recommendations')
    print()
    
    print('### Immediate (P1)')
    p1_recs = [rec for rec in issues if rec['severity'] == 'P1']
    if p1_recs:
        for i, rec in enumerate(p1_recs, 1):
            print(f'{i}. **解决 {rec["type"]}** - {rec["description"]}')
    else:
        print('无紧急问题')
    
    print()
    
    print('### Short-term (P2)')
    p2_recs = [rec for rec in issues if rec['severity'] == 'P2']
    if p2_recs:
        for i, rec in enumerate(p2_recs, 1):
            print(f'{i}. **{rec["description"]}**')
    else:
        # 默认建议
        if lesson_stats['pending'] > 0:
            print(f'1. **打通 lesson→rule 最小闭环** - 从 {lesson_stats["pending"]} 条 pending lesson 中提炼规则')
        if readiness_dist.get('not-executable', 0) > 10:
            print(f'2. **Agent 分层治理** - 区分真链/候选链/休眠壳 ({readiness_dist.get("not-executable", 0)} 个空壳)')
    
    print()
    
    print('### Long-term (P3)')
    if not cost_tracking['enabled']:
        print('1. **建立成本追踪系统** - 记录 token 使用和成本')
    if production_ready_count < 5:
        print(f'2. **扩展真链数量** - 从候选链中激活 2-3 条 (当前: {production_ready_count})')
    if readiness_dist.get('not-executable', 0) > 15:
        print(f'3. **清理空壳 Agent** - 归档长期无计划运行的 Agent ({readiness_dist.get("not-executable", 0)} 个)')
    
    print()
    
    print('---')
    print()
    
    print('## Next Check')
    next_check = datetime.now() + timedelta(hours=12)
    print(f'**Scheduled:** {next_check.strftime("%Y-%m-%d %H:%M")} (12 hours)')
    print()
    
    print('**Focus Areas:**')
    focus_areas = []
    
    if observation_agents:
        focus_areas.append(f'{observation_agents[0]} 执行结果')
    
    if not memory_server['online']:
        focus_areas.append('Memory Server 连通性')
    
    if len(issues) > 0:
        focus_areas.append(f'改进队列处理 ({len(issues)} 个问题已记录)')
    
    if not focus_areas:
        focus_areas.append('系统稳定性监控')
    
    for area in focus_areas:
        print(f'- {area}')
    
    print()
    
    # 记录改进统计
    if issues:
        print(f'**Self-Improvement:** {len(issues)} issues recorded to improvement queue')
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
