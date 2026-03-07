#!/usr/bin/env python3
"""
Memory Retrieval Gate - 标准化判定函数 v1.0

输入字段、判定顺序、冲突优先级全部可复现、可审计。

Gate 判定流程：
  1. 样本量检查（硬门槛）
  2. 性能指标检查（p50/p95/p99 latency）
  3. 命中率检查（hit rate）
  4. 质量检查（helpfulness feedback）
  5. 稳定性检查（latency 突刺保护）
  6. 综合判定（GO / HOLD / ROLLBACK）

防误判三件套：
  A. helpfulness 最小样本门槛：feedback < 30/天 → INFO，不参与 phase 判定
  B. success rate delta 置信保护：enabled/disabled 任一组 < 20 → 不出结论
  C. 异常突刺保护：单日全绿但 p99 异常升高 → WARN

作者：小九 | 版本：v1.0
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
TZ = timezone(timedelta(hours=8))


# ═══════════════════════════════════════════════════════════════════════════
# Gate 配置（所有阈值集中管理）
# ═══════════════════════════════════════════════════════════════════════════

GATE_CONFIG = {
    # ── 配置版本 ──
    "gate_config_version": "1.0.0",   # 配置版本号（用于回溯审计）
    
    # ── 样本量门槛 ──
    "min_total_feedback": 100,        # GO 判定最低 feedback 总量
    "min_daily_feedback_for_phase": 30,  # 防误判A：低于此值 helpfulness 只标 INFO
    "min_group_sample_for_delta": 20,    # 防误判B：enabled/disabled 任一组低于此值不出结论

    # ── 性能指标（ms）──
    "p50_latency_max_ms": 200,        # p50 上限
    "p95_latency_max_ms": 500,        # p95 上限
    "p99_latency_max_ms": 1000,       # p99 上限
    "p99_spike_ratio": 3.0,           # 防误判C：p99 > p95 * ratio → WARN

    # ── 命中率 ──
    "hit_rate_min": 0.60,             # 最低命中率

    # ── 质量（helpfulness）──
    "helpfulness_min": 0.55,          # 平均 helpfulness 下限
    "helpfulness_positive_ratio": 0.60,  # 正面反馈占比下限

    # ── 稳定性 ──
    "latency_cv_max": 0.30,           # 变异系数上限（std/mean）
    "consecutive_green_days": 3,      # GO 需要连续绿灯天数

    # ── 综合判定 ──
    "rollback_triggers": 2,           # 累计 FAIL 指标数 >= 此值 → ROLLBACK
}


# ═══════════════════════════════════════════════════════════════════════════
# 数据采集
# ═══════════════════════════════════════════════════════════════════════════

def collect_metrics(date_str: Optional[str] = None) -> dict:
    """
    从各数据源采集当日指标。
    返回标准化 metrics dict。
    """
    if date_str is None:
        date_str = datetime.now(TZ).strftime("%Y-%m-%d")

    metrics = {
        "date": date_str,
        "collected_at": datetime.now(TZ).isoformat(),
        "performance": _collect_performance(date_str),
        "hit_rate": _collect_hit_rate(date_str),
        "quality": _collect_quality(date_str),
        "stability": _collect_stability(date_str),
    }
    return metrics


def _collect_performance(date_str: str) -> dict:
    """从 memory_retrieval_log.jsonl 采集延迟分位数"""
    log_path = BASE_DIR / "memory_retrieval_log.jsonl"
    latencies = []

    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                except Exception:
                    continue
                ts = rec.get("timestamp", "")
                if ts.startswith(date_str):
                    lat = rec.get("latency_ms") or rec.get("elapsed_ms")
                    if lat is not None:
                        latencies.append(float(lat))

    if not latencies:
        return {"p50": None, "p95": None, "p99": None, "count": 0, "latencies": []}

    latencies.sort()
    n = len(latencies)
    return {
        "p50": latencies[int(n * 0.50)],
        "p95": latencies[int(min(n - 1, n * 0.95))],
        "p99": latencies[int(min(n - 1, n * 0.99))],
        "mean": sum(latencies) / n,
        "count": n,
        "latencies": latencies,  # 保留原始数据供稳定性分析
    }


def _collect_hit_rate(date_str: str) -> dict:
    """从 memory_retrieval_log.jsonl 采集命中率"""
    log_path = BASE_DIR / "memory_retrieval_log.jsonl"
    total = 0
    hits = 0

    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line.strip())
                except Exception:
                    continue
                ts = rec.get("timestamp", "")
                if ts.startswith(date_str):
                    total += 1
                    # hit = 返回了有效结果
                    result_count = rec.get("result_count", rec.get("hits", 0))
                    if result_count and result_count > 0:
                        hits += 1

    rate = hits / total if total > 0 else None
    return {"total_queries": total, "hits": hits, "rate": rate}


def _collect_quality(date_str: str) -> dict:
    """从 feedback_log.jsonl + memory server feedback 采集质量指标"""
    # 尝试多个 feedback 来源
    feedback_sources = [
        BASE_DIR / "reports" / "feedback_log.jsonl",
        BASE_DIR / "feedback_log.jsonl",
        BASE_DIR / "data" / "learning" / "feedback_log.jsonl",
    ]

    feedbacks_today = []
    for src in feedback_sources:
        if src.exists():
            with open(src, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                    except Exception:
                        continue
                    ts = rec.get("timestamp", "")
                    if ts.startswith(date_str):
                        feedbacks_today.append(rec)

    total = len(feedbacks_today)
    positive = sum(1 for f in feedbacks_today if f.get("helpful", f.get("type") == "positive"))
    helpfulness_scores = [
        f.get("helpfulness", 0.5)
        for f in feedbacks_today
        if "helpfulness" in f
    ]
    avg_helpfulness = (
        sum(helpfulness_scores) / len(helpfulness_scores)
        if helpfulness_scores
        else None
    )
    positive_ratio = positive / total if total > 0 else None

    return {
        "feedback_count": total,
        "positive_count": positive,
        "positive_ratio": positive_ratio,
        "avg_helpfulness": avg_helpfulness,
    }


def _collect_stability(date_str: str) -> dict:
    """计算延迟稳定性（变异系数）"""
    perf = _collect_performance(date_str)
    latencies = perf.get("latencies", [])

    if len(latencies) < 5:
        return {"cv": None, "std": None, "mean": None, "sample_size": len(latencies)}

    mean = sum(latencies) / len(latencies)
    variance = sum((x - mean) ** 2 for x in latencies) / len(latencies)
    std = variance ** 0.5
    cv = std / mean if mean > 0 else None

    return {"cv": round(cv, 4) if cv else None, "std": round(std, 2), "mean": round(mean, 2), "sample_size": len(latencies)}


# ═══════════════════════════════════════════════════════════════════════════
# 单项检查（每项返回 PASS / WARN / FAIL / INFO）
# ═══════════════════════════════════════════════════════════════════════════

def check_performance(metrics: dict) -> dict:
    """检查延迟指标"""
    perf = metrics["performance"]
    cfg = GATE_CONFIG

    if perf["count"] == 0:
        return {"status": "INFO", "reason": "无性能数据", "details": perf}

    issues = []
    if perf["p50"] is not None and perf["p50"] > cfg["p50_latency_max_ms"]:
        issues.append(f"p50={perf['p50']:.0f}ms > {cfg['p50_latency_max_ms']}ms")
    if perf["p95"] is not None and perf["p95"] > cfg["p95_latency_max_ms"]:
        issues.append(f"p95={perf['p95']:.0f}ms > {cfg['p95_latency_max_ms']}ms")
    if perf["p99"] is not None and perf["p99"] > cfg["p99_latency_max_ms"]:
        issues.append(f"p99={perf['p99']:.0f}ms > {cfg['p99_latency_max_ms']}ms")

    if issues:
        return {"status": "FAIL", "reason": "; ".join(issues), "details": perf}
    return {"status": "PASS", "reason": "延迟正常", "details": perf}


def check_hit_rate(metrics: dict) -> dict:
    """检查命中率"""
    hr = metrics["hit_rate"]
    cfg = GATE_CONFIG

    if hr["total_queries"] == 0:
        return {"status": "INFO", "reason": "无查询数据", "details": hr}

    if hr["rate"] is not None and hr["rate"] < cfg["hit_rate_min"]:
        return {
            "status": "FAIL",
            "reason": f"命中率 {hr['rate']:.1%} < {cfg['hit_rate_min']:.0%}",
            "details": hr,
        }
    return {"status": "PASS", "reason": f"命中率 {hr['rate']:.1%}", "details": hr}


def check_quality(metrics: dict) -> dict:
    """
    检查质量（含防误判A：最小样本门槛）
    feedback < min_daily_feedback_for_phase → INFO，不参与 phase 判定
    """
    q = metrics["quality"]
    cfg = GATE_CONFIG

    if q["feedback_count"] == 0:
        return {"status": "INFO", "reason": "无反馈数据", "details": q, "participates_in_phase": False}

    # 防误判A：样本不足只标 INFO
    if q["feedback_count"] < cfg["min_daily_feedback_for_phase"]:
        return {
            "status": "INFO",
            "reason": f"反馈样本 {q['feedback_count']} < {cfg['min_daily_feedback_for_phase']}（不参与 phase 判定）",
            "details": q,
            "participates_in_phase": False,
        }

    issues = []
    if q["avg_helpfulness"] is not None and q["avg_helpfulness"] < cfg["helpfulness_min"]:
        issues.append(f"avg_helpfulness={q['avg_helpfulness']:.2f} < {cfg['helpfulness_min']}")
    if q["positive_ratio"] is not None and q["positive_ratio"] < cfg["helpfulness_positive_ratio"]:
        issues.append(f"positive_ratio={q['positive_ratio']:.1%} < {cfg['helpfulness_positive_ratio']:.0%}")

    if issues:
        return {"status": "FAIL", "reason": "; ".join(issues), "details": q, "participates_in_phase": True}
    return {"status": "PASS", "reason": "质量达标", "details": q, "participates_in_phase": True}


def check_spike(metrics: dict) -> dict:
    """
    防误判C：异常突刺保护
    单日全绿但 p99 > p95 * spike_ratio → WARN
    """
    perf = metrics["performance"]
    cfg = GATE_CONFIG

    if perf["p95"] is None or perf["p99"] is None:
        return {"status": "INFO", "reason": "数据不足，无法检测突刺", "details": {}}

    ratio = perf["p99"] / perf["p95"] if perf["p95"] > 0 else 0
    if ratio > cfg["p99_spike_ratio"]:
        return {
            "status": "WARN",
            "reason": f"p99/p95 = {ratio:.1f}x > {cfg['p99_spike_ratio']}x（异常突刺）",
            "details": {"p95": perf["p95"], "p99": perf["p99"], "ratio": round(ratio, 2)},
        }
    return {"status": "PASS", "reason": f"p99/p95 = {ratio:.1f}x 正常", "details": {"ratio": round(ratio, 2)}}


def check_stability(metrics: dict) -> dict:
    """检查延迟稳定性"""
    stab = metrics["stability"]
    cfg = GATE_CONFIG

    if stab["cv"] is None:
        return {"status": "INFO", "reason": f"样本不足 ({stab['sample_size']})", "details": stab}

    if stab["cv"] > cfg["latency_cv_max"]:
        return {
            "status": "WARN",
            "reason": f"CV={stab['cv']:.2f} > {cfg['latency_cv_max']}（延迟波动大）",
            "details": stab,
        }
    return {"status": "PASS", "reason": f"CV={stab['cv']:.2f} 稳定", "details": stab}


def check_success_rate_delta(
    enabled_success: float,
    disabled_success: float,
    enabled_count: int,
    disabled_count: int,
) -> dict:
    """
    防误判B：success rate delta 置信保护
    enabled/disabled 任一组样本 < min_group_sample_for_delta → 不出结论
    """
    cfg = GATE_CONFIG

    if enabled_count < cfg["min_group_sample_for_delta"] or disabled_count < cfg["min_group_sample_for_delta"]:
        return {
            "status": "INFO",
            "reason": (
                f"样本不足（enabled={enabled_count}, disabled={disabled_count}，"
                f"需各 >= {cfg['min_group_sample_for_delta']}）"
            ),
            "delta": None,
            "conclusion": "INSUFFICIENT_DATA",
        }

    delta = enabled_success - disabled_success
    return {
        "status": "PASS" if delta >= 0 else "WARN",
        "reason": f"delta = {delta:+.1f}%（enabled={enabled_success:.1f}%, disabled={disabled_success:.1f}%）",
        "delta": round(delta, 2),
        "conclusion": "POSITIVE" if delta > 0 else ("NEUTRAL" if delta == 0 else "NEGATIVE"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 综合 Gate 判定
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_gate(metrics: dict, history: Optional[list] = None) -> dict:
    """
    综合 Gate 判定。

    判定顺序（优先级从高到低）：
      1. ROLLBACK：FAIL 数 >= rollback_triggers
      2. HOLD：任何 FAIL 或 WARN，或总 feedback < min_total_feedback
      3. GO：所有 PASS + 连续 green days 达标 + feedback >= 100

    冲突优先级：ROLLBACK > HOLD > GO

    返回：
      {
        "decision": "GO" | "HOLD" | "ROLLBACK",
        "reasons": [...],
        "checks": {...},
        "gate_config": {...},
        "timestamp": "..."
      }
    """
    cfg = GATE_CONFIG

    checks = {
        "performance": check_performance(metrics),
        "hit_rate": check_hit_rate(metrics),
        "quality": check_quality(metrics),
        "spike": check_spike(metrics),
        "stability": check_stability(metrics),
    }

    reasons = []
    fail_count = 0
    warn_count = 0
    info_count = 0

    for name, result in checks.items():
        status = result["status"]
        if status == "FAIL":
            fail_count += 1
            reasons.append(f"[FAIL] {name}: {result['reason']}")
        elif status == "WARN":
            warn_count += 1
            reasons.append(f"[WARN] {name}: {result['reason']}")
        elif status == "INFO":
            info_count += 1
            reasons.append(f"[INFO] {name}: {result['reason']}")
        else:
            reasons.append(f"[PASS] {name}: {result['reason']}")

    # 总 feedback 检查
    total_feedback = _count_total_feedback()
    if total_feedback < cfg["min_total_feedback"]:
        reasons.append(
            f"[HOLD] 总 feedback {total_feedback} < {cfg['min_total_feedback']}（样本不足）"
        )

    # 连续绿灯天数
    green_days = _count_consecutive_green_days(history or [])

    # ── 判定（优先级：ROLLBACK > HOLD > GO）──
    decision = "GO"

    # ROLLBACK
    if fail_count >= cfg["rollback_triggers"]:
        decision = "ROLLBACK"
        reasons.insert(0, f"⛔ ROLLBACK: {fail_count} 项 FAIL >= {cfg['rollback_triggers']}")

    # HOLD
    elif fail_count > 0 or warn_count > 0 or total_feedback < cfg["min_total_feedback"]:
        decision = "HOLD"
        if fail_count > 0:
            reasons.insert(0, f"⏸️ HOLD: {fail_count} 项 FAIL")
        elif warn_count > 0:
            reasons.insert(0, f"⏸️ HOLD: {warn_count} 项 WARN")
        elif total_feedback < cfg["min_total_feedback"]:
            reasons.insert(0, f"⏸️ HOLD: feedback 不足 ({total_feedback}/{cfg['min_total_feedback']})")

    # GO
    else:
        if green_days < cfg["consecutive_green_days"]:
            decision = "HOLD"
            reasons.insert(0, f"⏸️ HOLD: 连续绿灯 {green_days}天 < {cfg['consecutive_green_days']}天")
        else:
            reasons.insert(0, f"✅ GO: 所有指标达标，连续 {green_days} 天绿灯")

    result = {
        "decision": decision,
        "reasons": reasons,
        "checks": checks,
        "summary": {
            "fail_count": fail_count,
            "warn_count": warn_count,
            "info_count": info_count,
            "total_feedback": total_feedback,
            "green_days": green_days,
        },
        "gate_config": cfg,
        "timestamp": datetime.now(TZ).isoformat(),
    }

    # 持久化
    _save_gate_result(result)

    return result


def _count_total_feedback() -> int:
    """统计所有 feedback 总量"""
    total = 0
    sources = [
        BASE_DIR / "reports" / "feedback_log.jsonl",
        BASE_DIR / "feedback_log.jsonl",
        BASE_DIR / "data" / "learning" / "feedback_log.jsonl",
    ]
    seen_ids = set()
    for src in sources:
        if src.exists():
            with open(src, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                        rid = rec.get("record_id") or rec.get("lesson_id") or line.strip()
                        if rid not in seen_ids:
                            seen_ids.add(rid)
                            total += 1
                    except Exception:
                        continue
    return total


def _count_consecutive_green_days(history: list) -> int:
    """从历史 gate 结果中计算连续绿灯天数"""
    if not history:
        # 尝试从文件加载
        gate_log = REPORTS_DIR / "gate_history.jsonl"
        if gate_log.exists():
            with open(gate_log, "r", encoding="utf-8") as f:
                history = []
                for line in f:
                    try:
                        history.append(json.loads(line.strip()))
                    except Exception:
                        continue

    if not history:
        return 0

    # 从最近往前数连续 PASS（无 FAIL/WARN）的天数
    count = 0
    for entry in reversed(history):
        checks = entry.get("checks", {})
        has_issue = any(
            c.get("status") in ("FAIL", "WARN")
            for c in checks.values()
            if isinstance(c, dict)
        )
        if has_issue:
            break
        count += 1

    return count


def _save_gate_result(result: dict):
    """保存 gate 判定结果"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 追加到历史
    gate_log = REPORTS_DIR / "gate_history.jsonl"
    with open(gate_log, "a", encoding="utf-8") as f:
        # 写入精简版（不含 latencies 原始数据，但保留 gate_config_version）
        slim = {
            "decision": result["decision"],
            "reasons": result["reasons"][:5],  # 最多 5 条
            "summary": result["summary"],
            "timestamp": result["timestamp"],
            "gate_config_version": result.get("gate_config", {}).get("gate_config_version", "unknown"),
            "checks": {
                k: {"status": v["status"], "reason": v["reason"]}
                for k, v in result["checks"].items()
            },
        }
        f.write(json.dumps(slim, ensure_ascii=False) + "\n")

    # 最新结果
    latest_path = REPORTS_DIR / "gate_latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        # 移除 latencies 原始数据避免文件过大
        clean = json.loads(json.dumps(result, default=str))
        if "performance" in clean.get("checks", {}):
            details = clean["checks"]["performance"].get("details", {})
            details.pop("latencies", None)
        json.dump(clean, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# Telegram 摘要生成（含 Gate 理由）
# ═══════════════════════════════════════════════════════════════════════════

def format_gate_telegram(result: dict) -> str:
    """生成 Telegram 友好的 Gate 摘要"""
    decision = result["decision"]
    summary = result["summary"]
    reasons = result["reasons"]
    cfg_version = result.get("gate_config", {}).get("gate_config_version", "unknown")

    icon = {"GO": "✅", "HOLD": "⏸️", "ROLLBACK": "⛔"}.get(decision, "❓")

    lines = [
        f"{icon} Memory Gate: {decision}",
        f"🔖 Config: v{cfg_version} | {result.get('timestamp', '')[:10]}",
        f"📊 FAIL:{summary['fail_count']} WARN:{summary['warn_count']} INFO:{summary['info_count']}",
        f"📝 Feedback: {summary['total_feedback']}/100 | Green days: {summary['green_days']}/3",
        "",
        "Gate 理由：",
    ]

    for r in reasons[:6]:
        lines.append(f"  {r}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "evaluate"
    date_str = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "evaluate":
        print("=" * 60)
        print("  Memory Retrieval Gate Evaluation")
        print("=" * 60)

        metrics = collect_metrics(date_str)
        result = evaluate_gate(metrics)

        print(f"\n📅 Date: {metrics['date']}")
        print(f"🔍 Decision: {result['decision']}")
        print(f"\n📋 Checks:")
        for name, check in result["checks"].items():
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(check["status"], "?")
            print(f"  {icon} {name}: {check['reason']}")

        print(f"\n📊 Summary:")
        s = result["summary"]
        print(f"  FAIL: {s['fail_count']} | WARN: {s['warn_count']} | INFO: {s['info_count']}")
        print(f"  Total feedback: {s['total_feedback']}")
        print(f"  Green days: {s['green_days']}")

        print(f"\n{'=' * 60}")
        print(f"  Gate Decision: {result['decision']}")
        print(f"{'=' * 60}")

        # 打印 Telegram 摘要
        print(f"\n--- Telegram Summary ---")
        print(format_gate_telegram(result))

    elif cmd == "config":
        print(json.dumps(GATE_CONFIG, indent=2))

    elif cmd == "history":
        gate_log = REPORTS_DIR / "gate_history.jsonl"
        if gate_log.exists():
            with open(gate_log, "r", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line.strip())
                    print(f"  {rec['timestamp']} | {rec['decision']} | "
                          f"FAIL:{rec['summary']['fail_count']} WARN:{rec['summary']['warn_count']}")
        else:
            print("  No gate history yet.")

    elif cmd == "delta":
        # 手动测试 success rate delta
        # 用法: python memory_gate.py delta <enabled_sr> <disabled_sr> <enabled_n> <disabled_n>
        if len(sys.argv) >= 6:
            r = check_success_rate_delta(
                float(sys.argv[2]), float(sys.argv[3]),
                int(sys.argv[4]), int(sys.argv[5]),
            )
            print(f"  Status: {r['status']}")
            print(f"  Reason: {r['reason']}")
            print(f"  Conclusion: {r['conclusion']}")
        else:
            print("Usage: python memory_gate.py delta <enabled_sr> <disabled_sr> <enabled_n> <disabled_n>")

    else:
        print("Usage: python memory_gate.py [evaluate|config|history|delta]")


if __name__ == "__main__":
    main()
