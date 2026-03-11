#!/usr/bin/env python3
"""
Pattern Detector v1.0.0
从零散失败、重复现象、长期日志里识别"模式"，为 lesson 和 diagnosis 提供基础。

MVP 识别 4 类模式：timeout, network_error, resource_exhausted, agent_idle
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data")

# 模式类型定义
PATTERN_TYPES = {
    "timeout": {
        "keywords": ["timeout", "timed out", "timed_out", "deadline exceeded", "took too long"],
        "impact_base": "high",
    },
    "network_error": {
        "keywords": ["network", "connection", "econnrefused", "econnreset", "enotfound",
                      "socket", "dns", "ssl", "certificate", "fetch failed", "request failed"],
        "impact_base": "high",
    },
    "resource_exhausted": {
        "keywords": ["memory", "disk", "resource", "oom", "out of memory", "no space",
                      "quota", "limit exceeded", "rate limit"],
        "impact_base": "critical",
    },
    "agent_idle": {
        "keywords": [],  # 特殊处理：基于统计而非关键词
        "impact_base": "low",
    },
}


def parse_time_window(window: str) -> datetime:
    """解析时间窗口，返回起始时间"""
    now = datetime.now(timezone.utc)
    if window == "24h":
        return now - timedelta(hours=24)
    elif window == "7d":
        return now - timedelta(days=7)
    elif window == "30d":
        return now - timedelta(days=30)
    else:
        return now - timedelta(days=7)


def load_jsonl(filepath: Path) -> list:
    """加载 JSONL 文件"""
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


def load_json(filepath: Path) -> dict:
    """加载 JSON 文件"""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return {}


def classify_error(record: dict) -> str | None:
    """根据错误信息分类模式类型"""
    # 提取错误文本
    error_text = ""
    if isinstance(record.get("error"), str):
        error_text = record["error"].lower()
    elif isinstance(record.get("result"), dict):
        error_text = str(record["result"].get("error", "")).lower()
        error_text += " " + str(record["result"].get("output", "")).lower()

    status = str(record.get("status", "")).lower()
    if status == "failed" and not error_text:
        error_text = "failed"

    if not error_text and status != "failed":
        return None

    # 按关键词匹配
    for ptype, config in PATTERN_TYPES.items():
        if ptype == "agent_idle":
            continue
        for kw in config["keywords"]:
            if kw in error_text:
                return ptype

    # 如果是 failed 但没匹配到具体类型
    if status == "failed":
        return "unknown_failure"

    return None


def detect_idle_agents(agents_data: dict, executions: list) -> list:
    """检测从未触发的 Agent（排除 shadow/disabled）"""
    idle_agents = []
    agents = agents_data.get("agents", [])

    # 收集有执行记录的 agent
    active_agent_ids = set()
    for ex in executions:
        aid = ex.get("agent_id", "")
        active_agent_ids.add(aid)

    for agent in agents:
        name = agent.get("name", "")
        enabled = agent.get("enabled", True)
        mode = agent.get("mode", "active")
        routable = agent.get("routable", False)
        lifecycle = agent.get("lifecycle_state", "active")
        stats = agent.get("stats", {})
        total_tasks = stats.get("tasks_total", 0)

        # 跳过 shadow / disabled
        if not enabled or mode in ["shadow", "disabled"] or lifecycle in ["shadow", "disabled"]:
            continue

        # 从未执行过任务且不在执行记录中
        if total_tasks == 0 and name not in active_agent_ids:
            idle_agents.append({
                "agent": name,
                "role": agent.get("role", ""),
                "group": agent.get("group", ""),
                "routable": routable,
                "lifecycle_state": lifecycle,
            })

    return idle_agents


def cluster_patterns(executions: list, alerts: list, window_start: datetime) -> list:
    """聚类识别重复模式"""
    clusters = defaultdict(lambda: {
        "pattern_type": "",
        "affected_agents": set(),
        "affected_skills": set(),
        "frequency": 0,
        "first_seen": None,
        "last_seen": None,
        "evidence": [],
        "impact_level": "low",
    })

    # 处理执行记录
    for ex in executions:
        ptype = classify_error(ex)
        if not ptype or ptype == "unknown_failure":
            continue

        # 解析时间
        ts_str = ex.get("start_time") or ex.get("timestamp") or ex.get("end_time", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts < window_start:
                continue
        except (ValueError, AttributeError):
            pass

        cluster = clusters[ptype]
        cluster["pattern_type"] = ptype
        cluster["frequency"] += 1
        cluster["affected_agents"].add(ex.get("agent_id", "unknown"))

        task_type = ""
        if isinstance(ex.get("result"), dict):
            task_type = ex["result"].get("task_type", "")
        if task_type:
            cluster["affected_skills"].add(task_type)

        # 记录证据（最多 5 条）
        if len(cluster["evidence"]) < 5:
            evidence = f"task={ex.get('task_id', '?')}, agent={ex.get('agent_id', '?')}, status={ex.get('status', '?')}"
            cluster["evidence"].append(evidence)

        # 更新时间范围
        if ts_str:
            if cluster["first_seen"] is None or ts_str < cluster["first_seen"]:
                cluster["first_seen"] = ts_str
            if cluster["last_seen"] is None or ts_str > cluster["last_seen"]:
                cluster["last_seen"] = ts_str

    # 处理告警记录
    for alert in alerts:
        error_type = str(alert.get("error_type", "")).lower()
        ptype = None
        for pt, config in PATTERN_TYPES.items():
            if pt == "agent_idle":
                continue
            for kw in config["keywords"]:
                if kw in error_type:
                    ptype = pt
                    break
            if ptype:
                break

        if not ptype:
            continue

        cluster = clusters[ptype]
        cluster["pattern_type"] = ptype
        cluster["frequency"] += 1
        cluster["affected_skills"].add(alert.get("skill", "unknown"))

        if len(cluster["evidence"]) < 5:
            cluster["evidence"].append(
                f"alert: skill={alert.get('skill', '?')}, error={alert.get('error_type', '?')}"
            )

    # 设置 impact level
    for ptype, cluster in clusters.items():
        base = PATTERN_TYPES.get(ptype, {}).get("impact_base", "low")
        freq = cluster["frequency"]
        if freq >= 10:
            cluster["impact_level"] = "critical"
        elif freq >= 5:
            cluster["impact_level"] = "high"
        elif freq >= 2:
            cluster["impact_level"] = "medium"
        else:
            cluster["impact_level"] = base

    return clusters


def generate_fix_direction(ptype: str, cluster: dict) -> str:
    """生成候选修复方向"""
    directions = {
        "timeout": "增加超时时间、拆分大任务、检查外部依赖响应速度",
        "network_error": "检查网络连接、验证 API endpoint、添加重试机制",
        "resource_exhausted": "清理磁盘空间、增加内存限制、优化资源使用",
        "agent_idle": "检查触发条件是否正确、验证路由配置、考虑是否需要保留",
    }
    return directions.get(ptype, "需要人工分析")


def main():
    parser = argparse.ArgumentParser(description="Pattern Detector v1.0.0")
    parser.add_argument("--source", default=str(DATA_DIR), help="Data source directory")
    parser.add_argument("--window", default="7d", choices=["24h", "7d", "30d"], help="Time window")
    parser.add_argument("--top", type=int, default=3, help="Top N patterns to report")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()

    source = Path(args.source)
    window_start = parse_time_window(args.window)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"🔍 Pattern Detector v1.0.0")
    print(f"  📂 Source: {source}")
    print(f"  ⏰ Window: {args.window} (since {window_start.strftime('%Y-%m-%d %H:%M')} UTC)")

    # 加载数据
    executions = load_jsonl(source / "task_executions.jsonl")
    alerts = load_jsonl(source / "alerts.jsonl") + load_jsonl(source / "skill_failure_alerts.jsonl")
    agents_data = load_json(source / "agents.json")
    lessons = load_json(source / "lessons.json")

    print(f"  📊 Loaded: {len(executions)} executions, {len(alerts)} alerts, {len(agents_data.get('agents', []))} agents")

    # 聚类模式
    clusters = cluster_patterns(executions, alerts, window_start)

    # 检测 idle agents
    idle_agents = detect_idle_agents(agents_data, executions)
    if idle_agents:
        clusters["agent_idle"] = {
            "pattern_type": "agent_idle",
            "affected_agents": set(a["agent"] for a in idle_agents),
            "affected_skills": set(),
            "frequency": len(idle_agents),
            "first_seen": None,
            "last_seen": None,
            "evidence": [f"agent={a['agent']} ({a['role']}), routable={a['routable']}" for a in idle_agents[:5]],
            "impact_level": "low" if len(idle_agents) < 5 else "medium",
        }

    # 转换为输出格式
    pattern_list = []
    for i, (ptype, cluster) in enumerate(sorted(clusters.items(), key=lambda x: -x[1]["frequency"])):
        pattern_list.append({
            "pattern_id": f"pat-{ptype}-{i+1:03d}",
            "pattern_type": ptype,
            "affected_agents": sorted(cluster["affected_agents"]),
            "affected_skills": sorted(cluster["affected_skills"]),
            "frequency": cluster["frequency"],
            "first_seen": cluster["first_seen"],
            "last_seen": cluster["last_seen"],
            "evidence": cluster["evidence"],
            "impact_level": cluster["impact_level"],
            "candidate_fix_direction": generate_fix_direction(ptype, cluster),
        })

    # 1. pattern_clusters.json
    (out / "pattern_clusters.json").write_text(
        json.dumps(pattern_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 2. top_patterns.md
    top_n = pattern_list[:args.top]
    md = f"""# Pattern Detection Report

