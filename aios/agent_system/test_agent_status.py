"""
test_agent_status.py - agent_status.py 单元测试

测试范围：
1. 状态枚举合法性
2. 状态校验函数
3. 默认状态构造器
4. 状态映射辅助函数
5. 状态转换规则

版本：v1.0
最后更新：2026-03-11
"""

import sys
from pathlib import Path

# 添加 agent_system 到路径
sys.path.insert(0, str(Path(__file__).parent))

from agent_status import (
    ReadinessStatus, RunStatus, HealthStatus,
    validate_readiness_status, validate_run_status, validate_health_status,
    validate_status_object,
    create_default_agent_status, create_default_skill_status,
    map_legacy_status, infer_health_from_stats, should_be_routable,
    can_transition,
    get_status_summary, is_production_ready, is_healthy, needs_attention
)


def test_status_enums():
    """测试状态枚举"""
    print("Testing status enums...")
    
    # ReadinessStatus
    assert ReadinessStatus.REGISTERED.value == "registered"
    assert ReadinessStatus.PRODUCTION_READY.value == "production-ready"
    assert ReadinessStatus.ARCHIVED.value == "archived"
    
    # RunStatus
    assert RunStatus.SUCCESS.value == "success"
    assert RunStatus.FAILED.value == "failed"
    assert RunStatus.NO_SAMPLE.value == "no-sample"
    
    # HealthStatus
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.WARNING.value == "warning"
    assert HealthStatus.CRITICAL.value == "critical"
    
    print("✅ Status enums test passed")


def test_validation():
    """测试状态校验"""
    print("\nTesting validation...")
    
    # 合法状态
    assert validate_readiness_status("registered") == True
    assert validate_readiness_status("production-ready") == True
    assert validate_run_status("success") == True
    assert validate_health_status("healthy") == True
    
    # 非法状态
    assert validate_readiness_status("invalid") == False
    assert validate_run_status("invalid") == False
    assert validate_health_status("invalid") == False
    
    # 状态对象校验
    valid_obj = {
        "readiness_status": "registered",
        "run_status": "no-sample",
        "health_status": "unknown",
        "enabled": False,
        "routable": False
    }
    is_valid, errors = validate_status_object(valid_obj)
    assert is_valid == True
    assert len(errors) == 0
    
    # 缺少必需字段
    invalid_obj = {
        "readiness_status": "registered"
    }
    is_valid, errors = validate_status_object(invalid_obj)
    assert is_valid == False
    assert len(errors) > 0
    
    # 非法状态值
    invalid_obj = {
        "readiness_status": "invalid",
        "run_status": "no-sample",
        "health_status": "unknown",
        "enabled": False,
        "routable": False
    }
    is_valid, errors = validate_status_object(invalid_obj)
    assert is_valid == False
    assert "Invalid readiness_status" in errors[0]
    
    print("✅ Validation test passed")


def test_default_constructors():
    """测试默认状态构造器"""
    print("\nTesting default constructors...")
    
    # Agent 默认状态
    agent_status = create_default_agent_status("test_agent")
    assert agent_status["readiness_status"] == "registered"
    assert agent_status["run_status"] == "no-sample"
    assert agent_status["health_status"] == "unknown"
    assert agent_status["enabled"] == False
    assert agent_status["routable"] == False
    assert agent_status["last_run"] is None
    
    # Skill 默认状态
    skill_status = create_default_skill_status("test_skill")
    assert skill_status["readiness_status"] == "registered"
    assert skill_status["validation_date"] is None
    assert skill_status["validation_status"] is None
    
    # 自定义就绪状态
    custom_status = create_default_agent_status(
        "test_agent",
        readiness=ReadinessStatus.PRODUCTION_READY,
        enabled=True,
        routable=True
    )
    assert custom_status["readiness_status"] == "production-ready"
    assert custom_status["enabled"] == True
    assert custom_status["routable"] == True
    
    print("✅ Default constructors test passed")


