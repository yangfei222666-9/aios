# -*- coding: utf-8 -*-
"""
太极OS Dashboard v2.0

Phase 3 迁移目标：基于统一状态词表的结构化聚合。

核心原则：
1. 聚合口径一致 — 卡片数字、分类统计、详情列表必须同源
2. 边界值不污染图表 — no-sample / unknown / not-evaluable 不能被误算进异常
3. 对象间可比较但不混叠 — Agent/Task/Lesson 可以同屏展示，但不能硬压成一种状态
4. 适配层零重复推导 — 只消费 state_vocabulary_adapter.py

数据源：agents.json + task_queue.jsonl + lessons.json
输出：终端文本 Dashboard（未来可扩展为 Web）
"""

import json
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from state_vocabulary_adapter import get_agents_states, get_tasks_states, get_lessons_states

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TZ_CN = timezone(timedelta(hours=8))


# ============================================================
# 数据加载
# ============================================================

def load_agents() -> list:
    """加载 agents.json 并推导状态"""
    path = os.path.join(DATA_DIR, "agents.json")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        agents = data.get('agents', [])
    return get_agents_states(agents)


def load_tasks() -> list:
    """加载 task_queue.jsonl 并推导状态"""
    path = os.path.join(DATA_DIR, "task_queue.jsonl")
    tasks = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
    return get_tasks_states(tasks)


def load_lessons() -> list:
    """加载 lessons.json 并推导状态"""
    path = os.path.join(DATA_DIR, "lessons.json")
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        lessons = data.get('lessons', [])
    return get_lessons_states(lessons)


# ============================================================
# 聚合逻辑
# ============================================================

def aggregate_agents(agents: list) -> dict:
    """
    聚合 Agent 状态
    
    返回：
    {
        "total": int,
        "routable": int,  # 可调度（非 archived / shadow）
        "has_runs": int,  # 有运行记录（run != never-run / no-sample）
        "healthy": int,   # 健康（health == healthy）
        "no_sample": int, # 未形成样本（health == no-sample）
        "by_readiness": { "registered": int, ... },
        "by_run": { "never-run": int, ... },
        "by_health": { "healthy": int, ... }
    }
    """
    total = len(agents)
    
    # 统计分布
    by_readiness = defaultdict(int)
    by_run = defaultdict(int)
    by_health = defaultdict(int)
    
    routable = 0
    has_runs = 0
    healthy = 0
    no_sample = 0
    
    for agent in agents:
        state = agent.get('state', {})
        r = state.get('readiness', 'unknown')
        run = state.get('run', 'unknown')
        h = state.get('health', 'unknown')
        
        by_readiness[r] += 1
        by_run[run] += 1
        by_health[h] += 1
        
        # 可调度：非 archived / shadow
        if r not in ['archived', 'shadow']:
            routable += 1
        
        # 有运行记录：run != never-run / no-sample
        if run not in ['never-run', 'no-sample']:
            has_runs += 1
        
        # 健康：health == healthy
        if h == 'healthy':
            healthy += 1
        
        # 未形成样本：health == no-sample
        if h == 'no-sample':
            no_sample += 1
    
    return {
        "total": total,
        "routable": routable,
        "has_runs": has_runs,
        "healthy": healthy,
        "no_sample": no_sample,
        "by_readiness": dict(by_readiness),
        "by_run": dict(by_run),
        "by_health": dict(by_health)
    }


def aggregate_tasks(tasks: list) -> dict:
    """
    聚合 Task 状态
    
    返回：
    {
        "total": int,
        "pending": int,
        "running": int,
        "completed": int,
        "failed": int,
        "by_status": { "pending": int, ... }
    }
    """
    total = len(tasks)
    
    by_status = defaultdict(int)
    pending = 0
    running = 0
    completed = 0
    failed = 0
    
    for task in tasks:
        state = task.get('state', {})
        status = state.get('status', 'unknown')
        
        by_status[status] += 1
        
        if status == 'pending':
            pending += 1
        elif status == 'running':
            running += 1
        elif status == 'completed':
            completed += 1
        elif status == 'failed':
            failed += 1
    
    return {
        "total": total,
        "pending": pending,
        "running": running,
        "completed": completed,
        "failed": failed,
        "by_status": dict(by_status)
    }


def aggregate_lessons(lessons: list) -> dict:
    """
    聚合 Lesson 状态
    
    返回：
    {
        "total": int,
        "pending": int,
        "extracted": int,
        "validated": int,
        "applied": int,
        "by_derivation": { "pending": int, ... }
    }
    """
    total = len(lessons)
    
    by_derivation = defaultdict(int)
    pending = 0
    extracted = 0
    validated = 0
    applied = 0
    
    for lesson in lessons:
        state = lesson.get('state', {})
        derivation = state.get('derivation', 'unknown')
        
        by_derivation[derivation] += 1
        
        if derivation == 'pending':
            pending += 1
        elif derivation == 'extracted':
            extracted += 1
        elif derivation == 'validated':
            validated += 1
        elif derivation == 'applied':
            applied += 1
    
    return {
        "total": total,
        "pending": pending,
        "extracted": extracted,
        "validated": validated,
        "applied": applied,
        "by_derivation": dict(by_derivation)
    }


