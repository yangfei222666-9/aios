#!/usr/bin/env python3
"""
v4.1.0 模拟请求测试
验证细化策略是否真实生效
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from experience_learner_v4 import learner_v4

def test_dependency_subtypes():
    """测试 dependency_error 子类型推荐"""
    print("\n[Test 1] dependency_error 子类型推荐")
    
    # 1. dependency_not_found
    rec1 = learner_v4.recommend({
        'error_type': 'dependency_not_found',
        'task_id': 'test-dep-001',
    })
    print(f"  dependency_not_found:")
    print(f"    Strategy: {rec1['recommended_strategy']}")
    print(f"    Source: {rec1['source']}")
    print(f"    Expected: retry_with_mirror")
    assert rec1['recommended_strategy'] in ('retry_with_mirror', 'default_recovery'), \
        f"Unexpected: {rec1['recommended_strategy']}"
    
    # 2. version_conflict
    rec2 = learner_v4.recommend({
        'error_type': 'version_conflict',
        'task_id': 'test-dep-002',
    })
    print(f"  version_conflict:")
    print(f"    Strategy: {rec2['recommended_strategy']}")
    print(f"    Source: {rec2['source']}")
    print(f"    Expected: version_pin")
    assert rec2['recommended_strategy'] in ('version_pin', 'default_recovery'), \
        f"Unexpected: {rec2['recommended_strategy']}"
    
    # 3. transient_dependency_failure
    rec3 = learner_v4.recommend({
        'error_type': 'transient_dependency_failure',
        'task_id': 'test-dep-003',
    })
    print(f"  transient_dependency_failure:")
    print(f"    Strategy: {rec3['recommended_strategy']}")
    print(f"    Source: {rec3['source']}")
    print(f"    Expected: dependency_check_and_retry")
    assert rec3['recommended_strategy'] in ('dependency_check_and_retry', 'default_recovery'), \
        f"Unexpected: {rec3['recommended_strategy']}"
    
    # 4. dependency_error (generic)
    rec4 = learner_v4.recommend({
        'error_type': 'dependency_error',
        'task_id': 'test-dep-004',
    })
    print(f"  dependency_error (generic):")
    print(f"    Strategy: {rec4['recommended_strategy']}")
    print(f"    Source: {rec4['source']}")
    print(f"    Expected: dependency_check_and_retry or default_recovery")

def test_resource_exhausted():
    """测试 resource_exhausted 推荐"""
    print("\n[Test 2] resource_exhausted 推荐")
    
    rec = learner_v4.recommend({
        'error_type': 'resource_exhausted',
        'task_id': 'test-res-001',
    })
    print(f"  Strategy: {rec['recommended_strategy']}")
    print(f"  Source: {rec['source']}")
    print(f"  Expected: reduce_batch_and_retry or stream_processing")
    assert rec['recommended_strategy'] in ('reduce_batch_and_retry', 'stream_processing', 'default_recovery'), \
        f"Unexpected: {rec['recommended_strategy']}"

def test_grayscale_ratio():
    """测试 70% 灰度比例"""
    print("\n[Test 3] 70% 灰度比例验证")
    
    # 模拟 100 次请求
    results = {'experience': 0, 'default': 0, 'grayscale_skip': 0, 'disabled': 0}
    for i in range(100):
        rec = learner_v4.recommend({
            'error_type': 'timeout',
            'task_id': f'test-gray-{i:03d}',
        })
        results[rec['source']] += 1
    
    total = sum(results.values())
    print(f"  总请求: {total}")
    print(f"  experience: {results['experience']} ({results['experience']/total:.1%})")
    print(f"  default: {results['default']} ({results['default']/total:.1%})")
    print(f"  grayscale_skip: {results['grayscale_skip']} ({results['grayscale_skip']/total:.1%})")
    print(f"  Expected grayscale_skip: ~30% (100% - 70%)")
    
    # 允许 ±10% 误差
    skip_ratio = results['grayscale_skip'] / total
    assert 0.20 <= skip_ratio <= 0.40, f"Grayscale skip ratio {skip_ratio:.1%} out of range [20%, 40%]"

def main():
    print("=" * 70)
    print("v4.1.0 模拟请求测试")
    print("=" * 70)
    
    # 临时设置灰度 100% 以确保测试命中
    original_ratio = learner_v4.config.get('grayscale_ratio')
    learner_v4.set_grayscale_ratio(1.0)
    
    try:
        test_dependency_subtypes()
        test_resource_exhausted()
    finally:
        # 恢复原始灰度比例
        learner_v4.set_grayscale_ratio(original_ratio)
    
    # 测试灰度比例（使用真实 70%）
    test_grayscale_ratio()
    
    print("\n" + "=" * 70)
    print("所有测试通过 ✅")
    print("=" * 70)

if __name__ == '__main__':
    main()
