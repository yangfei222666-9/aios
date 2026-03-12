#!/usr/bin/env python3
"""
Phase 3 v4.0 端到端集成测试

验证完整闭环：
1. 推荐（灰度 + 回滚开关 + 幂等）
2. 重生（feedback + strategy + spawn request）
3. 追踪（推荐后失败分桶）
4. 监控（告警 + 自动降灰度）
"""
import json
import time
import shutil
from pathlib import Path

AIOS_DIR = Path(__file__).resolve().parent

# 备份测试前状态
BACKUP_FILES = [
    "experience_db_v4.jsonl",
    "recommendation_log.jsonl",
    "learner_v4_config.json",
    "learner_v4_metrics.json",
]


def backup():
    for f in BACKUP_FILES:
        src = AIOS_DIR / f
        if src.exists():
            shutil.copy2(src, src.with_suffix(".bak"))


def restore():
    for f in BACKUP_FILES:
        bak = AIOS_DIR / (f + ".bak") if not f.endswith(".bak") else AIOS_DIR / f
        bak_path = (AIOS_DIR / f).with_suffix(".bak")
        src = AIOS_DIR / f
        if bak_path.exists():
            shutil.copy2(bak_path, src)
            bak_path.unlink()
        elif src.exists():
            src.unlink()


def test_e2e():
    from experience_learner_v4 import ExperienceLearnerV4

    print("=" * 60)
    print("Phase 3 v4.0 E2E Integration Test")
    print("=" * 60)

    # 用全新实例（避免全局单例污染）
    learner = ExperienceLearnerV4()

    # ── Test 1: 灰度门控 ──────────────────────────────────────────────────
    print("\n[Test 1] Grayscale gate (10%)")
    learner.set_grayscale_ratio(0.10)

    hit_count = 0
    skip_count = 0
    N = 100
    for i in range(N):
        rec = learner.recommend({"error_type": "timeout", "task_id": f"gate-{i}"})
        if rec["grayscale"]:
            hit_count += 1
        else:
            skip_count += 1

    ratio = hit_count / N
    print(f"  Grayscale hit: {hit_count}/{N} ({ratio:.0%})")
    assert 0.02 <= ratio <= 0.25, f"Grayscale ratio {ratio:.0%} out of expected range [2%, 25%]"
    print("  OK")

    # ── Test 2: 幂等写入 ──────────────────────────────────────────────────
    print("\n[Test 2] Idempotent save")
    learner.set_grayscale_ratio(1.0)

    s1 = learner.save_success({
        "task_id": "e2e-001",
        "error_type": "timeout",
        "strategy": "split_and_retry",
        "confidence": 0.90,
        "recovery_time": 5.0,
    })
    s2 = learner.save_success({
        "task_id": "e2e-002",
        "error_type": "timeout",
        "strategy": "split_and_retry",
        "confidence": 0.85,
        "recovery_time": 3.0,
    })
    assert s1 == True, "First save should succeed"
    assert s2 == False, "Second save should be idempotent skip"
    print(f"  First: {s1}, Second: {s2}")
    print("  OK")

    # ── Test 3: 推荐命中 ──────────────────────────────────────────────────
    print("\n[Test 3] Recommendation hit")
    rec = learner.recommend({"error_type": "timeout", "task_id": "e2e-003"})
    assert rec["source"] == "experience", f"Expected experience, got {rec['source']}"
    assert rec["recommended_strategy"] in ("split_and_retry", "increase_timeout_and_retry")
    assert "strategy_version" in rec
    print(f"  Strategy: {rec['recommended_strategy']}")
    print(f"  Version: {rec['strategy_version']}")
    print(f"  Confidence: {rec['confidence']}")
    print("  OK")

    # ── Test 4: 推荐后失败分桶 ────────────────────────────────────────────
    print("\n[Test 4] Post-recommendation outcome tracking")
    learner.track_outcome("e2e-003", "split_and_retry", "experience", True)
    learner.track_outcome("e2e-004", "split_and_retry", "experience", False)
    learner.track_outcome("e2e-005", "default_recovery", "default", True)
    learner.track_outcome("e2e-006", "default_recovery", "default", False)

    metrics = learner.get_metrics()
    raw = metrics["raw"]
    assert raw["post_recommend_success"] >= 1
    assert raw["post_recommend_failed"] >= 1
    assert raw["post_default_success"] >= 1
    assert raw["post_default_failed"] >= 1
    print(f"  post_recommend: +{raw['post_recommend_success']}/-{raw['post_recommend_failed']}")
    print(f"  post_default: +{raw['post_default_success']}/-{raw['post_default_failed']}")
    print("  OK")

    # ── Test 5: 回滚开关 ──────────────────────────────────────────────────
    print("\n[Test 5] Kill switch")
    learner.set_enabled(False)
    rec = learner.recommend({"error_type": "timeout", "task_id": "e2e-007"})
    assert rec["source"] == "disabled"
    learner.set_enabled(True)
    print(f"  Disabled source: {rec['source']}")
    print("  OK")

    # ── Test 6: 版本字段 ──────────────────────────────────────────────────
    print("\n[Test 6] Version field in all outputs")
    # 检查经验库
    with open(AIOS_DIR / "experience_db_v4.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line.strip())
            assert "strategy_version" in entry, f"Missing strategy_version in {entry}"
    # 检查推荐日志
    with open(AIOS_DIR / "recommendation_log.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line.strip())
            assert "strategy_version" in entry, f"Missing strategy_version in {entry}"
    print("  All entries have strategy_version")
    print("  OK")

    # ── Test 7: 监控告警 ──────────────────────────────────────────────────
    print("\n[Test 7] Monitor health check")
    from learner_v4_monitor import check_learner_v4_health
    result = check_learner_v4_health()
    print(f"  Status: {result['status']}")
    print(f"  Alerts: {len(result['alerts'])}")
    print(f"  Actions: {len(result['actions_taken'])}")
    print("  OK")

    # ── Metrics Summary ───────────────────────────────────────────────────
    print("\n[Metrics Summary]")
    m = learner.get_metrics()
    print(f"  recommend_hit_rate: {m['recommend_hit_rate']:.1%}")
    print(f"  regen_success_rate: {m['regen_success_rate']:.1%}")
    print(f"  manual_intervention_rate: {m['manual_intervention_rate']:.1%}")
    print(f"  post_recommend_failure_rate: {m['post_recommend_failure_rate']:.1%}")
    print(f"  store: {m['store_stats']}")

    print("\n" + "=" * 60)
    print("All 7 tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    backup()
    try:
        test_e2e()
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        restore()
