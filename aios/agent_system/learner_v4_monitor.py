#!/usr/bin/env python3
"""
Learner v4 Monitor - 验收指标监控 + 每日简报集成

监控指标：
  1. recommend_hit_rate（推荐命中率）
  2. regen_success_rate（重生成功率）
  3. manual_intervention_rate（人工介入率）
  4. post_recommend_failure_rate（推荐后失败率）

告警阈值：
  - post_recommend_failure_rate > 30% → 自动降灰度到 0%
  - regen_success_rate < 50% → 告警
  - recommend_hit_rate < 5% 且 store > 10 entries → 告警
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_DIR = Path(__file__).resolve().parent
OBSERVATION_LOG = AIOS_DIR / "memory" / "observation_log.md"


def check_learner_v4_health() -> dict:
    """
    检查 Learner v4 健康度

    Returns:
        {
            "status": "ok" | "warning" | "critical",
            "metrics": dict,
            "alerts": list[str],
            "actions_taken": list[str],
        }
    """
    from experience_learner_v4 import learner_v4

    metrics = learner_v4.get_metrics()
    alerts = []
    actions = []

    # 1. 推荐后失败率 > 30% → 自动降灰度到 0%
    post_fail = metrics.get("post_recommend_failure_rate", 0)
    if post_fail > 0.30:
        alerts.append(f"post_recommend_failure_rate={post_fail:.1%} > 30%")
        learner_v4.set_grayscale_ratio(0.0)
        actions.append("Auto-disabled grayscale (ratio → 0%)")

    # 2. 重生成功率 < 50%
    regen_success = metrics.get("regen_success_rate", 1.0)
    raw = metrics.get("raw", {})
    regen_total = raw.get("regen_total", 0)
    if regen_total >= 5 and regen_success < 0.50:
        alerts.append(f"regen_success_rate={regen_success:.1%} < 50% (n={regen_total})")

    # 3. 推荐命中率过低（有足够经验但命中不了）
    hit_rate = metrics.get("recommend_hit_rate", 0)
    store = metrics.get("store_stats", {})
    if store.get("total_entries", 0) >= 10 and hit_rate < 0.05:
        alerts.append(f"recommend_hit_rate={hit_rate:.1%} < 5% (store={store['total_entries']})")

    status = "ok"
    if alerts:
        status = "critical" if actions else "warning"

    return {
        "status": status,
        "metrics": metrics,
        "alerts": alerts,
        "actions_taken": actions,
    }


def append_to_observation_log(metrics: dict):
    """追加到 observation_log.md"""
    OBSERVATION_LOG.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    hit = metrics.get("recommend_hit_rate", 0)
    regen = metrics.get("regen_success_rate", 0)
    post_fail = metrics.get("post_recommend_failure_rate", 0)
    store = metrics.get("store_stats", {})
    cfg = metrics.get("config", {})

    line = (
        f"| {now} | {hit:.1%} | {regen:.1%} | {post_fail:.1%} "
        f"| {store.get('total_entries', 0)} | {cfg.get('grayscale_ratio', 0):.0%} "
        f"| {cfg.get('strategy_version', '?')} |\n"
    )

    # 如果文件不存在或没有表头，先写表头
    header = "| Time | Hit Rate | Regen Success | Post-Rec Fail | Store | Grayscale | Version |\n"
    header += "|------|----------|---------------|---------------|-------|-----------|---------|\n"

    if not OBSERVATION_LOG.exists():
        with open(OBSERVATION_LOG, "w", encoding="utf-8") as f:
            f.write("# Learner v4 Observation Log\n\n")
            f.write(header)

    with open(OBSERVATION_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def run_learner_monitor():
    """运行监控（集成到每日简报 / Heartbeat）"""
    result = check_learner_v4_health()

    print(f"[LEARNER_MONITOR] Status: {result['status'].upper()}")
    m = result["metrics"]
    print(f"  Hit rate: {m.get('recommend_hit_rate', 0):.1%}")
    print(f"  Regen success: {m.get('regen_success_rate', 0):.1%}")
    print(f"  Post-rec fail: {m.get('post_recommend_failure_rate', 0):.1%}")
    print(f"  Store: {m.get('store_stats', {}).get('total_entries', 0)} entries")

    if result["alerts"]:
        for a in result["alerts"]:
            print(f"  ⚠️  {a}")
    if result["actions_taken"]:
        for a in result["actions_taken"]:
            print(f"  🔧 {a}")

    # 追加到观察日志
    append_to_observation_log(m)

    return result


if __name__ == "__main__":
    run_learner_monitor()
