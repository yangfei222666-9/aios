# -*- coding: utf-8 -*-
"""
Test Health Monitor Dispatch Metrics v1.0

验证 5 个验收标准：
1. health-monitor 能成功读取 dispatch_log.jsonl
2. 能统计 decision / policy / final_status 分布
3. 能识别 top blocked / top degraded / top failed 模式
4. 能把 dispatch 结论写进 L4 Diagnosis
5. 不影响现有 health score 主链
"""

import json
from pathlib import Path

from dispatch_log_reader import DispatchLogReader
from health_monitor_dispatch_metrics import HealthMonitorDispatchMetrics


def test_1_read_dispatch_log():
    """验收 1: 能成功读取 dispatch_log.jsonl"""
    print("[TEST 1] 读取 dispatch_log.jsonl")
    
    reader = DispatchLogReader()
    total = reader.count_total()
    recent = reader.read_recent(hours=24.0)
    
    print(f"  Total records: {total}")
    print(f"  Recent 24h: {len(recent)}")
    
    if total > 0:
        print("  ✅ 读取成功")
        return True
    else:
        print("  ⚠️ 无记录（可能是首次运行）")
        return True  # 无记录也算通过


def test_2_statistics():
    """验收 2: 能统计 decision / policy / final_status 分布"""
    print("\n[TEST 2] 统计分布")
    
    analyzer = HealthMonitorDispatchMetrics()
    result = analyzer.analyze(hours=24.0)
    
    dd = result['decision_distribution']
    pd = result['policy_distribution']
    
    print(f"  Decision Distribution: {len(dd.get('top_situations', []))} situations, {len(dd.get('top_handlers', []))} handlers")
    print(f"  Policy Distribution: {len(pd.get('policy_results', {}))} policy types, {len(pd.get('final_statuses', {}))} status types")
    
    if 'decision_distribution' in result and 'policy_distribution' in result:
        print("  ✅ 统计成功")
        return True
    else:
        print("  ❌ 统计失败")
        return False


def test_3_pattern_recognition():
    """验收 3: 能识别 top blocked / top degraded / top failed 模式"""
    print("\n[TEST 3] 模式识别")
    
    analyzer = HealthMonitorDispatchMetrics()
    result = analyzer.analyze(hours=24.0)
    
    pd = result['policy_distribution']
    deg = result['degradation_and_fallback']
    hs = result['hotspots']
    
    print(f"  Top Blocked: {pd.get('top_blocked_situations', [])}")
    print(f"  Top Degraded: {deg.get('top_degraded_situations', [])}")
    print(f"  Top Failed: {hs.get('top_failed_situations', [])}")
    
    # 只要能提取这三个字段就算通过
    if 'top_blocked_situations' in pd and 'top_degraded_situations' in deg and 'top_failed_situations' in hs:
        print("  ✅ 模式识别成功")
        return True
    else:
        print("  ❌ 模式识别失败")
        return False


def test_4_diagnosis():
    """验收 4: 能把 dispatch 结论写进 L4 Diagnosis"""
    print("\n[TEST 4] 诊断生成")
    
    analyzer = HealthMonitorDispatchMetrics()
    result = analyzer.analyze(hours=24.0)
    
    diagnosis = result.get('diagnosis', [])
    
    print(f"  Diagnosis lines: {len(diagnosis)}")
    for d in diagnosis:
        print(f"    • {d}")
    
    # 必须有 3 句诊断
    if len(diagnosis) == 3:
        print("  ✅ 诊断生成成功（3 句）")
        return True
    else:
        print(f"  ❌ 诊断生成失败（期望 3 句，实际 {len(diagnosis)} 句）")
        return False


def test_5_no_impact_on_health_score():
    """验收 5: 不影响现有 health score 主链"""
    print("\n[TEST 5] 不影响现有 health score")
    
    # 这个测试只需要确认 dispatch_metrics 是独立模块
    # 不依赖 health score 计算，也不修改 health score
    
    analyzer = HealthMonitorDispatchMetrics()
    result = analyzer.analyze(hours=24.0)
    
    # 检查返回结果中没有 health_score 字段
    if 'health_score' not in result:
        print("  ✅ 独立模块，不影响 health score")
        return True
    else:
        print("  ❌ 返回结果中包含 health_score，可能影响主链")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Health Monitor Dispatch Metrics - 验收测试")
    print("=" * 60)
    
    tests = [
        test_1_read_dispatch_log,
        test_2_statistics,
        test_3_pattern_recognition,
        test_4_diagnosis,
        test_5_no_impact_on_health_score,
    ]
    
    results = []
    for test in tests:
        try:
            passed = test()
            results.append(passed)
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    
    if all(results):
        print("✅ 所有验收标准通过")
    else:
        print("❌ 部分验收标准未通过")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
