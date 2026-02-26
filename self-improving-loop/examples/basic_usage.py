"""
Self-Improving Loop - 基础使用示例
"""

from self_improving_loop import SelfImprovingLoop


def example_basic():
    """基础使用示例"""
    print("=" * 60)
    print("  Self-Improving Loop - 基础使用")
    print("=" * 60)

    # 创建实例
    loop = SelfImprovingLoop()

    # 模拟任务执行函数
    def my_task():
        # 你的实际任务逻辑
        print("执行任务...")
        return {"status": "success", "data": "result"}

    # 包装任务执行
    result = loop.execute_with_improvement(
        agent_id="my-agent",
        task="处理用户请求",
        execute_fn=my_task
    )

    # 检查结果
    print(f"\n任务结果:")
    print(f"  成功: {result['success']}")
    print(f"  耗时: {result['duration_sec']:.3f}s")
    print(f"  改进触发: {result['improvement_triggered']}")
    print(f"  改进应用: {result['improvement_applied']}")

    if result['rollback_executed']:
        print(f"  已回滚: {result['rollback_executed']['reason']}")

    # 查看统计
    stats = loop.get_improvement_stats("my-agent")
    print(f"\nAgent 统计:")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  回滚次数: {stats['rollback_count']}")


def example_with_failures():
    """模拟失败场景"""
    print("\n" + "=" * 60)
    print("  模拟失败场景")
    print("=" * 60)

    loop = SelfImprovingLoop()

    # 模拟会失败的任务
    def failing_task():
        import random
        if random.random() < 0.7:  # 70% 失败率
            raise Exception("模拟错误")
        return {"status": "success"}

    # 执行多次任务
    for i in range(10):
        result = loop.execute_with_improvement(
            agent_id="test-agent",
            task=f"任务 {i+1}",
            execute_fn=failing_task
        )

        status = "✓" if result['success'] else "✗"
        print(f"  {status} 任务 {i+1}: {result['duration_sec']:.3f}s", end="")

        if result['improvement_triggered']:
            print(f" [触发改进]", end="")

        if result['rollback_executed']:
            print(f" [已回滚]", end="")

        print()

    # 最终统计
    stats = loop.get_improvement_stats("test-agent")
    print(f"\n最终统计:")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  回滚次数: {stats['rollback_count']}")


if __name__ == "__main__":
    example_basic()
    example_with_failures()
