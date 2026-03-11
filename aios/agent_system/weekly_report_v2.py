# -*- coding: utf-8 -*-
"""
太极OS 周报生成器 v2.0

Phase 4 迁移目标：基于统一状态词表的跨周期总结。

核心原则：
1. 周汇总口径一致 — 总览、分组、结论必须来自统一适配层
2. 时间跨度不制造假变化 — no-sample / unknown / not-evaluable 不能因为跨 7 天就被写成"退化""异常"
3. "状态"与"趋势"分开写 — 当前状态 vs 本周变化，不能混淆
4. 周报仍然不压成一个总状态 — Agent 还是 readiness / run / health，Lesson 还是 derivation

数据源：agents.json + task_executions.jsonl + lessons.json
输出：reports/weekly_report_v2_YYYY-WW.md
"""

import json
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from state_vocabulary_adapter import get_agents_states, get_tasks_states, get_lessons_states

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
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


def load_tasks_this_week(week_start: str, week_end: str) -> list:
    """加载本周任务执行记录"""
    path = os.path.join(BASE_DIR, "task_executions.jsonl")
    if not os.path.exists(path):
        return []
    
    tasks = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                # 检查时间戳是否在本周范围内
                timestamp = task.get('timestamp', '')
                if isinstance(timestamp, str):
                    # 提取日期部分（YYYY-MM-DD）
                    date_part = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]
                    if week_start <= date_part <= week_end:
                        tasks.append(task)
    
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
    聚合 Agent 状态（当前状态，不是变化）
    
    返回：
    {
        "total": int,
        "routable": int,
        "has_runs": int,
        "healthy": int,
        "no_sample": int,
        "by_readiness": { "registered": int, ... },
        "by_run": { "never-run": int, ... },
        "by_health": { "healthy": int, ... }
    }
    """
    total = len(agents)
    
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
        
        if r not in ['archived', 'shadow']:
            routable += 1
        
        if run not in ['never-run', 'no-sample']:
            has_runs += 1
        
        if h == 'healthy':
            healthy += 1
        
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
    聚合本周任务执行情况
    
    返回：
    {
        "total": int,
        "completed": int,
        "failed": int,
        "success_rate": float
    }
    """
    total = len(tasks)
    completed = 0
    failed = 0
    
    for task in tasks:
        result = task.get('result', {})
        if result.get('success', False) or task.get('status') == 'completed':
            completed += 1
        else:
            failed += 1
    
    success_rate = round(completed / total * 100, 1) if total > 0 else 0.0
    
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "success_rate": success_rate
    }


