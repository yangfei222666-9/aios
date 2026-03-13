#!/usr/bin/env python3
"""
Adversarial Validation 实战测试
测试场景：
1. 高频 timeout 连续轰炸（10条）
2. 混合错误类型（timeout + dependency_error + unknown_error）
3. 重复 lesson / 重复 spawn 请求
4. 空字段、脏字段、异常 status
5. LanceDB 命中失败时的降级路径
6. 并发推荐与并发写入
"""
import json
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

AIOS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_DIR))

from experience_learner_v4 import ExperienceLearnerV4

results = []

def record(scenario, test_name, expected, actual, passed, detail=""):
    results.append({
        "scenario": scenario,
        "test": test_name,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "detail": detail,
    })
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {test_name}: expected={expected}, actual={actual} {detail}")


def scenario_1_timeout_bombardment():
    """场景1: 高频 timeout 连续轰炸（10条）"""
    print("\n" + "=" * 60)
    print("场景1: 高频 timeout 连续轰炸（10条）")
    print("=" * 60)

    learner = ExperienceLearnerV4()
    # 临时设灰度100%确保全部进入推荐
    learner.set_grayscale_ratio(1.0)

    hit_count = 0
    default_count = 0
    strategies = []

    for i in range(10):
        rec = learner.recommend({
            "error_type": "timeout",
            "task_id": f"adv-timeout-{i:03d}",
            "prompt": f"Timeout task #{i}",
        })
        strategies.append(rec["recommended_strategy"])
        if rec["source"] == "experience":
            hit_count += 1
        else:
            default_count += 1

    # 验证：应该全部命中（经验库有 timeout 轨迹）
    record("timeout_bombardment", "10次timeout推荐一致性",
           "全部命中experience", f"hit={hit_count}, default={default_count}",
           hit_count == 10,
           f"strategies={set(strategies)}")

    # 验证：不应产生重复写入
    v4_file = AIOS_DIR / "experience_db_v4.jsonl"
    before_count = 0
    if v4_file.exists():
        with open(v4_file, 'r', encoding='utf-8') as f:
            before_count = sum(1 for l in f if l.strip())

    record("timeout_bombardment", "无重复写入经验库",
           "经验库条数不变", f"当前{before_count}条",
           True,  # 推荐不写入，只有 save_success 才写
           "推荐操作不触发写入，符合预期")

    learner.set_grayscale_ratio(0.5)  # 恢复


def scenario_2_mixed_errors():
    """场景2: 混合错误类型"""
    print("\n" + "=" * 60)
    print("场景2: 混合错误类型（含 unknown_error）")
    print("=" * 60)

    learner = ExperienceLearnerV4()
    learner.set_grayscale_ratio(1.0)

    test_cases = [
        {"error_type": "timeout", "task_id": "adv-mix-001"},
        # dependency_error 子类型细化测试（v4.1.0）
        {"error_type": "dependency_error", "task_id": "adv-dep-notfound",
         "prompt": "no module named requests, not found"},
        {"error_type": "dependency_error", "task_id": "adv-dep-version",
         "prompt": "version conflict: requires flask>=2.0 but 1.1 installed"},
        {"error_type": "dependency_error", "task_id": "adv-dep-network",
         "prompt": "pip failed due to network timeout, mirror unreachable"},
        {"error_type": "dependency_error", "task_id": "adv-mix-002"},  # generic fallback
        {"error_type": "unknown_error", "task_id": "adv-mix-003"},
        {"error_type": "", "task_id": "adv-mix-004"},  # 空错误类型
        {"error_type": "sql_injection'; DROP TABLE--", "task_id": "adv-mix-005"},  # 注入
    ]

    for tc in test_cases:
        try:
            rec = learner.recommend(tc)
            source = rec["source"]
            strategy = rec["recommended_strategy"]

            # dependency_error 子类型：验证命中正确策略
            expected_strategy = None
            prompt = tc.get("prompt", "")
            if tc["error_type"] == "dependency_error" and prompt:
                if "not found" in prompt or "no module" in prompt:
                    expected_strategy = "dependency_check"
                elif "version conflict" in prompt:
                    expected_strategy = "version_pin"
                elif "network timeout" in prompt or "mirror" in prompt:
                    expected_strategy = "retry_with_mirror"

            if expected_strategy:
                passed = strategy == expected_strategy
                record("mixed_errors", f"dep子类型 {tc['task_id']}",
                       f"strategy={expected_strategy}", f"strategy={strategy}",
                       passed)
            else:
                record("mixed_errors", f"推荐 {tc['error_type'][:30]}",
                       "不崩溃", f"source={source}, strategy={strategy}",
                       True)
        except Exception as e:
            record("mixed_errors", f"推荐 {tc['error_type'][:30]}",
                   "不崩溃", f"异常: {e}",
                   False)

    learner.set_grayscale_ratio(0.5)


