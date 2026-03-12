"""
Policy Decision 测试
"""

from policy_decision import PolicyDecisionEngine
from policy_decision_schema import PolicyInput


def test_auto_execute_low_risk():
    """测试1: 低风险监控任务 → auto_execute"""
    print("\n=== 测试1: 低风险监控任务 → auto_execute ===")
    
    engine = PolicyDecisionEngine()
    
    policy_input = PolicyInput(
        operation_type="monitor",
        handler_type="skill",
        handler_name="aios-health-monitor",
        risk_level="low",
        system_health="healthy",
        known_failure_patterns=[],
        user_policy={},
        router_decision={"confidence": 99.4, "fallback_handlers": []}
    )
    
    output = engine.decide(policy_input)
    
    print(engine.explain_decision(output))
    print(f"\n匹配规则: {', '.join(output.matched_rules)}")
    print(f"风险评分: {output.risk_summary['risk_score']}/100")
    
    # 验证
    assert output.policy_result == "auto_execute"
    print("\n✅ 测试通过")


def test_require_confirmation_high_risk():
    """测试2: 高风险修改任务 → require_confirmation"""
    print("\n=== 测试2: 高风险修改任务 → require_confirmation ===")
    
    engine = PolicyDecisionEngine()
    
    policy_input = PolicyInput(
        operation_type="code_modify",
        handler_type="agent",
        handler_name="coder-dispatcher",
        risk_level="high",
        system_health="healthy",
        known_failure_patterns=[],
        user_policy={},
        router_decision={"confidence": 85.0, "fallback_handlers": ["backup-coder"]}
    )
    
    output = engine.decide(policy_input)
    
    print(engine.explain_decision(output))
    print(f"\n匹配规则: {', '.join(output.matched_rules)}")
    print(f"风险评分: {output.risk_summary['risk_score']}/100")
    
    # 验证
    assert output.policy_result == "require_confirmation"
    assert output.fallback_action == "require_human"
    print("\n✅ 测试通过")


def test_degrade_known_failure():
    """测试3: 命中 timeout 失败模式 → degrade"""
    print("\n=== 测试3: 命中 timeout 失败模式 → degrade ===")
    
    engine = PolicyDecisionEngine()
    
    policy_input = PolicyInput(
        operation_type="analysis",
        handler_type="skill",
        handler_name="pattern-detector",
        risk_level="medium",
        system_health="healthy",
        known_failure_patterns=["timeout", "resource_exhausted"],
        user_policy={},
        router_decision={"confidence": 75.0, "fallback_handlers": ["backup-analyzer"]}
    )
    
    output = engine.decide(policy_input)
    
    print(engine.explain_decision(output))
    print(f"\n匹配规则: {', '.join(output.matched_rules)}")
    print(f"风险评分: {output.risk_summary['risk_score']}/100")
    
    # 验证
    assert output.policy_result == "degrade"
    assert output.fallback_action == "use_backup_handler"
    print("\n✅ 测试通过")


def test_reject_critical_system():
    """测试4: 系统 critical + 高风险操作 → reject"""
    print("\n=== 测试4: 系统 critical + 高风险操作 → reject ===")
    
    engine = PolicyDecisionEngine()
    
    policy_input = PolicyInput(
        operation_type="backup_restore",
        handler_type="skill",
        handler_name="backup-restore-manager",
        risk_level="high",
        system_health="critical",
        known_failure_patterns=[],
        user_policy={},
        router_decision={"confidence": 90.0, "fallback_handlers": []}
    )
    
    output = engine.decide(policy_input)
    
    print(engine.explain_decision(output))
    print(f"\n匹配规则: {', '.join(output.matched_rules)}")
    print(f"风险评分: {output.risk_summary['risk_score']}/100")
    
    # 验证
    assert output.policy_result == "reject"
    assert output.fallback_action == "require_human"
    print("\n✅ 测试通过")


def test_degrade_use_backup():
    """测试5: 主 handler 不稳定，切备用 → degrade + use_backup_handler"""
    print("\n=== 测试5: 主 handler 不稳定，切备用 → degrade + use_backup_handler ===")
    
    engine = PolicyDecisionEngine()
    
    policy_input = PolicyInput(
        operation_type="analysis",
        handler_type="agent",
        handler_name="primary-analyzer",
        risk_level="medium",
        system_health="degraded",
        known_failure_patterns=["intermittent_failure"],
        user_policy={},
        router_decision={"confidence": 65.0, "fallback_handlers": ["backup-analyzer"]}
    )
    
    output = engine.decide(policy_input)
    
    print(engine.explain_decision(output))
    print(f"\n匹配规则: {', '.join(output.matched_rules)}")
    print(f"风险评分: {output.risk_summary['risk_score']}/100")
    
    # 验证
    assert output.policy_result == "degrade"
    print("\n✅ 测试通过")


def test_reject_no_fallback():
    """测试6: 无 fallback 的危险动作 → reject"""
    print("\n=== 测试6: 无 fallback 的危险动作 → reject ===")
    
    engine = PolicyDecisionEngine()
    
    policy_input = PolicyInput(
        operation_type="code_modify",
        handler_type="agent",
        handler_name="experimental-coder",
        risk_level="critical",
        system_health="healthy",
        known_failure_patterns=[],
        user_policy={},
        router_decision={"confidence": 80.0, "fallback_handlers": []}  # 无备用
    )
    
    output = engine.decide(policy_input)
    
    print(engine.explain_decision(output))
    print(f"\n匹配规则: {', '.join(output.matched_rules)}")
    print(f"风险评分: {output.risk_summary['risk_score']}/100")
    
    # 验证
    assert output.policy_result == "reject"
    assert output.fallback_action == "require_human"
    print("\n✅ 测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Policy Decision 测试套件")
    print("=" * 60)
    
    try:
        test_auto_execute_low_risk()
        test_require_confirmation_high_risk()
        test_degrade_known_failure()
        test_reject_critical_system()
        test_degrade_use_backup()
        test_reject_no_fallback()
        
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
