# -*- coding: utf-8 -*-
"""
太极OS 日报生成器 v2.0

Phase 2 迁移目标：基于统一状态词表输出日报。

核心原则：
1. 状态叙述不失真 — Agent/Skill 用 readiness/run/health，Task 用 run/health，Lesson 用 derivation
2. 无样本对象不制造噪音 — no-sample 不是异常，unknown 不是风险
3. 文本层区分"就绪"和"已验证" — 已配置/已就绪/已运行/已验证/健康稳定/暂不可评估 分开写
4. 汇总口径稳定 — 摘要、分组、正文三层一致

数据源：agents.json + task_executions.jsonl + lessons.json + task_queue.jsonl
输出：reports/daily_report_v2_YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

TZ_CN = timezone(timedelta(hours=8))


# ============================================================
# 状态推导层 — 使用统一适配层
# ============================================================

from state_vocabulary_adapter import get_agents_states

def load_agents_with_states(agents_file: str) -> list:
    """
    读取 agents.json 并通过统一适配层推导状态
    
    Phase 2 迁移：使用 state_vocabulary_adapter 统一推导逻辑
    """
    with open(agents_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        agents = data.get('agents', [])
    
    # 使用统一适配层推导状态
    return get_agents_states(agents)


def infer_lesson_derivation(lesson: dict) -> str:
    """推导 Lesson 提炼状态（derivation）。"""
    status = lesson.get("regeneration_status", lesson.get("derivation_status", ""))
    if status in ("extracted", "applied", "validated", "stable"):
        return status
    if status == "pending":
        return "pending"
    return "recorded"


# ============================================================
# 数据加载
# ============================================================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def filter_today(entries, date_str, ts_key="timestamp"):
    result = []
    for e in entries:
        ts = e.get(ts_key)
        if ts is None:
            continue
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=TZ_CN)
        elif isinstance(ts, str):
            if ts[:10] == date_str:
                result.append(e)
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                dt = dt.astimezone(TZ_CN)
            except ValueError:
                continue
        else:
            continue
        if dt.strftime("%Y-%m-%d") == date_str:
            result.append(e)
    return result


# ============================================================
# 日报数据收集
# ============================================================

def collect_agent_summary(agents: list) -> dict:
    """
    收集 Agent 摘要，基于新词表三维度分组。
    
    返回结构：
    {
        "total": int,
        "by_readiness": { "production-ready": [...], "executable": [...], ... },
        "by_run": { "success": [...], "no-sample": [...], ... },
        "by_health": { "healthy": [...], "unknown": [...], ... },
        "routable_count": int,
        "active_count": int,
    }
    """
    by_readiness = {}
    by_run = {}
    by_health = {}
    
    for a in agents:
        state = a.get("state", {})
        r = state.get("readiness", "unknown")
        s = state.get("run", "unknown")
        h = state.get("health", "unknown")
        
        name = a.get("name", "unknown")
        entry = {"name": name, "readiness": r, "run": s, "health": h, "agent": a}
        
        by_readiness.setdefault(r, []).append(entry)
        by_run.setdefault(s, []).append(entry)
        by_health.setdefault(h, []).append(entry)
    
    # 可路由 = 非 archived 且非 shadow
    routable = [a for a in agents if a.get("state", {}).get("readiness") not in ("archived", "shadow")]
    active = [a for a in routable if a.get("state", {}).get("run") == "completed"]
    
    return {
        "total": len(agents),
        "by_readiness": by_readiness,
        "by_run": by_run,
        "by_health": by_health,
        "routable_count": len(routable),
        "active_count": len(active),
    }


def collect_task_summary(date_str: str) -> dict:
    """收集 Task 摘要。"""
    try:
        from paths import TASK_EXECUTIONS as _TE, TASK_QUEUE as _TQ
        exec_path = str(_TE)
        queue_path = str(_TQ)
    except ImportError:
        exec_path = os.path.join(BASE_DIR, "task_executions.jsonl")
        queue_path = os.path.join(DATA_DIR, "task_queue.jsonl")
    
    all_tasks = load_jsonl(exec_path)
    today_tasks = filter_today(all_tasks, date_str)
    
    total = len(today_tasks)
    success = sum(1 for t in today_tasks if t.get("result", {}).get("success", False) or t.get("status") == "completed")
    failed = total - success
    
    durations = []
    for t in today_tasks:
        d = t.get("result", {}).get("duration")
        if isinstance(d, (int, float)) and d >= 0:
            durations.append(d)
    avg_latency = round(sum(durations) / len(durations), 2) if durations else 0.0
    
    # Queue
    queue = load_jsonl(queue_path)
    pending = sum(1 for t in queue if t.get("status") == "pending")
    
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success / total * 100, 1) if total > 0 else 0.0,
        "avg_latency": avg_latency,
        "pending": pending,
        "sample_state": "noise" if total < 10 else ("warmup" if total <= 50 else "valid"),
    }


def collect_lesson_summary() -> dict:
    """收集 Lesson 摘要，基于 derivation 状态分组。"""
    path = os.path.join(BASE_DIR, "lessons.json")
    raw = load_json(path)
    
    if isinstance(raw, list):
        lessons = raw
    elif isinstance(raw, dict):
        lessons = raw.get("lessons", [])
    else:
        lessons = []
    
    by_derivation = {}
    for l in lessons:
        d = infer_lesson_derivation(l)
        by_derivation.setdefault(d, []).append(l)
    
    rules_derived = raw.get("rules_derived", []) if isinstance(raw, dict) else []
    
    return {
        "total": len(lessons),
        "by_derivation": by_derivation,
        "rules_derived_count": len(rules_derived),
    }


# ============================================================
# 日报文本生成
# ============================================================

# 中文映射表 — 保证文本层表达一致
READINESS_LABEL = {
    "production-ready": "生产就绪",
    "validated": "已验证",
    "executable": "已就绪",
    "registered": "已注册（未进入执行链）",
    "shadow": "保留观察（不路由）",
    "archived": "已归档",
}

RUN_LABEL = {
    "success": "运行正常",
    "failed": "运行失败",
    "no-sample": "未形成样本",
}

HEALTH_LABEL = {
    "healthy": "健康",
    "degraded": "性能退化",
    "unhealthy": "不健康",
    "insufficient-sample": "样本不足，暂不可评估",
    "unknown": "暂不可评估",
}

DERIVATION_LABEL = {
    "recorded": "已记录",
    "pending": "待提炼",
    "extracted": "已提炼",
    "applied": "已应用",
    "validated": "已验证",
    "stable": "稳定有效",
}


def _agent_section(agent_summary: dict) -> str:
    """生成 Agent 段落。"""
    lines = []
    total = agent_summary["total"]
    routable = agent_summary["routable_count"]
    active = agent_summary["active_count"]
    
    lines.append(f"Agent 总数: {total} | 可调度: {routable} | 有运行记录: {active}")
    lines.append("")
    
    # 按 readiness 分组展示
    lines.append("按就绪度:")
    by_r = agent_summary["by_readiness"]
    # 按优先级排序
    order = ["production-ready", "validated", "executable", "registered", "shadow", "archived"]
    for r in order:
        entries = by_r.get(r, [])
        if not entries:
            continue
        label = READINESS_LABEL.get(r, r)
        names = [e["name"] for e in entries]
        lines.append(f"  {label} ({len(entries)}): {', '.join(names)}")
    
    lines.append("")
    
    # 按运行状态分组
    lines.append("按运行状态:")
    by_s = agent_summary["by_run"]
    for s in ["success", "failed", "no-sample"]:
        entries = by_s.get(s, [])
        if not entries:
            continue
        label = RUN_LABEL.get(s, s)
        names = [e["name"] for e in entries]
        lines.append(f"  {label} ({len(entries)}): {', '.join(names)}")
    
    lines.append("")
    
    # 按健康度分组
    lines.append("按健康度:")
    by_h = agent_summary["by_health"]
    for h in ["healthy", "degraded", "unhealthy", "insufficient-sample", "unknown"]:
        entries = by_h.get(h, [])
        if not entries:
            continue
        label = HEALTH_LABEL.get(h, h)
        names = [e["name"] for e in entries]
        lines.append(f"  {label} ({len(entries)}): {', '.join(names)}")
    
    return "\n".join(lines)


def _task_section(task_summary: dict) -> str:
    """生成 Task 段落。"""
    lines = []
    t = task_summary
    
    lines.append(f"今日任务: {t['total']} | 成功: {t['success']} | 失败: {t['failed']} | 成功率: {t['success_rate']}%")
    lines.append(f"平均耗时: {t['avg_latency']}s | 待处理: {t['pending']}")
    
    if t["sample_state"] == "noise":
        lines.append(f"样本状态: 样本不足（{t['total']} < 10），指标仅供参考")
    elif t["sample_state"] == "warmup":
        lines.append(f"样本状态: 预热中（{t['total']} 条），趋势初步可参考")
    else:
        lines.append(f"样本状态: 有效（{t['total']} 条）")
    
    return "\n".join(lines)


def _lesson_section(lesson_summary: dict) -> str:
    """生成 Lesson 段落。"""
    lines = []
    total = lesson_summary["total"]
    rules = lesson_summary["rules_derived_count"]
    
    lines.append(f"Lesson 总数: {total} | 已提炼规则: {rules}")
    
    by_d = lesson_summary["by_derivation"]
    if by_d:
        lines.append("按提炼状态:")
        for d in ["stable", "validated", "applied", "extracted", "pending", "recorded"]:
            entries = by_d.get(d, [])
            if not entries:
                continue
            label = DERIVATION_LABEL.get(d, d)
            lines.append(f"  {label} ({len(entries)})")
    
    if total == 0:
        lines.append("暂无 Lesson 记录")
    
    return "\n".join(lines)


def _summary_section(agent_summary: dict, task_summary: dict, lesson_summary: dict) -> str:
    """
    生成顶部摘要 — 口径必须和正文一致。
    
    摘要只用正文中已经计算好的数字，不重新计算。
    """
    lines = []
    
    # Agent 一句话
    total_agents = agent_summary["total"]
    routable = agent_summary["routable_count"]
    active = agent_summary["active_count"]
    no_sample_count = len(agent_summary["by_run"].get("no-sample", []))
    
    lines.append(f"Agent: {total_agents} 个，{routable} 个可调度，{active} 个有运行记录")
    if no_sample_count > 0:
        lines.append(f"  其中 {no_sample_count} 个尚未形成样本（非异常）")
    
    # Task 一句话
    t = task_summary
    if t["total"] == 0:
        lines.append("Task: 今日无任务执行")
    else:
        lines.append(f"Task: 今日 {t['total']} 个，成功率 {t['success_rate']}%")
        if t["sample_state"] == "noise":
            lines.append("  样本不足，指标仅供参考")
    
    # Lesson 一句话
    l = lesson_summary
    if l["total"] == 0:
        lines.append("Lesson: 暂无记录")
    else:
        lines.append(f"Lesson: {l['total']} 条，已提炼规则 {l['rules_derived_count']} 条")
    
    return "\n".join(lines)


def _alerts_section(agent_summary: dict, task_summary: dict) -> str:
    """
    生成告警段落。
    
    核心规则：
    - no-sample 不是告警
    - unknown health 不是告警
    - 只有真实异常才告警
    """
    alerts = []
    
    # Agent 告警：只关注有运行记录但不健康的
    unhealthy = agent_summary["by_health"].get("unhealthy", [])
    degraded = agent_summary["by_health"].get("degraded", [])
    
    for e in unhealthy:
        alerts.append(f"⚠️ {e['name']}: 不健康（成功率低于 70%）")
    for e in degraded:
        alerts.append(f"ℹ️ {e['name']}: 性能退化（成功率 70-90%）")
    
    # Task 告警
    t = task_summary
    if t["total"] > 0 and t["success_rate"] < 80:
        alerts.append(f"⚠️ 今日任务成功率 {t['success_rate']}%，低于 80% 阈值")
    if t["failed"] > 0:
        alerts.append(f"ℹ️ 今日有 {t['failed']} 个任务失败")
    
    if not alerts:
        return "无告警"
    
    return "\n".join(alerts)


def generate_daily_report_v2(date_str: str = None) -> str:
    """
    生成 v2 日报。
    
    返回完整 markdown 文本。
    """
    if date_str is None:
        date_str = datetime.now(TZ_CN).strftime("%Y-%m-%d")
    
    now = datetime.now(TZ_CN).strftime("%Y-%m-%d %H:%M")
    
    # 加载数据（使用统一适配层）
    agents_file = os.path.join(DATA_DIR, "agents.json")
    agents = load_agents_with_states(agents_file)
    
    # 收集各维度摘要
    agent_summary = collect_agent_summary(agents)
    task_summary = collect_task_summary(date_str)
    lesson_summary = collect_lesson_summary()
    
    # 生成各段落
    summary = _summary_section(agent_summary, task_summary, lesson_summary)
    agent_text = _agent_section(agent_summary)
    task_text = _task_section(task_summary)
    lesson_text = _lesson_section(lesson_summary)
    alerts_text = _alerts_section(agent_summary, task_summary)
    
    report = f"""# 太极OS 日报 — {date_str}

生成时间: {now}

---

## 总览

{summary}

---

## Agent 状态

{agent_text}

---

## 任务执行

{task_text}

---

## 经验沉淀

{lesson_text}

---

## 告警

{alerts_text}

---

太极OS · 日报 v2.0 · 基于统一状态词表
"""
    
    return report


def save_report(report: str, date_str: str = None):
    """保存日报到 reports/ 目录。"""
    if date_str is None:
        date_str = datetime.now(TZ_CN).strftime("%Y-%m-%d")
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"daily_report_v2_{date_str}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path


def run(date_str: str = None):
    """主入口。"""
    if date_str is None:
        date_str = datetime.now(TZ_CN).strftime("%Y-%m-%d")
    
    report = generate_daily_report_v2(date_str)
    path = save_report(report, date_str)
    
    print(report)
    print(f"\n已保存到: {path}")
    
    return report


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    run(date_str)
