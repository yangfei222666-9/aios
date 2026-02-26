#!/usr/bin/env python3
"""生成测试决策数据"""
import sys
sys.path.insert(0, r"C:\Users\A\.openclaw\workspace")

from aios.agent_system.production_router import ProductionRouter, TaskContext, TaskType, RiskLevel

router = ProductionRouter()

# 生成 10 个不同场景的决策
scenarios = [
    TaskContext(
        task_id="task-001",
        description="实现用户登录功能",
        task_type=TaskType.CODING,
        complexity=5,
        risk_level=RiskLevel.MEDIUM,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.4,
        memory_usage=0.5
    ),
    TaskContext(
        task_id="task-002",
        description="修复支付接口超时",
        task_type=TaskType.DEBUG,
        complexity=7,
        risk_level=RiskLevel.HIGH,
        error_rate=0.35,
        performance_drop=0.0,
        cpu_usage=0.5,
        memory_usage=0.6
    ),
    TaskContext(
        task_id="task-003",
        description="优化数据库查询",
        task_type=TaskType.OPTIMIZE,
        complexity=8,
        risk_level=RiskLevel.MEDIUM,
        error_rate=0.1,
        performance_drop=0.3,
        cpu_usage=0.6,
        memory_usage=0.7
    ),
    TaskContext(
        task_id="task-004",
        description="重构用户模块",
        task_type=TaskType.REFACTOR,
        complexity=6,
        risk_level=RiskLevel.MEDIUM,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.4,
        memory_usage=0.5
    ),
    TaskContext(
        task_id="task-005",
        description="部署到生产环境",
        task_type=TaskType.DEPLOY,
        complexity=9,
        risk_level=RiskLevel.CRITICAL,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.4,
        memory_usage=0.5
    ),
    TaskContext(
        task_id="task-006",
        description="编写单元测试",
        task_type=TaskType.TEST,
        complexity=4,
        risk_level=RiskLevel.LOW,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.3,
        memory_usage=0.4
    ),
    TaskContext(
        task_id="task-007",
        description="系统健康检查",
        task_type=TaskType.MONITOR,
        complexity=3,
        risk_level=RiskLevel.LOW,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.85,
        memory_usage=0.9
    ),
    TaskContext(
        task_id="task-008",
        description="分析用户行为数据",
        task_type=TaskType.ANALYZE,
        complexity=6,
        risk_level=RiskLevel.LOW,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.5,
        memory_usage=0.6
    ),
    TaskContext(
        task_id="task-009",
        description="调研竞品功能",
        task_type=TaskType.RESEARCH,
        complexity=5,
        risk_level=RiskLevel.LOW,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.4,
        memory_usage=0.5
    ),
    TaskContext(
        task_id="task-010",
        description="代码审查",
        task_type=TaskType.REVIEW,
        complexity=7,
        risk_level=RiskLevel.HIGH,
        error_rate=0.05,
        performance_drop=0.0,
        cpu_usage=0.4,
        memory_usage=0.5
    ),
]

print("生成测试决策数据...")
for ctx in scenarios:
    plan = router.route(ctx)
    print(f"✓ {ctx.task_id}: {plan.agent_type} + {plan.model} (confidence: {plan.confidence:.2f})")

print(f"\n✅ 已生成 {len(scenarios)} 条决策记录")
print("访问 http://localhost:9092 查看 Dashboard")
