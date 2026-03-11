#!/usr/bin/env python3
"""
Agent Performance Analyzer v1.0.0
从"Agent 在不在"升级到"Agent 是否有价值、是否退化、是否该保持待命"。
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data")


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


# 高价值 Agent 组（即使 idle 也应保留）
HIGH_VALUE_GROUPS = {"dispatcher", "core"}
# 应急备用角色关键词
EMERGENCY_KEYWORDS = ["security", "audit", "backup", "restore", "emergency", "recovery"]


def classify_agent(agent: dict, exec_history: dict) -> dict:
    """对单个 Agent 进行分类和评分"""
    name = agent.get("name", "")
    enabled = agent.get("enabled", True)
    mode = agent.get("mode", "active")
    routable = agent.get("routable", False)
    lifecycle = agent.get("lifecycle_state", "active")
    group = agent.get("group", "")
    role = agent.get("role", "")
    stats = agent.get("stats", {})
    total = stats.get("tasks_total", 0)
    completed = stats.get("tasks_completed", 0)
    failed = stats.get("tasks_failed", 0)
    success_rate = stats.get("success_rate", 0)
    production_ready = agent.get("production_ready", False)

    # 从执行历史获取更多信息
    agent_execs = exec_history.get(name, [])
    recent_execs = [e for e in agent_execs if _is_recent(e, days=7)]
    last_active = _get_last_active(agent_execs)

    # 连续失败检测
    consecutive_failures = _count_consecutive_failures(agent_execs)

    # ─── 分类逻辑 ───

    # 1. Shadow（最高优先级判定）
    if not enabled or mode == "shadow" or lifecycle == "shadow":
        category = "shadow"
        action = "保留 shadow"
        reason = "已被标记为 shadow/disabled"

    # 2. Disabled
    elif mode == "disabled" or lifecycle == "disabled":
        category = "shadow"  # 归入 shadow 桶
        action = "保留 disabled"
        reason = "已被禁用"

    # 3. Degraded（连续失败 >= 3 或成功率 < 50% 且有足够样本）
    elif consecutive_failures >= 3:
        category = "degraded"
        action = "需要修复"
        reason = f"连续失败 {consecutive_failures} 次"

    elif total >= 5 and success_rate < 50:
        category = "degraded"
        action = "需要修复"
        reason = f"成功率仅 {success_rate}%（{completed}/{total}）"

    # 4. Active Routable（有执行记录且可路由）
    elif routable and total > 0:
        category = "active_routable"
        action = "继续运行"
        reason = f"活跃，成功率 {success_rate}%"

    # 5. Standby Emergency（从未触发但属于应急类）
    elif total == 0 and any(kw in role.lower() or kw in name.lower() for kw in EMERGENCY_KEYWORDS):
        category = "standby_emergency"
        action = "保留待命"
        reason = "应急备用角色，无需频繁触发"

    # 6. Schedulable Idle（可调度但从未触发）
    elif routable and total == 0:
        if group in HIGH_VALUE_GROUPS:
            category = "schedulable_idle"
            action = "保留待命"
            reason = f"高价值组 ({group})，等待触发"
        else:
            category = "schedulable_idle"
            action = "继续观察"
            reason = "从未触发，评估是否需要保留"

    # 7. 其他
    else:
        category = "schedulable_idle"
        action = "继续观察"
        reason = "状态不明确"

    return {
        "name": name,
        "role": role,
        "group": group,
        "category": category,
        "enabled": enabled,
        "routable": routable,
        "production_ready": production_ready,
        "stats": {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "success_rate": success_rate,
            "recent_7d": len(recent_execs),
            "consecutive_failures": consecutive_failures,
        },
        "last_active": last_active,
        "action": action,
        "reason": reason,
    }


def _is_recent(execution: dict, days: int = 7) -> bool:
    ts_str = execution.get("start_time", "")
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return ts >= datetime.now(timezone.utc) - timedelta(days=days)
    except (ValueError, AttributeError):
        return False


def _get_last_active(executions: list) -> str | None:
    if not executions:
        return None
    latest = max(executions, key=lambda e: e.get("start_time", ""), default=None)
    return latest.get("start_time") if latest else None


def _count_consecutive_failures(executions: list) -> int:
    if not executions:
        return 0
    sorted_execs = sorted(executions, key=lambda e: e.get("start_time", ""), reverse=True)
    count = 0
    for e in sorted_execs:
        if e.get("status") == "failed":
            count += 1
        else:
            break
    return count


def analyze(agents_data: dict, executions: list) -> dict:
    """分析所有 Agent"""
    # 按 agent_id 分组执行记录
    exec_by_agent = defaultdict(list)
    for ex in executions:
        aid = ex.get("agent_id", "")
        exec_by_agent[aid].append(ex)

    agents = agents_data.get("agents", [])
    scorecards = []
    categories = defaultdict(list)

    for agent in agents:
        card = classify_agent(agent, exec_by_agent)
        scorecards.append(card)
        categories[card["category"]].append(card["name"])

    # 识别特殊列表
    underused = [c for c in scorecards if c["category"] == "schedulable_idle" and c["routable"]]
    degraded = [c for c in scorecards if c["category"] == "degraded"]

    return {
        "scorecards": scorecards,
        "categories": dict(categories),
        "underused": underused,
        "degraded": degraded,
        "summary": {
            "total": len(agents),
            "active_routable": len(categories.get("active_routable", [])),
            "schedulable_idle": len(categories.get("schedulable_idle", [])),
            "standby_emergency": len(categories.get("standby_emergency", [])),
            "shadow": len(categories.get("shadow", [])),
            "degraded": len(categories.get("degraded", [])),
        },
    }


def generate_reports(result: dict, output_dir: str):
    """生成报告"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = result["summary"]

    # 1. agent_performance_report.md
    md = f"""# Agent Performance Report

**分析时间：** {now}
**Agent 总数：** {summary['total']}

## 分类概览

| 类别 | 数量 | 说明 |
|------|------|------|
| active_routable | {summary['active_routable']} | 活跃可路由 |
| schedulable_idle | {summary['schedulable_idle']} | 可调度但从未触发 |
| standby_emergency | {summary['standby_emergency']} | 应急备用 |
| shadow | {summary['shadow']} | Shadow/Disabled |
| degraded | {summary['degraded']} | 退化需关注 |

## 详细评分卡

| Agent | 类别 | 成功率 | 总任务 | 近7天 | 建议 |
|-------|------|--------|--------|-------|------|
"""
    for card in sorted(result["scorecards"], key=lambda c: (
        {"active_routable": 0, "degraded": 1, "schedulable_idle": 2, "standby_emergency": 3, "shadow": 4}.get(c["category"], 9)
    )):
        md += f"| {card['name']} | {card['category']} | {card['stats']['success_rate']}% | {card['stats']['total_tasks']} | {card['stats']['recent_7d']} | {card['action']} |\n"

    if result["degraded"]:
        md += "\n## ⚠️ 退化 Agent\n\n"
        for d in result["degraded"]:
            md += f"- **{d['name']}**: {d['reason']}\n  建议: {d['action']}\n\n"

    if result["underused"]:
        md += "\n## 💤 低使用 Agent（可调度但从未触发）\n\n"
        for u in result["underused"]:
            md += f"- **{u['name']}** ({u['role']}): {u['reason']}\n  建议: {u['action']}\n\n"

    md += f"\n---\n*Generated by agent-performance-analyzer v1.0.0*\n"
    (out / "agent_performance_report.md").write_text(md, encoding="utf-8")

    # 2-4. JSON 输出
    (out / "agent_scorecard.json").write_text(
        json.dumps(result["scorecards"], ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "underused_agents.json").write_text(
        json.dumps(result["underused"], ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "degraded_agents.json").write_text(
        json.dumps(result["degraded"], ensure_ascii=False, indent=2), encoding="utf-8")

    return out


def main():
    parser = argparse.ArgumentParser(description="Agent Performance Analyzer v1.0.0")
    parser.add_argument("--source", default=str(DATA_DIR), help="Data source directory")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()

    source = Path(args.source)
    print("📊 Agent Performance Analyzer v1.0.0")
    print(f"  📂 Source: {source}")

    agents_data = load_json(source / "agents.json")
    executions = load_jsonl(source / "task_executions.jsonl")
    print(f"  📊 {len(agents_data.get('agents', []))} agents, {len(executions)} executions")

    result = analyze(agents_data, executions)
    out = generate_reports(result, args.output)

    s = result["summary"]
    print(f"\n📊 Results:")
    print(f"  🟢 Active Routable: {s['active_routable']}")
    print(f"  💤 Schedulable Idle: {s['schedulable_idle']}")
    print(f"  🛡️ Standby Emergency: {s['standby_emergency']}")
    print(f"  👻 Shadow/Disabled: {s['shadow']}")
    print(f"  ⚠️ Degraded: {s['degraded']}")
    print(f"\n  📁 Reports: {out}")


if __name__ == "__main__":
    main()