def collect_alerts(agent_agg: dict, task_agg: dict) -> list:
    """
    收集告警
    
    只显示真正可评估且异常的对象，不把 no-sample 当异常
    """
    alerts = []
    
    # Agent 告警：只关注有运行记录但不健康的
    unhealthy = agent_agg['by_health'].get('critical', 0)
    degraded = agent_agg['by_health'].get('degraded', 0)
    
    if unhealthy > 0:
        alerts.append(f"⚠️ {unhealthy} 个 Agent 健康度严重")
    if degraded > 0:
        alerts.append(f"ℹ️ {degraded} 个 Agent 健康度退化")
    
    # Task 告警：失败任务
    failed = task_agg.get('failed', 0)
    if failed > 0:
        alerts.append(f"⚠️ {failed} 个任务失败")
    
    return alerts


# ============================================================
# 渲染
# ============================================================

def render_overview_cards(agent_agg: dict, task_agg: dict, lesson_agg: dict) -> str:
    """渲染总览卡片"""
    lines = []
    lines.append("【总览卡片】")
    lines.append("")
    
    # Agent 卡片
    lines.append(f"Agent:")
    lines.append(f"  总数: {agent_agg['total']}")
    lines.append(f"  可调度: {agent_agg['routable']}")
    lines.append(f"  有运行记录: {agent_agg['has_runs']}")
    lines.append(f"  健康: {agent_agg['healthy']}")
    lines.append(f"  未形成样本: {agent_agg['no_sample']}")
    lines.append("")
    
    # Task 卡片
    lines.append(f"Task:")
    lines.append(f"  总数: {task_agg['total']}")
    lines.append(f"  待处理: {task_agg['pending']}")
    lines.append(f"  运行中: {task_agg['running']}")
    lines.append(f"  已完成: {task_agg['completed']}")
    lines.append(f"  失败: {task_agg['failed']}")
    lines.append("")
    
    # Lesson 卡片
    lines.append(f"Lesson:")
    lines.append(f"  总数: {lesson_agg['total']}")
    lines.append(f"  待提炼: {lesson_agg['pending']}")
    lines.append(f"  已提炼: {lesson_agg['extracted']}")
    lines.append(f"  已验证: {lesson_agg['validated']}")
    lines.append(f"  已应用: {lesson_agg['applied']}")
    
    return "\n".join(lines)


def render_distribution_panels(agent_agg: dict, lesson_agg: dict) -> str:
    """渲染分组面板"""
    lines = []
    lines.append("【分组面板】")
    lines.append("")
    
    # Agent readiness 分布
    lines.append("Agent 就绪度分布:")
    for status, count in sorted(agent_agg['by_readiness'].items()):
        lines.append(f"  {status}: {count}")
    lines.append("")
    
    # Agent run 分布
    lines.append("Agent 运行状态分布:")
    for status, count in sorted(agent_agg['by_run'].items()):
        lines.append(f"  {status}: {count}")
    lines.append("")
    
    # Agent health 分布
    lines.append("Agent 健康度分布:")
    for status, count in sorted(agent_agg['by_health'].items()):
        marker = "⚠️" if status in ['critical', 'degraded'] else ""
        lines.append(f"  {marker}{status}: {count}")
    lines.append("")
    
    # Lesson derivation 分布
    lines.append("Lesson 提炼状态分布:")
    for status, count in sorted(lesson_agg['by_derivation'].items()):
        lines.append(f"  {status}: {count}")
    
    return "\n".join(lines)


def render_alerts(alerts: list) -> str:
    """渲染告警面板"""
    lines = []
    lines.append("【告警面板】")
    lines.append("")
    
    if not alerts:
        lines.append("无告警")
    else:
        for alert in alerts:
            lines.append(alert)
    
    return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================

def generate_dashboard() -> str:
    """生成 Dashboard"""
    now = datetime.now(TZ_CN).strftime("%Y-%m-%d %H:%M:%S")
    
    # 加载数据
    agents = load_agents()
    tasks = load_tasks()
    lessons = load_lessons()
    
    # 聚合
    agent_agg = aggregate_agents(agents)
    task_agg = aggregate_tasks(tasks)
    lesson_agg = aggregate_lessons(lessons)
    
    # 收集告警
    alerts = collect_alerts(agent_agg, task_agg)
    
    # 渲染
    overview = render_overview_cards(agent_agg, task_agg, lesson_agg)
    distribution = render_distribution_panels(agent_agg, lesson_agg)
    alerts_text = render_alerts(alerts)
    
    # 组装
    dashboard = f"""# 太极OS Dashboard v2.0

生成时间: {now}

---

{overview}

---

{distribution}

---

{alerts_text}

---

太极OS · Dashboard v2.0 · 基于统一状态词表
"""
    
    return dashboard


def main():
    """主入口"""
    dashboard = generate_dashboard()
    print(dashboard)
    
    # 保存到文件
    output_path = os.path.join(BASE_DIR, "reports", "dashboard_v2.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(dashboard)
    
    print(f"\n已保存到: {output_path}")


if __name__ == "__main__":
    main()
