#!/usr/bin/env python3
"""
AIOS Runtime Observer - 48h Observation Mode
观察系统运行节奏，不做任何策略调整。

输出指标（Day3 交付给珊瑚海）：
  records, top_hexagrams, top_transitions,
  stability_index, entropy, transition_entropy

数据源：pattern_history.jsonl + task_executions.jsonl
"""
import json
import math
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path(__file__).parent
HISTORY = BASE / "data" / "pattern_history.jsonl"
EXECUTIONS = BASE / "task_executions.jsonl"
OBS_LOG = BASE / "reports" / "runtime_observations.jsonl"


def load_records():
    """加载卦象历史"""
    if not HISTORY.exists():
        return []
    with open(HISTORY, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_executions(hours=72):
    """加载最近N小时的任务执行记录"""
    if not EXECUTIONS.exists():
        return []
    cutoff = datetime.now().timestamp() - hours * 3600
    records = []
    with open(EXECUTIONS, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            ts = r.get("timestamp", 0)
            if ts > cutoff:
                records.append(r)
    return records


def shannon_entropy(counts: dict) -> float:
    """计算 Shannon 熵"""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def compute_hexagram_distribution(records):
    """卦象分布"""
    return Counter(r.get("pattern", "unknown") for r in records)


def compute_transitions(records):
    """计算卦象转换序列"""
    transitions = Counter()
    for i in range(1, len(records)):
        prev = records[i - 1].get("pattern", "?")
        curr = records[i].get("pattern", "?")
        transitions[f"{prev}→{curr}"] += 1
    return transitions


def compute_stability_index(records):
    """稳定性指数 = 最频繁卦象占比"""
    if not records:
        return 0.0
    dist = compute_hexagram_distribution(records)
    most_common_count = dist.most_common(1)[0][1]
    return round(most_common_count / len(records) * 100, 1)


def detect_anomalous_transitions(transitions):
    """检测异常跳跃（跨层转换）"""
    # 正常路径层级：坤(稳定) → 兑(协作) → 震(增长) → 离(高能) → 坎(风险)
    layer = {"坤卦": 0, "兑卦": 1, "震卦": 2, "离卦": 3, "坎卦": 4, "大过卦": 5}
    anomalies = []
    for t, count in transitions.items():
        parts = t.split("→")
        if len(parts) == 2:
            src = layer.get(parts[0], -1)
            dst = layer.get(parts[1], -1)
            if src >= 0 and dst >= 0 and abs(dst - src) > 2:
                anomalies.append({"transition": t, "count": count, "gap": abs(dst - src)})
    return anomalies


def observe():
    """执行一次观察，返回完整指标"""
    records = load_records()
    executions = load_executions(hours=72)

    hex_dist = compute_hexagram_distribution(records)
    transitions = compute_transitions(records)
    stability = compute_stability_index(records)
    hex_entropy = shannon_entropy(dict(hex_dist))
    trans_entropy = shannon_entropy(dict(transitions))
    anomalies = detect_anomalous_transitions(transitions)

    # 任务统计
    total_tasks = len(executions)
    success_tasks = sum(
        1 for e in executions
        if e.get("result", {}).get("success", False)
    )
    success_rate = round(success_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0.0

    # Top 排序
    top_hex = hex_dist.most_common(5)
    top_trans = transitions.most_common(5)

    # 判断 dominant hexagram 占比是否 > 40%（珊瑚海的稳定标准）
    dominant_pct = top_hex[0][1] / len(records) * 100 if records and top_hex else 0
    system_stable = dominant_pct > 40

    # 熵趋势（和上次观察对比）
    prev = load_previous_observation()
    entropy_trend = "unknown"
    trans_entropy_trend = "unknown"
    if prev:
        prev_e = prev.get("entropy", 0)
        prev_te = prev.get("transition_entropy", 0)
        if hex_entropy < prev_e - 0.05:
            entropy_trend = "↓ converging"
        elif hex_entropy > prev_e + 0.05:
            entropy_trend = "↑ diverging"
        else:
            entropy_trend = "≈ stable"
        if trans_entropy < prev_te - 0.05:
            trans_entropy_trend = "↓ converging"
        elif trans_entropy > prev_te + 0.05:
            trans_entropy_trend = "↑ diverging"
        else:
            trans_entropy_trend = "≈ stable"

    observation = {
        "timestamp": datetime.now().isoformat(),
        "records": len(records),
        "top_hexagrams": {h: c for h, c in top_hex},
        "top_transitions": {t: c for t, c in top_trans},
        "stability_index": stability,
        "entropy": hex_entropy,
        "transition_entropy": trans_entropy,
        "entropy_trend": entropy_trend,
        "trans_entropy_trend": trans_entropy_trend,
        "dominant_hexagram": top_hex[0][0] if top_hex else "none",
        "dominant_pct": round(dominant_pct, 1),
        "system_stable": system_stable,
        "anomalous_transitions": anomalies,
        "task_stats": {
            "total_72h": total_tasks,
            "success_rate": success_rate,
        },
    }

    # 保存观察记录
    save_observation(observation)
    return observation


def load_previous_observation():
    """加载上一次观察"""
    if not OBS_LOG.exists():
        return None
    with open(OBS_LOG, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def save_observation(obs):
    """追加观察记录"""
    OBS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OBS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(obs, ensure_ascii=False) + "\n")


def format_report(obs):
    """格式化为可读报告"""
    lines = []
    lines.append(f"═══ AIOS Runtime Observation ═══")
    lines.append(f"Time: {obs['timestamp']}")
    lines.append(f"Records: {obs['records']}")
    lines.append("")

    lines.append("📊 Hexagram Distribution:")
    for h, c in obs["top_hexagrams"].items():
        pct = c / obs["records"] * 100 if obs["records"] > 0 else 0
        bar = "█" * int(pct / 5)
        lines.append(f"  {h}: {c} ({pct:.0f}%) {bar}")

    lines.append("")
    lines.append("🔄 Top Transitions:")
    for t, c in obs["top_transitions"].items():
        lines.append(f"  {t}: {c}")

    lines.append("")
    lines.append(f"📈 Stability Index: {obs['stability_index']}%")
    lines.append(f"📉 Entropy: {obs['entropy']} ({obs['entropy_trend']})")
    lines.append(f"📉 Transition Entropy: {obs['transition_entropy']} ({obs['trans_entropy_trend']})")
    lines.append(f"🏠 Dominant: {obs['dominant_hexagram']} ({obs['dominant_pct']}%)")
    lines.append(f"✅ System Stable: {obs['system_stable']}")

    if obs["anomalous_transitions"]:
        lines.append("")
        lines.append("⚠️ Anomalous Transitions:")
        for a in obs["anomalous_transitions"]:
            lines.append(f"  {a['transition']} x{a['count']} (gap={a['gap']})")

    lines.append("")
    lines.append(f"📋 Tasks (72h): {obs['task_stats']['total_72h']} | Success: {obs['task_stats']['success_rate']}%")
    lines.append("═══════════════════════════════")
    return "\n".join(lines)


if __name__ == "__main__":
    obs = observe()
    print(format_report(obs))
