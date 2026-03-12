"""
Skill Router 测试
"""

import json
from pathlib import Path
from skill_router import SkillRouter
from skill_router_schema import TaskContext


def load_test_cases():
    """加载测试用例"""
    fixtures_path = Path(__file__).parent / "fixtures" / "router_cases.json"
    with open(fixtures_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_single_clear_match():
    """测试1: 单候选清晰命中"""
    print("\n=== 测试1: 单候选清晰命中 ===")
    
    router = SkillRouter()
    
    task_context = TaskContext(
        source="heartbeat",
        task_type="monitor",
        content="检查系统健康状态",
        priority="normal",
        risk_level="safe",
        system_state={"health_score": 85},
        recent_history=[],
        available_handlers=["aios-health-monitor"]
    )
    
    output = router.route(task_context)
    
    print(router.explain_decision(output))
    print(f"\n置信度: {output.confidence:.1f}")
    
    # 验证
    assert output.chosen_handler == "aios-health-monitor"
    assert output.confidence >= 80.0
    print("\n✅ 测试通过")


def test_multiple_candidates_conflict():
    """测试2: 多候选冲突"""
    print("\n=== 测试2: 多候选冲突 ===")
    
    router = SkillRouter()
    
    task_context = TaskContext(
        source="user",
        task_type="analysis",
        content="分析最近的失败模式",
        priority="high",
        risk_level="safe",
        system_state={"health_score": 75},
        recent_history=[],
        available_handlers=["pattern-detector", "agent-performance-analyzer", "lesson-extractor"]
    )
    
    output = router.route(task_context)
    
    print(router.explain_decision(output))
    print(f"\n置信度: {output.confidence:.1f}")
    print(f"备选: {', '.join(output.fallback_handlers)}")
    
    # 验证
    assert output.chosen_handler is not None
    assert len(output.candidates) >= 2
    assert len(output.fallback_handlers) >= 1
    print("\n✅ 测试通过")


def test_high_risk_routing():
    """测试3: 高风险但仍可路由"""
    print("\n=== 测试3: 高风险但仍可路由 ===")
    
    router = SkillRouter()
    
    task_context = TaskContext(
        source="system",
        task_type="backup",
        content="执行紧急备份",
        priority="critical",
        risk_level="medium",
        system_state={"health_score": 60},
        recent_history=[],
        available_handlers=["backup-restore-manager"]
    )
    
    output = router.route(task_context)
    
    print(router.explain_decision(output))
    print(f"\n置信度: {output.confidence:.1f}")
    
    # 验证
    assert output.chosen_handler == "backup-restore-manager"
    assert "critical" in output.situation_type
    print("\n✅ 测试通过")


def test_no_candidate_match():
    """测试4: 无候选命中"""
    print("\n=== 测试4: 无候选命中 ===")
    
    router = SkillRouter()
    
    task_context = TaskContext(
        source="user",
        task_type="unknown",
        content="执行未知任务",
        priority="normal",
        risk_level="high",
        system_state={},
        recent_history=[],
        available_handlers=["github-repo-analyzer", "pattern-detector"]
    )
    
    output = router.route(task_context)
    
    print(router.explain_decision(output))
    print(f"\n置信度: {output.confidence:.1f}")
    
    # 验证
    assert output.chosen_handler is None
    assert output.confidence == 0.0
    print("\n✅ 测试通过")


def test_all_fixtures():
    """测试所有 fixtures 用例"""
    print("\n=== 测试所有 fixtures 用例 ===")
    
    router = SkillRouter()
    test_cases = load_test_cases()
    
    for i, case in enumerate(test_cases['test_cases'], 1):
        print(f"\n--- Fixture {i}: {case['name']} ---")
        
        task_context = TaskContext(**case['input'])
        output = router.route(task_context)
        
        print(router.explain_decision(output))
        
        # 验证期望
        expected = case['expected']
        if 'chosen_handler' in expected:
            assert output.chosen_handler == expected['chosen_handler'], \
                f"期望 {expected['chosen_handler']}, 实际 {output.chosen_handler}"
        
        if 'min_confidence' in expected:
            assert output.confidence >= expected['min_confidence'], \
                f"置信度过低: {output.confidence} < {expected['min_confidence']}"
        
        print(f"✅ {case['name']} 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Skill Router 测试套件")
    print("=" * 60)
    
    try:
        test_single_clear_match()
        test_multiple_candidates_conflict()
        test_high_risk_routing()
        test_no_candidate_match()
        test_all_fixtures()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