def test_mapping_helpers():
    """测试状态映射辅助函数"""
    print("\nTesting mapping helpers...")
    
    # 旧状态映射
    assert map_legacy_status("active") == ReadinessStatus.PRODUCTION_READY
    assert map_legacy_status("stable") == ReadinessStatus.STABLE
    assert map_legacy_status("experimental") == ReadinessStatus.PRODUCTION_CANDIDATE
    assert map_legacy_status("unknown") == ReadinessStatus.REGISTERED
    
    # 健康状态推断
    stats_healthy = {"tasks_completed": 8, "tasks_failed": 2}
    assert infer_health_from_stats(stats_healthy) == HealthStatus.HEALTHY
    
    stats_warning = {"tasks_completed": 7, "tasks_failed": 3}
    assert infer_health_from_stats(stats_warning) == HealthStatus.WARNING
    
    stats_critical = {"tasks_completed": 5, "tasks_failed": 5}
    assert infer_health_from_stats(stats_critical) == HealthStatus.CRITICAL
    
    stats_unknown = {}
    assert infer_health_from_stats(stats_unknown) == HealthStatus.UNKNOWN
    
    # 可路由判断
    routable_obj = {
        "readiness_status": "production-ready",
        "enabled": True,
        "health_status": "healthy"
    }
    assert should_be_routable(routable_obj) == True
    
    not_routable_obj = {
        "readiness_status": "registered",
        "enabled": True,
        "health_status": "healthy"
    }
    assert should_be_routable(not_routable_obj) == False
    
    print("✅ Mapping helpers test passed")


def test_state_transitions():
    """测试状态转换规则"""
    print("\nTesting state transitions...")
    
    # 合法转换
    can, error = can_transition(
        ReadinessStatus.REGISTERED,
        ReadinessStatus.EXECUTABLE
    )
    assert can == True
    assert error is None
    
    can, error = can_transition(
        ReadinessStatus.VALIDATED,
        ReadinessStatus.PRODUCTION_CANDIDATE
    )
    assert can == True
    
    # 非法转换
    can, error = can_transition(
        ReadinessStatus.REGISTERED,
        ReadinessStatus.PRODUCTION_READY
    )
    assert can == False
    assert error is not None
    
    # 归档后不可转换
    can, error = can_transition(
        ReadinessStatus.ARCHIVED,
        ReadinessStatus.REGISTERED
    )
    assert can == False
    
    print("✅ State transitions test passed")


def test_utility_functions():
    """测试工具函数"""
    print("\nTesting utility functions...")
    
    test_obj = {
        "readiness_status": "production-ready",
        "run_status": "success",
        "health_status": "healthy",
        "enabled": True,
        "routable": True
    }
    
    # 状态摘要
    summary = get_status_summary(test_obj)
    assert "production-ready" in summary
    assert "success" in summary
    assert "healthy" in summary
    
    # 生产就绪判断
    assert is_production_ready(test_obj) == True
    
    not_ready_obj = {**test_obj, "readiness_status": "registered"}
    assert is_production_ready(not_ready_obj) == False
    
    # 健康判断
    assert is_healthy(test_obj) == True
    
    unhealthy_obj = {**test_obj, "health_status": "critical"}
    assert is_healthy(unhealthy_obj) == False
    
    # 需要关注判断
    assert needs_attention(test_obj) == False
    
    warning_obj = {**test_obj, "health_status": "warning"}
    assert needs_attention(warning_obj) == True
    
    failed_obj = {**test_obj, "run_status": "failed"}
    assert needs_attention(failed_obj) == True
    
    print("✅ Utility functions test passed")


def test_state_index_compatibility():
    """测试与 state_index.json 的兼容性"""
    print("\nTesting state_index.json compatibility...")
    
    # 模拟 state_index.json 中的对象
    github_researcher = {
        "readiness_status": "production-ready",
        "run_status": "success",
        "health_status": "healthy",
        "enabled": True,
        "routable": True,
        "last_run": "2026-03-11T13:30:00+08:00",
        "validation_report": "aios/agent_system/reports/github_researcher_validation_report.md",
        "notes": []
    }
    
    # 校验
    is_valid, errors = validate_status_object(github_researcher)
    assert is_valid == True
    assert len(errors) == 0
    
    # 判断
    assert is_production_ready(github_researcher) == True
    assert is_healthy(github_researcher) == True
    assert should_be_routable(github_researcher) == True
    assert needs_attention(github_researcher) == False
    
    print("✅ state_index.json compatibility test passed")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Running agent_status.py unit tests")
    print("=" * 60)
    
    try:
        test_status_enums()
        test_validation()
        test_default_constructors()
        test_mapping_helpers()
        test_state_transitions()
        test_utility_functions()
        test_state_index_compatibility()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