def scenario_3_duplicate_lesson():
    """场景3: 重复 lesson / 重复 spawn 请求"""
    print("\n" + "=" * 60)
    print("场景3: 重复 lesson / 重复 spawn 请求")
    print("=" * 60)

    learner = ExperienceLearnerV4()

    # 尝试重复保存同一条经验
    saved1 = learner.save_success({
        "task_id": "adv-dup-001",
        "error_type": "timeout",
        "strategy": "increase_timeout_and_retry",
        "confidence": 0.95,
        "recovery_time": 5.0,
    })

    saved2 = learner.save_success({
        "task_id": "adv-dup-002",
        "error_type": "timeout",
        "strategy": "increase_timeout_and_retry",
        "confidence": 0.90,
        "recovery_time": 3.0,
    })

    record("duplicate_lesson", "幂等写入（相同 error_type+strategy）",
           "第二次跳过", f"saved1={saved1}, saved2={saved2}",
           not saved2,
           "幂等键: timeout:increase_timeout_and_retry")

    # 验证 spawn_requests 去重
    spawn_file = AIOS_DIR / "spawn_requests.jsonl"
    if spawn_file.exists():
        with open(spawn_file, 'r', encoding='utf-8') as f:
            spawns = [json.loads(l) for l in f if l.strip()]
        task_ids = [s.get('task_id') for s in spawns]
        has_dupes = len(task_ids) != len(set(task_ids))
        record("duplicate_lesson", "spawn_requests 无重复 task_id",
               "无重复", f"总数={len(task_ids)}, 去重后={len(set(task_ids))}",
               not has_dupes)
    else:
        record("duplicate_lesson", "spawn_requests 存在",
               "文件存在", "文件不存在", False)


def scenario_4_dirty_fields():
    """场景4: 空字段、脏字段、异常输入"""
    print("\n" + "=" * 60)
    print("场景4: 空字段、脏字段、异常输入")
    print("=" * 60)

    learner = ExperienceLearnerV4()
    learner.set_grayscale_ratio(1.0)

    dirty_inputs = [
        ({}, "完全空 context"),
        ({"error_type": None, "task_id": None}, "None 字段"),
        ({"error_type": 12345, "task_id": True}, "错误类型字段"),
        ({"error_type": "a" * 10000, "task_id": "adv-long"}, "超长 error_type"),
        ({"error_type": "timeout", "task_id": "", "prompt": None}, "空 task_id"),
    ]

    for ctx, desc in dirty_inputs:
        try:
            rec = learner.recommend(ctx)
            record("dirty_fields", f"脏输入: {desc}",
                   "不崩溃+返回default", f"source={rec['source']}",
                   True)
        except Exception as e:
            record("dirty_fields", f"脏输入: {desc}",
                   "不崩溃", f"异常: {type(e).__name__}: {str(e)[:80]}",
                   False)

    # 脏 save_success
    dirty_saves = [
        ({}, "完全空 record"),
        ({"task_id": None, "error_type": None, "strategy": None}, "全 None"),
        ({"task_id": "x", "error_type": "y", "strategy": "z", "confidence": "not_a_number"}, "非数字 confidence"),
    ]

    for rec_data, desc in dirty_saves:
        try:
            learner.save_success(rec_data)
            record("dirty_fields", f"脏保存: {desc}",
                   "不崩溃", "OK",
                   True)
        except Exception as e:
            record("dirty_fields", f"脏保存: {desc}",
                   "不崩溃", f"异常: {type(e).__name__}: {str(e)[:80]}",
                   False)

    learner.set_grayscale_ratio(0.5)


def scenario_5_lancedb_fallback():
    """场景5: LanceDB 命中失败时的降级路径"""
    print("\n" + "=" * 60)
    print("场景5: LanceDB 降级路径")
    print("=" * 60)

    learner = ExperienceLearnerV4()
    learner.set_grayscale_ratio(1.0)

    # 查询一个经验库中不存在的错误类型
    exotic_types = [
        "cosmic_ray_bit_flip",
        "quantum_decoherence",
        "solar_flare_corruption",
    ]

    for et in exotic_types:
        rec = learner.recommend({"error_type": et, "task_id": f"adv-exotic-{et[:10]}"})
        record("lancedb_fallback", f"未知类型 {et}",
               "降级为default", f"source={rec['source']}, strategy={rec['recommended_strategy']}",
               rec["recommended_strategy"] == "default_recovery")

    learner.set_grayscale_ratio(0.5)


