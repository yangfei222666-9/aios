#!/usr/bin/env python3
"""
AIOS Runtime Observer - 48h Observation Mode
瑙傚療绯荤粺杩愯鑺傚锛屼笉鍋氫换浣曠瓥鐣ヨ皟鏁淬€?
杈撳嚭鎸囨爣锛圖ay3 浜や粯缁欑強鐟氭捣锛夛細
  records, top_hexagrams, top_transitions,
  stability_index, entropy, transition_entropy

鏁版嵁婧愶細pattern_history.jsonl + task_executions_v2.jsonl
"""
import json
import math
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path(__file__).parent
HISTORY = BASE / "data" / "pattern_history.jsonl"
EXECUTIONS = BASE / "task_executions_v2.jsonl"
OBS_LOG = BASE / "reports" / "runtime_observations.jsonl"


def load_records():
    """鍔犺浇鍗﹁薄鍘嗗彶"""
    if not HISTORY.exists():
        return []
    with open(HISTORY, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_executions(hours=72):
    """鍔犺浇鏈€杩慛灏忔椂鐨勪换鍔℃墽琛岃褰?""
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
    """璁＄畻 Shannon 鐔?""
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
    """鍗﹁薄鍒嗗竷"""
    return Counter(r.get("pattern", "unknown") for r in records)


def compute_transitions(records):
    """璁＄畻鍗﹁薄杞崲搴忓垪"""
    transitions = Counter()
    for i in range(1, len(records)):
        prev = records[i - 1].get("pattern", "?")
        curr = records[i].get("pattern", "?")
        transitions[f"{prev}鈫抺curr}"] += 1
    return transitions


def compute_stability_index(records):
    """绋冲畾鎬ф寚鏁?= 鏈€棰戠箒鍗﹁薄鍗犳瘮"""
    if not records:
        return 0.0
    dist = compute_hexagram_distribution(records)
    most_common_count = dist.most_common(1)[0][1]
    return round(most_common_count / len(records) * 100, 1)


def detect_anomalous_transitions(transitions):
    """妫€娴嬪紓甯歌烦璺冿紙璺ㄥ眰杞崲锛?""
    # 姝ｅ父璺緞灞傜骇锛氬潳(绋冲畾) 鈫?鍏?鍗忎綔) 鈫?闇?澧為暱) 鈫?绂?楂樿兘) 鈫?鍧?椋庨櫓)
    layer = {"鍧ゅ崷": 0, "鍏戝崷": 1, "闇囧崷": 2, "绂诲崷": 3, "鍧庡崷": 4, "澶ц繃鍗?: 5}
    anomalies = []
    for t, count in transitions.items():
        parts = t.split("鈫?)
        if len(parts) == 2:
            src = layer.get(parts[0], -1)
            dst = layer.get(parts[1], -1)
            if src >= 0 and dst >= 0 and abs(dst - src) > 2:
                anomalies.append({"transition": t, "count": count, "gap": abs(dst - src)})
    return anomalies


def observe():
    """鎵ц涓€娆¤瀵燂紝杩斿洖瀹屾暣鎸囨爣"""
    records = load_records()
    executions = load_executions(hours=72)

    hex_dist = compute_hexagram_distribution(records)
    transitions = compute_transitions(records)
    stability = compute_stability_index(records)
    hex_entropy = shannon_entropy(dict(hex_dist))
    trans_entropy = shannon_entropy(dict(transitions))
    anomalies = detect_anomalous_transitions(transitions)

    # 浠诲姟缁熻
    total_tasks = len(executions)
    success_tasks = sum(
        1 for e in executions
        if e.get("result", {}).get("success", False)
    )
    success_rate = round(success_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0.0

    # Top 鎺掑簭
    top_hex = hex_dist.most_common(5)
    top_trans = transitions.most_common(5)

    # 鍒ゆ柇 dominant hexagram 鍗犳瘮鏄惁 > 40%锛堢強鐟氭捣鐨勭ǔ瀹氭爣鍑嗭級
    dominant_pct = top_hex[0][1] / len(records) * 100 if records and top_hex else 0
    system_stable = dominant_pct > 40

    # 鐔佃秼鍔匡紙鍜屼笂娆¤瀵熷姣旓級
    prev = load_previous_observation()
    entropy_trend = "unknown"
    trans_entropy_trend = "unknown"
    if prev:
        prev_e = prev.get("entropy", 0)
        prev_te = prev.get("transition_entropy", 0)
        if hex_entropy < prev_e - 0.05:
            entropy_trend = "鈫?converging"
        elif hex_entropy > prev_e + 0.05:
            entropy_trend = "鈫?diverging"
        else:
            entropy_trend = "鈮?stable"
        if trans_entropy < prev_te - 0.05:
            trans_entropy_trend = "鈫?converging"
        elif trans_entropy > prev_te + 0.05:
            trans_entropy_trend = "鈫?diverging"
        else:
            trans_entropy_trend = "鈮?stable"

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

    # 淇濆瓨瑙傚療璁板綍
    save_observation(observation)
    return observation


def load_previous_observation():
    """鍔犺浇涓婁竴娆¤瀵?""
    if not OBS_LOG.exists():
        return None
    with open(OBS_LOG, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def save_observation(obs):
    """杩藉姞瑙傚療璁板綍"""
    OBS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OBS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(obs, ensure_ascii=False) + "\n")


def format_report(obs):
    """鏍煎紡鍖栦负鍙鎶ュ憡"""
    lines = []
    lines.append(f"鈺愨晲鈺?AIOS Runtime Observation 鈺愨晲鈺?)
    lines.append(f"Time: {obs['timestamp']}")
    lines.append(f"Records: {obs['records']}")
    lines.append("")

    lines.append("馃搳 Hexagram Distribution:")
    for h, c in obs["top_hexagrams"].items():
        pct = c / obs["records"] * 100 if obs["records"] > 0 else 0
        bar = "鈻? * int(pct / 5)
        lines.append(f"  {h}: {c} ({pct:.0f}%) {bar}")

    lines.append("")
    lines.append("馃攧 Top Transitions:")
    for t, c in obs["top_transitions"].items():
        lines.append(f"  {t}: {c}")

    lines.append("")
    lines.append(f"馃搱 Stability Index: {obs['stability_index']}%")
    lines.append(f"馃搲 Entropy: {obs['entropy']} ({obs['entropy_trend']})")
    lines.append(f"馃搲 Transition Entropy: {obs['transition_entropy']} ({obs['trans_entropy_trend']})")
    lines.append(f"馃彔 Dominant: {obs['dominant_hexagram']} ({obs['dominant_pct']}%)")
    lines.append(f"鉁?System Stable: {obs['system_stable']}")

    if obs["anomalous_transitions"]:
        lines.append("")
        lines.append("鈿狅笍 Anomalous Transitions:")
        for a in obs["anomalous_transitions"]:
            lines.append(f"  {a['transition']} x{a['count']} (gap={a['gap']})")

    lines.append("")
    lines.append(f"馃搵 Tasks (72h): {obs['task_stats']['total_72h']} | Success: {obs['task_stats']['success_rate']}%")
    lines.append("鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?)
    return "\n".join(lines)


if __name__ == "__main__":
    obs = observe()
    print(format_report(obs))

