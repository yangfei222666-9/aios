#!/usr/bin/env python3
"""
AIOS Health Monitor v1.0.0
太极OS 健康监控 + 可观测性报告。
四层报告：L1 Runtime, L2 Incident, L3 Trend, L4 Diagnosis。
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data")
WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")


def load_json(filepath: Path) -> dict:
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return {}


def load_jsonl(filepath: Path) -> list:
    records = []
    if not filepath.exists():
        return records
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return records


# ─── L1: Runtime ───

def analyze_runtime(agents_data: dict, task_queue: list, heartbeat_stats: dict) -> dict:
    """L1: 当前运行时状态"""
    agents = agents_data.get("agents", [])

    # Agent 分桶
    buckets = {
        "active_routable": [],
        "active_non_routable": [],
        "shadow": [],
        "disabled": [],
        "idle_never_triggered": [],
    }

    for agent in agents:
        name = agent.get("name", "")
        enabled = agent.get("enabled", True)
        mode = agent.get("mode", "active")
        routable = agent.get("routable", False)
        lifecycle = agent.get("lifecycle_state", "active")
        stats = agent.get("stats", {})
        total = stats.get("tasks_total", 0)

        # Shadow / Disabled 判定（最高优先级）
        if not enabled or mode in ["shadow", "disabled"] or lifecycle in ["shadow", "disabled"]:
            if mode == "shadow" or lifecycle == "shadow":
                buckets["shadow"].append(name)
            else:
                buckets["disabled"].append(name)
            continue

        # Active 判定
        if routable:
            if total > 0:
                buckets["active_routable"].append(name)
            else:
                buckets["idle_never_triggered"].append(name)
        else:
            buckets["active_non_routable"].append(name)

    # 任务队列状态
    queue_status = defaultdict(int)
    for task in task_queue:
        status = task.get("status", "unknown")
        queue_status[status] += 1

    # 可调度 Agent 数（排除 shadow/disabled）
    schedulable = len(buckets["active_routable"]) + len(buckets["idle_never_triggered"]) + len(buckets["active_non_routable"])
    active_pct = (len(buckets["active_routable"]) / schedulable * 100) if schedulable > 0 else 0

    return {
        "total_agents": len(agents),
        "schedulable_agents": schedulable,
        "active_routable": len(buckets["active_routable"]),
        "active_pct": round(active_pct, 1),
        "shadow": len(buckets["shadow"]),
        "disabled": len(buckets["disabled"]),
        "idle_never_triggered": len(buckets["idle_never_triggered"]),
        "buckets": {k: v for k, v in buckets.items()},
        "queue": dict(queue_status),
        "queue_total": len(task_queue),
        "heartbeat_last": heartbeat_stats.get("last_run", "unknown"),
        "heartbeat_status": heartbeat_stats.get("status", "unknown"),
    }


# ─── L2: Incident ───

def analyze_incidents(executions: list, alerts: list, top_n: int = 10) -> dict:
    """L2: 事件记录"""
    # 最近失败事件
    failures = [ex for ex in executions if ex.get("status") == "failed"]
    recent_failures = sorted(failures, key=lambda x: x.get("start_time", ""), reverse=True)[:top_n]

    # 告警按严重程度排序
    severity_order = {"CRIT": 0, "critical": 0, "HIGH": 1, "high": 1, "WARN": 2, "warning": 2, "LOW": 3, "low": 3}
    sorted_alerts = sorted(
        alerts,
        key=lambda x: severity_order.get(x.get("severity", x.get("level", "low")), 9)
    )[:top_n]

    # 连续失败的 Agent
    agent_failures = defaultdict(int)
    for ex in failures:
        agent_failures[ex.get("agent_id", "unknown")] += 1
    consecutive_failures = {k: v for k, v in agent_failures.items() if v >= 2}

    return {
        "recent_failures": [{
            "task_id": f.get("task_id", "?"),
            "agent_id": f.get("agent_id", "?"),
            "time": f.get("start_time", "?"),
            "error": str(f.get("error", f.get("result", {}).get("error", "unknown")))[:200],
        } for f in recent_failures],
        "alerts": [{
            "skill": a.get("skill", "?"),
            "severity": a.get("severity", a.get("level", "?")),
            "error_type": a.get("error_type", "?"),
            "time": a.get("timestamp", a.get("time", "?")),
        } for a in sorted_alerts],
        "consecutive_failures": consecutive_failures,
        "total_failures": len(failures),
        "total_alerts": len(alerts),
    }


# ─── L3: Trend ───

def analyze_trends(executions: list) -> dict:
    """L3: 趋势分析"""
    now = datetime.now(timezone.utc)
    windows = {"24h": 1, "7d": 7, "30d": 30}
    trends = {}

    for label, days in windows.items():
        cutoff = now - timedelta(days=days)
        window_execs = []
        for ex in executions:
            ts_str = ex.get("start_time", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    window_execs.append(ex)
            except (ValueError, AttributeError):
                pass

        total = len(window_execs)
        completed = sum(1 for e in window_execs if e.get("status") == "completed")
        failed = sum(1 for e in window_execs if e.get("status") == "failed")
        success_rate = (completed / total * 100) if total > 0 else 0

        # 错误类型分布
        error_types = defaultdict(int)
        for e in window_execs:
            if e.get("status") == "failed":
                err = str(e.get("error", e.get("result", {}).get("error", "unknown"))).lower()
                if "timeout" in err:
                    error_types["timeout"] += 1
                elif "network" in err or "connection" in err:
                    error_types["network"] += 1
                elif "resource" in err or "memory" in err:
                    error_types["resource"] += 1
                else:
                    error_types["other"] += 1

        trends[label] = {
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(success_rate, 1),
            "error_distribution": dict(error_types),
        }

    return trends


# ─── L4: Diagnosis ───

def diagnose(runtime: dict, incidents: dict, trends: dict) -> dict:
    """L4: 诊断结论"""
    weakest_link = "未发现明显弱链路"
    priority_fix = "当前无需紧急修复"
    expected_improvement = "系统运行正常"

    issues = []

    # 检查 1: 活跃率过低
    if runtime["active_pct"] < 30 and runtime["schedulable_agents"] > 5:
        issues.append({
            "severity": "high",
            "area": "Agent 活跃率",
            "detail": f"仅 {runtime['active_pct']}% Agent 活跃（{runtime['active_routable']}/{runtime['schedulable_agents']}）",
            "fix": "检查 idle Agent 的触发条件和路由配置",
            "improvement": f"活跃率提升到 50%+ 可增加系统吞吐量",
        })

    # 检查 2: 连续失败
    if incidents["consecutive_failures"]:
        worst = max(incidents["consecutive_failures"].items(), key=lambda x: x[1])
        issues.append({
            "severity": "high",
            "area": f"Agent {worst[0]} 连续失败",
            "detail": f"{worst[0]} 连续失败 {worst[1]} 次",
            "fix": f"检查 {worst[0]} 的超时设置、依赖服务、任务复杂度",
            "improvement": f"修复后可恢复 {worst[0]} 的正常执行能力",
        })

    # 检查 3: 成功率下降
    trend_7d = trends.get("7d", {})
    if trend_7d.get("success_rate", 100) < 80 and trend_7d.get("total", 0) > 5:
        issues.append({
            "severity": "medium",
            "area": "7天成功率",
            "detail": f"7天成功率仅 {trend_7d['success_rate']}%（{trend_7d['completed']}/{trend_7d['total']}）",
            "fix": "分析失败任务的共性，检查是否有系统性问题",
            "improvement": "成功率恢复到 90%+ 可提升系统可靠性",
        })

    # 检查 4: 队列积压
    pending = runtime["queue"].get("pending", 0)
    if pending > 10:
        issues.append({
            "severity": "medium",
            "area": "任务队列积压",
            "detail": f"队列中有 {pending} 个待处理任务",
            "fix": "增加处理频率或检查是否有阻塞任务",
            "improvement": "清理积压后可恢复正常处理速度",
        })

    # 检查 5: idle agents 过多
    idle_count = runtime["idle_never_triggered"]
    if idle_count > 10:
        issues.append({
            "severity": "low",
            "area": "大量 idle Agent",
            "detail": f"{idle_count} 个 Agent 从未触发",
            "fix": "评估是否需要保留，考虑降级为 standby 或 shadow",
            "improvement": "精简 Agent 列表可降低管理复杂度",
        })

    # 生成诊断结论
    if issues:
        issues.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 9))
        top = issues[0]
        weakest_link = top["area"]
        priority_fix = top["fix"]
        expected_improvement = top["improvement"]

    # 健康分数
    score = 100
    for issue in issues:
        if issue["severity"] == "critical":
            score -= 30
        elif issue["severity"] == "high":
            score -= 20
        elif issue["severity"] == "medium":
            score -= 10
        elif issue["severity"] == "low":
            score -= 5
    score = max(0, score)

    health_status = "GOOD" if score >= 80 else "WARNING" if score >= 60 else "CRITICAL"

    return {
        "health_score": score,
        "health_status": health_status,
        "weakest_link": weakest_link,
        "priority_fix": priority_fix,
        "expected_improvement": expected_improvement,
        "issues": issues,
        "diagnosis_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def generate_reports(runtime: dict, incidents: dict, trends: dict, diagnosis: dict, output_dir: str):
    """生成所有输出文件"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. health_report.md
    report = f"""# 太极OS 健康报告

**生成时间：** {now}
**健康分数：** {diagnosis['health_score']}/100 ({diagnosis['health_status']})

---

## L1 Runtime — 运行时状态

| 指标 | 值 |
|------|-----|
| Agent 总数 | {runtime['total_agents']} |
| 可调度 Agent | {runtime['schedulable_agents']} |
| 活跃可路由 | {runtime['active_routable']} ({runtime['active_pct']}%) |
| Shadow | {runtime['shadow']} |
| Disabled | {runtime['disabled']} |
| 从未触发 | {runtime['idle_never_triggered']} |
| 队列总数 | {runtime['queue_total']} |
| 最近心跳 | {runtime['heartbeat_last']} |

### Agent 分桶

"""
    for bucket, agents in runtime["buckets"].items():
        if agents:
            report += f"**{bucket}** ({len(agents)}):\n"
            for a in agents[:10]:
                report += f"- {a}\n"
            if len(agents) > 10:
                report += f"- ...and {len(agents) - 10} more\n"
            report += "\n"

    report += f"""## L2 Incident — 事件记录

**总失败数：** {incidents['total_failures']}
**总告警数：** {incidents['total_alerts']}

### 最近失败

"""
    for f in incidents["recent_failures"][:5]:
        report += f"- [{f['time'][:19]}] {f['agent_id']}: {f['error'][:100]}\n"

    if incidents["consecutive_failures"]:
        report += "\n### 连续失败 Agent\n\n"
        for agent, count in incidents["consecutive_failures"].items():
            report += f"- {agent}: {count} 次连续失败\n"

    report += f"""
## L3 Trend — 趋势分析

| 窗口 | 总数 | 成功 | 失败 | 成功率 |
|------|------|------|------|--------|
"""
    for window in ["24h", "7d", "30d"]:
        t = trends.get(window, {})
        report += f"| {window} | {t.get('total', 0)} | {t.get('completed', 0)} | {t.get('failed', 0)} | {t.get('success_rate', 0)}% |\n"

    report += f"""
## L4 Diagnosis — 诊断结论

**当前最弱链路：** {diagnosis['weakest_link']}
**最该优先修复：** {diagnosis['priority_fix']}
**修完后预期改善：** {diagnosis['expected_improvement']}

### 问题列表

"""
    for issue in diagnosis["issues"]:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
        report += f"{icon} **[{issue['severity'].upper()}] {issue['area']}**\n"
        report += f"  {issue['detail']}\n"
        report += f"  修复建议：{issue['fix']}\n\n"

    if not diagnosis["issues"]:
        report += "✅ 未发现需要关注的问题。\n"

    report += f"\n---\n*Generated by aios-health-monitor v1.0.0*\n"
    (out / "health_report.md").write_text(report, encoding="utf-8")

    # JSON 输出
    (out / "runtime.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2, default=list), encoding="utf-8")
    (out / "incidents.json").write_text(json.dumps(incidents, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "trends.json").write_text(json.dumps(trends, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "diagnosis.json").write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2), encoding="utf-8")

    return out


def main():
    parser = argparse.ArgumentParser(description="AIOS Health Monitor v1.0.0")
    parser.add_argument("--level", default="all", help="Report levels: L1,L2,L3,L4,all")
    parser.add_argument("--format", default="both", choices=["md", "json", "both"], help="Output format")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--quiet", action="store_true", help="Only output diagnosis conclusion")
    args = parser.parse_args()

    print("🏥 AIOS Health Monitor v1.0.0")
    print(f"  📂 Data: {DATA_DIR}")

    # 加载数据
    agents_data = load_json(DATA_DIR / "agents.json")
    task_queue = load_jsonl(DATA_DIR / "task_queue.jsonl")
    executions = load_jsonl(DATA_DIR / "task_executions.jsonl")
    alerts = load_jsonl(DATA_DIR / "alerts.jsonl") + load_jsonl(DATA_DIR / "skill_failure_alerts.jsonl")
    heartbeat_stats = load_json(DATA_DIR / "heartbeat_stats.json")

    print(f"  📊 {len(agents_data.get('agents', []))} agents, {len(executions)} executions, {len(alerts)} alerts")

    # 四层分析
    runtime = analyze_runtime(agents_data, task_queue, heartbeat_stats)
    incidents = analyze_incidents(executions, alerts)
    trends = analyze_trends(executions)
    diagnosis = diagnose(runtime, incidents, trends)

    if args.quiet:
        print(f"\n{'='*50}")
        print(f"健康分数: {diagnosis['health_score']}/100 ({diagnosis['health_status']})")
        print(f"当前最弱链路: {diagnosis['weakest_link']}")
        print(f"最该优先修复: {diagnosis['priority_fix']}")
        print(f"修完后预期改善: {diagnosis['expected_improvement']}")
        print(f"{'='*50}")
        return

    # 生成报告
    out = generate_reports(runtime, incidents, trends, diagnosis, args.output)

    # 输出摘要
    status_icon = {"GOOD": "🟢", "WARNING": "🟡", "CRITICAL": "🔴"}.get(diagnosis["health_status"], "⚪")
    print(f"\n{status_icon} Health: {diagnosis['health_score']}/100 ({diagnosis['health_status']})")
    print(f"  当前最弱链路: {diagnosis['weakest_link']}")
    print(f"  最该优先修复: {diagnosis['priority_fix']}")
    print(f"  修完后预期改善: {diagnosis['expected_improvement']}")
    print(f"\n  📁 Reports saved to: {out}")


if __name__ == "__main__":
    main()