**检测时间：** {now}
**时间窗口：** {args.window}
**数据源：** {source}
**发现模式：** {len(pattern_list)} 个

## Top {args.top} 模式

"""
    for i, p in enumerate(top_n, 1):
        md += f"""### #{i} {p['pattern_type']} (频次: {p['frequency']}, 影响: {p['impact_level']})

**影响 Agent：** {', '.join(p['affected_agents']) or '无'}
**影响 Skill：** {', '.join(p['affected_skills']) or '无'}
**首次出现：** {p['first_seen'] or '未知'}
**最近出现：** {p['last_seen'] or '未知'}

**证据样本：**
"""
        for ev in p["evidence"][:3]:
            md += f"- {ev}\n"
        md += f"\n**建议修复方向：** {p['candidate_fix_direction']}\n\n---\n\n"

    if not top_n:
        md += "✅ 未发现显著重复模式。\n"

    (out / "top_patterns.md").write_text(md, encoding="utf-8")

    # 3. candidate_root_causes.json
    root_causes = []
    for p in pattern_list:
        if p["frequency"] >= 2:
            root_causes.append({
                "pattern_id": p["pattern_id"],
                "pattern_type": p["pattern_type"],
                "frequency": p["frequency"],
                "candidate_cause": generate_fix_direction(p["pattern_type"], p),
                "confidence": "high" if p["frequency"] >= 5 else "medium",
                "needs_investigation": p["impact_level"] in ["high", "critical"],
            })
    (out / "candidate_root_causes.json").write_text(
        json.dumps(root_causes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 输出摘要
    print(f"\n✅ Detection complete!")
    print(f"  📊 Found {len(pattern_list)} patterns")
    for p in top_n:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(p["impact_level"], "⚪")
        print(f"  {icon} {p['pattern_type']}: freq={p['frequency']}, impact={p['impact_level']}")
    if idle_agents:
        print(f"  💤 {len(idle_agents)} idle agents (never triggered, not shadow/disabled)")
    print(f"\n  📁 Reports saved to: {out}")


if __name__ == "__main__":
    main()