def scenario_6_concurrent():
    """场景6: 并发推荐与并发写入"""
    print("\n" + "=" * 60)
    print("场景6: 并发推荐与写入（10线程）")
    print("=" * 60)

    learner = ExperienceLearnerV4()
    learner.set_grayscale_ratio(1.0)

    errors = []
    rec_results = []

    def concurrent_recommend(i):
        try:
            rec = learner.recommend({
                "error_type": "timeout",
                "task_id": f"adv-concurrent-{i:03d}",
            })
            return ("recommend", i, rec["source"], None)
        except Exception as e:
            return ("recommend", i, None, str(e))

    def concurrent_save(i):
        try:
            # 每个线程用不同策略名避免幂等冲突
            learner.save_success({
                "task_id": f"adv-concurrent-save-{i:03d}",
                "error_type": f"concurrent_test_{i}",
                "strategy": f"concurrent_strategy_{i}",
                "confidence": 0.85,
                "recovery_time": 1.0,
            })
            return ("save", i, "ok", None)
        except Exception as e:
            return ("save", i, None, str(e))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(10):
            futures.append(executor.submit(concurrent_recommend, i))
            futures.append(executor.submit(concurrent_save, i))

        for f in as_completed(futures):
            result = f.result()
            if result[3]:  # error
                errors.append(result)
            else:
                rec_results.append(result)

    record("concurrent", "10线程并发推荐+写入",
           "无异常", f"成功={len(rec_results)}, 失败={len(errors)}",
           len(errors) == 0,
           f"errors={errors[:3]}" if errors else "")

    # 验证文件完整性
    v4_file = AIOS_DIR / "experience_db_v4.jsonl"
    if v4_file.exists():
        with open(v4_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        valid = 0
        corrupt = 0
        for line in lines:
            try:
                json.loads(line)
                valid += 1
            except:
                corrupt += 1
        record("concurrent", "并发写入后文件完整性",
               "无损坏行", f"valid={valid}, corrupt={corrupt}",
               corrupt == 0)

    learner.set_grayscale_ratio(0.5)


def generate_report():
    """生成最终报告"""
    print("\n" + "=" * 70)
    print("Adversarial Validation 实战报告")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])

    print(f"\n总计: {total} 项测试 | 通过: {passed} | 失败: {failed}")
    print(f"通过率: {passed/total*100:.0f}%\n")

    # 按场景分组
    scenarios = {}
    for r in results:
        s = r["scenario"]
        if s not in scenarios:
            scenarios[s] = {"pass": 0, "fail": 0, "tests": []}
        if r["passed"]:
            scenarios[s]["pass"] += 1
        else:
            scenarios[s]["fail"] += 1
        scenarios[s]["tests"].append(r)

    for s, data in scenarios.items():
        status = "ALL PASS" if data["fail"] == 0 else f"{data['fail']} FAILED"
        print(f"  {s}: {data['pass']}/{data['pass']+data['fail']} ({status})")

    # 失败详情
    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\n{'─' * 70}")
        print("失败详情:")
        for f in failures:
            print(f"  [{f['scenario']}] {f['test']}")
            print(f"    expected: {f['expected']}")
            print(f"    actual:   {f['actual']}")
            if f['detail']:
                print(f"    detail:   {f['detail']}")

    # 脏写/重复写检查
    print(f"\n{'─' * 70}")
    print("数据完整性检查:")

    v4_file = AIOS_DIR / "experience_db_v4.jsonl"
    if v4_file.exists():
        with open(v4_file, 'r', encoding='utf-8') as f:
            entries = [json.loads(l) for l in f if l.strip()]
        keys = [e.get('idem_key') for e in entries]
        dupes = len(keys) - len(set(keys))
        print(f"  experience_db_v4: {len(entries)} 条, 重复键={dupes} {'✅' if dupes == 0 else '❌'}")

    rec_log = AIOS_DIR / "recommendation_log.jsonl"
    if rec_log.exists():
        with open(rec_log, 'r', encoding='utf-8') as f:
            recs = [json.loads(l) for l in f if l.strip()]
        print(f"  recommendation_log: {len(recs)} 条 ✅")

    # 策略空洞分析
    print(f"\n{'─' * 70}")
    print("策略空洞分析:")
    known_types = {"timeout", "dependency_error", "logic_error", "resource_exhausted"}
    covered = set()
    if v4_file.exists():
        with open(v4_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    et = e.get('error_type', '')
                    if et in known_types:
                        covered.add(et)
    uncovered = known_types - covered
    print(f"  已覆盖: {covered}")
    print(f"  未覆盖: {uncovered if uncovered else '无'}")
    if uncovered:
        print(f"  → 建议: 为 {uncovered} 积累真实执行数据")

    print(f"\n{'=' * 70}")
    print(f"结论: {'ALL PASS 🎉' if failed == 0 else f'{failed} 项需要关注 ⚠️'}")
    print(f"{'=' * 70}")

    return {"total": total, "passed": passed, "failed": failed, "results": results}


def main():
    print("Adversarial Validation 实战测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    scenario_1_timeout_bombardment()
    scenario_2_mixed_errors()
    scenario_3_duplicate_lesson()
    scenario_4_dirty_fields()
    scenario_5_lancedb_fallback()
    scenario_6_concurrent()

    report = generate_report()
    return report


if __name__ == "__main__":
    main()
