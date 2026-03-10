"""
AIOS Agent System 功能测试
"""

import json
import time
from aios.agent_system import AgentSystem


def test_basic_flow():
    """测试基本流程"""
    print("=" * 60)
    print("测试 1: 基本流程")
    print("=" * 60)

    system = AgentSystem()

    # 1. 初始状态
    print("\n1. 初始状态:")
    status = system.get_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 2. 第一个任务 - 应该创建 coder Agent
    print("\n2. 处理代码任务（应该创建新 Agent）:")
    result1 = system.handle_task("帮我写一个 Python 爬虫", auto_create=True)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    assert result1["status"] == "success"
    assert result1["action"] == "created"
    agent_id = result1["agent_id"]

    # 3. 第二个任务 - 应该复用现有 Agent
    print("\n3. 处理另一个代码任务（应该复用 Agent）:")
    result2 = system.handle_task("调试这段代码", auto_create=True)
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    assert result2["status"] == "success"
    assert result2["action"] == "assigned"
    assert result2["agent_id"] == agent_id

    # 4. 报告任务结果
    print("\n4. 报告任务结果:")
    system.report_task_result(agent_id, success=True, duration_sec=45.5)
    agent = system.get_agent_detail(agent_id)
    print(f"Agent 统计: {json.dumps(agent['stats'], indent=2, ensure_ascii=False)}")

    # 5. 最终状态
    print("\n5. 最终状态:")
    status = system.get_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    print("\n[OK] 测试 1 通过")


def test_multiple_types():
    """测试多种类型任务"""
    print("\n" + "=" * 60)
    print("测试 2: 多种类型任务")
    print("=" * 60)

    system = AgentSystem()

    tasks = [
        ("写一个 REST API", "coder"),
        ("分析用户数据", "analyst"),
        ("检查系统状态", "monitor"),
        ("搜索 Python 最佳实践", "researcher"),
        ("设计微服务架构", "coder"),
    ]

    for task, expected_template in tasks:
        print(f"\n任务: {task}")
        result = system.handle_task(task, auto_create=True)
        print(f"  动作: {result['action']}")
        print(f"  Agent: {result['agent_id']} ({result['agent_template']})")
        assert result["agent_template"] == expected_template

    # 查看最终状态
    print("\n最终状态:")
    status = system.get_status()
    print(f"  总 Agent 数: {status['total_active']}")
    print(
        f"  按类型分布: {json.dumps(status['summary']['by_template'], ensure_ascii=False)}"
    )

    print("\n[OK] 测试 2 通过")


def test_task_routing():
    """测试任务路由准确性"""
    print("\n" + "=" * 60)
    print("测试 3: 任务路由准确性")
    print("=" * 60)

    from aios.agent_system._deprecated.core_task_router import TaskRouter

    router = TaskRouter()

    test_cases = [
        ("写一个爬虫", "code", "coder"),
        ("分析日志", "analysis", "analyst"),
        ("监控CPU", "monitor", "monitor"),
        ("搜索资料", "research", "researcher"),
        ("设计架构", "design", "coder"),
    ]

    for message, expected_type, expected_template in test_cases:
        analysis = router.analyze_task(message)
        print(f"\n消息: {message}")
        print(f"  识别类型: {analysis['task_type']} (期望: {expected_type})")
        print(
            f"  推荐模板: {analysis['recommended_template']} (期望: {expected_template})"
        )
        print(f"  置信度: {analysis['confidence']:.2f}")
        assert analysis["task_type"] == expected_type
        assert analysis["recommended_template"] == expected_template

    print("\n[OK] 测试 3 通过")


def test_cleanup():
    """测试清理功能"""
    print("\n" + "=" * 60)
    print("测试 4: 清理闲置 Agent")
    print("=" * 60)

    system = AgentSystem()

    # 创建一些 Agent
    system.handle_task("写代码", auto_create=True)
    system.handle_task("分析数据", auto_create=True)

    print("\n清理前:")
    status = system.get_status()
    print(f"  活跃 Agent: {status['total_active']}")

    # 清理（设置很短的时间，应该清理所有）
    archived = system.cleanup_idle_agents(idle_hours=0)
    print(f"\n清理了 {len(archived)} 个 Agent: {', '.join(archived)}")

    print("\n清理后:")
    status = system.get_status()
    print(f"  活跃 Agent: {status['total_active']}")
    print(f"  归档 Agent: {status['summary']['archived']}")

    print("\n[OK] 测试 4 通过")


def main():
    """运行所有测试"""
    print("\n[START] AIOS Agent System 功能测试\n")

    try:
        test_basic_flow()
        test_multiple_types()
        test_task_routing()
        test_cleanup()

        print("\n" + "=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n[FAIL] 错误: {e}")
        raise


if __name__ == "__main__":
    main()
