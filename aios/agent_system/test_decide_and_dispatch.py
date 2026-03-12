"""
Decide and Dispatch 测试
"""

from decide_and_dispatch import DecideAndDispatch
from decide_and_dispatch_schema import TaskContext


def test_normal_monitor_task():
    """测试1: 普通监控任务 - router 选 monitor，policy 放行，成功派发"""
    print("\n=== 测试1: 普通监控任务 ===")
    
    dispatcher = DecideAndDispatch()
    
    task_context = TaskContext(
        source="heartbeat",
        task_type="monitor",
        content="检查系统健康状态",
        priority="normal",
        risk_level="low",
        system_state={"health_status": "healthy", "health_score": 85},
        recent_history=[],
        available_handlers=["aios-health-monitor", "pattern-detector"]
    )
    
    decision_record = dispatcher.process(task_context)
    
    print(dispatcher.explain_decision(decision_record))
    
    # 验证
    assert decision_record.chosen_handler == "aios-health-monitor"
    assert decision_record.final_status == "dispatched"
    print("\n✅ 测试通过")


def test_high_risk_modify_blocked():
    """测试2: 高风险修改任务 - router 选 handler，但 policy 要求确认，最终 blocked"""
    print("\n=== 测试2: 高风险修改任务 ===")
    
    dispatcher = DecideAndDispatch()
    
    task_context = TaskContext(
        source="user",
        task_type="backup",
        content="执行系统备份",
        priority="high",
        risk_level="high",
        system_state={"health_status": "healthy", "health_score": 90},
        recent_history=[],
        available_handlers=["backup-restore-manager"]
    )
    
    decision_record = dispatcher.process(task_context)
    
    print(dispatcher.explain_decision(decision_record))
    
    # 验证
    assert decision_record.final_status == "blocked"
    assert decision_record.dispatch_result.error is not None
    print("\n✅ 测试通过")


def test_known_failure_degrade():
    """测试3: 命中已知 timeout 模式 - router 正常，policy degrade，最终走降级路径"""
    print("\n=== 测试3: 命中已知 timeout 模式 ===")
    
    dispatcher = DecideAndDispatch()
    
    task_context = TaskContext(
        source="system",
        task_type="analysis",
        content="分析失败模式",
        priority="high",
        risk_level="medium",
        system_state={"health_status": "healthy", "health_score": 75},
        recent_history=[
            {"status": "failed", "error_type": "timeout"},
            {"status": "failed", "error_type": "resource_exhausted"}
        ],
        available_handlers=["pattern-detector", "agent-performance-analyzer"]
    )
    
    decision_record = dispatcher.process(task_context)
    
    print(dispatcher.explain_decision(decision_record))
    
    # 验证
    assert decision_record.final_status == "degraded"
    assert decision_record.dispatch_result.fallback_triggered == True
    print("\n✅ 测试通过")


def test_heartbeat_input():
    """测试4: heartbeat 输入 - 统一入口成功转成 task_context，并完成编排"""
    print("\n=== 测试4: heartbeat 输入 ===")
    
    dispatcher = DecideAndDispatch()
    
    task_context = TaskContext(
        source="heartbeat",
        task_type="monitor",
        content="定期健康检查",
        priority="low",
        risk_level="safe",
        system_state={"health_status": "healthy", "health_score": 92},
        recent_history=[],
        available_handlers=["aios-health-monitor"]
    )
    
    decision_record = dispatcher.process(task_context)
    
    print(dispatcher.explain_decision(decision_record))
    
    # 验证
    assert decision_record.current_situation is not None
    assert decision_record.final_status in ["dispatched", "blocked", "degraded", "failed"]
    print("\n✅ 测试通过")


def test_no_candidate_handler():
    """测试5: 无候选 handler - router 无可用候选，dispatch 失败但留下可复盘记录"""
    print("\n=== 测试5: 无候选 handler ===")
    
    dispatcher = DecideAndDispatch()
    
    task_context = TaskContext(
        source="user",
        task_type="unknown",
        content="执行未知任务",
        priority="normal",
        risk_level="high",
        system_state={"health_status": "healthy", "health_score": 80},
        recent_history=[],
        available_handlers=["github-repo-analyzer", "pattern-detector"]
    )
    
    decision_record = dispatcher.process(task_context)
    
    print(dispatcher.explain_decision(decision_record))
    
    # 验证
    assert decision_record.chosen_handler is None
    assert decision_record.final_status == "failed"
    assert decision_record.memory_writeback is not None
    print("\n✅ 测试通过")


def test_backup_handler_switch():
    """测试6: 备用 handler 切换 - 主 handler 不可用，走 fallback 到 backup handler"""
    print("\n=== 测试6: 备用 handler 切换 ===")
    
    dispatcher = DecideAndDispatch()
    
    task_context = TaskContext(
        source="system",
        task_type="analysis",
        content="性能分析",
        priority="medium",
        risk_level="medium",
        system_state={"health_status": "degraded", "health_score": 65},
        recent_history=[
            {"status": "failed", "error_type": "intermittent_failure"}
        ],
        available_handlers=["agent-performance-analyzer", "pattern-detector"]
    )
    
    decision_record = dispatcher.process(task_context)
    
    print(dispatcher.explain_decision(decision_record))
    
    # 验证
    assert decision_record.final_status in ["degraded", "dispatched"]
    if decision_record.dispatch_result.fallback_triggered:
        assert decision_record.dispatch_result.handler_used is not None
    print("\n✅ 测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Decide and Dispatch 测试套件")
    print("=" * 60)
    
    try:
        test_normal_monitor_task()
        test_high_risk_modify_blocked()
        test_known_failure_degrade()
        test_heartbeat_input()
        test_no_candidate_handler()
        test_backup_handler_switch()
        
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