def aggregate_lessons(lessons: list) -> dict:
    """
    聚合 Lesson 状态（当前状态，不是变化）
    
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


def collect_highlights(agents: list, agent_agg: dict) -> dict:
    """
    收集本周重点
    
    返回：
    {
        "new_validated": list,  # 新增已验证对象
        "new_healthy": list,    # 新增健康运行对象
        "truly_abnormal": list, # 真正异常对象
        "still_no_sample": list # 仍未形成样本的对象群
    }
    """
    new_validated = []
    new_healthy = []
    truly_abnormal = []
    still_no_sample = []
    
    for agent in agents:
        state = agent.get('state', {})
        name = agent.get('name', 'unknown')
        r = state.get('readiness', 'unknown')
        h = state.get('health', 'unknown')
        
        # 新增已验证对象（readiness == validated / production-ready / stable）
        if r in ['validated', 'production-ready', 'stable']:
            new_validated.append(name)
        
        # 新增健康运行对象（health == healthy）
        if h == 'healthy':
            new_healthy.append(name)
        
        # 真正异常对象（health == critical / degraded）
        if h in ['critical', 'degraded']:
            truly_abnormal.append(name)
        
        # 仍未形成样本的对象群（health == no-sample）
        if h == 'no-sample':
            still_no_sample.append(name)
    
    return {
        "new_validated": new_validated,
        "new_healthy": new_healthy,
        "truly_abnormal": truly_abnormal,
        "still_no_sample": still_no_sample
    }


def collect_alerts(agent_agg: dict, task_agg: dict) -> list:
    """
    收集告警（只写真实异常，不把无样本当问题）
    """
    alerts = []
    
    # Agent 告警：只关注有运行记录但不健康的
    critical = agent_agg['by_health'].get('critical', 0)
    degraded = agent_agg['by_health'].get('degraded', 0)
    
    if critical > 0:
        alerts.append(f"⚠️ {critical} 个 Agent 健康度严重")
    if degraded > 0:
        alerts.append(f"ℹ️ {degraded} 个 Agent 健康度退化")
    
    # Task 告警：本周失败任务
    failed = task_agg.get('failed', 0)
    if failed > 0:
        alerts.append(f"⚠️ 本周有 {failed} 个任务失败")
    
    return alerts


# ============================================================
# 渲染
# ============================================================

def render_overview(agent_agg: dict, task_agg: dict, lesson_agg: dict) -> str:
    """渲染本周总览"""
    lines = []
    lines.append("## 本周总览")
    lines.append("")
    
    # Agent 总览
    lines.append(f"**Agent:**")
    lines.append(f"- 总数: {agent_agg['total']}")
    lines.append(f"- 可调度: {agent_agg['routable']}")
    lines.append(f"- 有运行记录: {agent_agg['has_runs']}")
    lines.append(f"- 健康: {agent_agg['healthy']}")
    lines.append(f"- 未形成样本: {agent_agg['no_sample']}")
    lines.append("")
    
    # Task 总览
    lines.append(f"**Task:**")
    lines.append(f"- 本周执行: {task_agg['total']}")
    lines.append(f"- 成功: {task_agg['completed']}")
    lines.append(f"- 失败: {task_agg['failed']}")
    lines.append(f"- 成功率: {task_agg['success_rate']}%")
    lines.append("")
    
    # Lesson 总览
    lines.append(f"**Lesson:**")
    lines.append(f"- 总数: {lesson_agg['total']}")
    lines.append(f"- 待提炼: {lesson_agg['pending']}")
    lines.append(f"- 已提炼: {lesson_agg['extracted']}")
    lines.append(f"- 已验证: {lesson_agg['validated']}")
    lines.append(f"- 已应用: {lesson_agg['applied']}")
    
    return "\n".join(lines)


def render_distribution(agent_agg: dict, lesson_agg: dict) -> str:
    """渲染分组摘要"""
    lines = []
    lines.append("## 分组摘要")
    lines.append("")
    
    # Agent readiness 分布
    lines.append("**Agent 就绪度分布:**")
    for status, count in sorted(agent_agg['by_readiness'].items()):
        lines.append(f"- {status}: {count}")
    lines.append("")
    
    # Agent run 分布
    lines.append("**Agent 运行状态分布:**")
    for status, count in sorted(agent_agg['by_run'].items()):
        lines.append(f"- {status}: {count}")
    lines.append("")
    
    # Agent health 分布
    lines.append("**Agent 健康度分布:**")
    for status, count in sorted(agent_agg['by_health'].items()):
        marker = "⚠️ " if status in ['critical', 'degraded'] else ""
        lines.append(f"- {marker}{status}: {count}")
    lines.append("")
    
    # Lesson derivation 分布
    lines.append("**Lesson 提炼状态分布:**")
    for status, count in sorted(lesson_agg['by_derivation'].items()):
        lines.append(f"- {status}: {count}")
    
    return "\n".join(lines)


def render_highlights(highlights: dict) -> str:
    """渲染本周重点"""
    lines = []
    lines.append("## 本周重点")
    lines.append("")
    
    # 新增已验证对象
    if highlights['new_validated']:
        lines.append(f"**新增已验证对象 ({len(highlights['new_validated'])}):**")
        for name in highlights['new_validated'][:5]:  # 最多显示 5 个
            lines.append(f"- {name}")
        if len(highlights['new_validated']) > 5:
            lines.append(f"- ... 及其他 {len(highlights['new_validated']) - 5} 个")
        lines.append("")
    
    # 新增健康运行对象
    if highlights['new_healthy']:
        lines.append(f"**新增健康运行对象 ({len(highlights['new_healthy'])}):**")
        for name in highlights['new_healthy'][:5]:
            lines.append(f"- {name}")
        if len(highlights['new_healthy']) > 5:
            lines.append(f"- ... 及其他 {len(highlights['new_healthy']) - 5} 个")
        lines.append("")
    
    # 真正异常对象
    if highlights['truly_abnormal']:
        lines.append(f"**真正异常对象 ({len(highlights['truly_abnormal'])}):**")
        for name in highlights['truly_abnormal']:
            lines.append(f"- ⚠️ {name}")
        lines.append("")
    
    # 仍未形成样本的对象群
    if highlights['still_no_sample']:
        lines.append(f"**仍未形成样本的对象群 ({len(highlights['still_no_sample'])}):**")
        lines.append(f"- 共 {len(highlights['still_no_sample'])} 个 Agent 尚未运行")
        lines.append("")
    
    if not any([highlights['new_validated'], highlights['new_healthy'], 
                highlights['truly_abnormal'], highlights['still_no_sample']]):
        lines.append("本周无重点变化")
    
    return "\n".join(lines)


def render_alerts(alerts: list) -> str:
    """渲染告警段"""
    lines = []
    lines.append("## 告警")
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

def get_week_range(date_str: str = None) -> tuple:
    """
    获取指定日期所在周的起止日期
    
    返回：(week_start, week_end, week_label)
    例如：("2026-03-09", "2026-03-15", "2026-W11")
    """
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now(TZ_CN)
    
    # 获取周一
    week_start = dt - timedelta(days=dt.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_label = week_start.strftime("%Y-W%U")
    
    return (
        week_start.strftime("%Y-%m-%d"),
        week_end.strftime("%Y-%m-%d"),
        week_label
    )


def generate_weekly_report(date_str: str = None) -> str:
    """
    生成周报
    
    参数：
    - date_str: 指定日期（YYYY-MM-DD），默认为当前日期
    
    返回：完整 markdown 文本
    """
    week_start, week_end, week_label = get_week_range(date_str)
    now = datetime.now(TZ_CN).strftime("%Y-%m-%d %H:%M:%S")
    
    # 加载数据
    agents = load_agents()
    tasks = load_tasks_this_week(week_start, week_end)
    lessons = load_lessons()
    
    # 聚合
    agent_agg = aggregate_agents(agents)
    task_agg = aggregate_tasks(tasks)
    lesson_agg = aggregate_lessons(lessons)
    
    # 收集重点和告警
    highlights = collect_highlights(agents, agent_agg)
    alerts = collect_alerts(agent_agg, task_agg)
    
    # 渲染
    overview = render_overview(agent_agg, task_agg, lesson_agg)
    distribution = render_distribution(agent_agg, lesson_agg)
    highlights_text = render_highlights(highlights)
    alerts_text = render_alerts(alerts)
    
    # 组装
    report = f"""# 太极OS 周报 — {week_label}

周期: {week_start} ~ {week_end}  
生成时间: {now}

---

{overview}

---

{distribution}

---

{highlights_text}

---

{alerts_text}

---

太极OS · 周报 v2.0 · 基于统一状态词表
"""
    
    return report


def save_report(report: str, week_label: str):
    """保存周报到 reports/ 目录"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"weekly_report_v2_{week_label}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(report)
    return path


def main():
    """主入口"""
    import sys
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    
    report = generate_weekly_report(date_str)
    week_start, week_end, week_label = get_week_range(date_str)
    path = save_report(report, week_label)
    
    print(report)
    print(f"\n已保存到: {path}")


if __name__ == "__main__":
    main()
