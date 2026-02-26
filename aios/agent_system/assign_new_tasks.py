"""
重新分配任务给所有 Agent
"""
from auto_dispatcher import AutoDispatcher
from pathlib import Path
from datetime import datetime

workspace = Path("C:/Users/A/.openclaw/workspace")
dispatcher = AutoDispatcher(workspace)

print("=== 重新分配任务 ===\n")

# 任务1: Coder - 实现缓存装饰器
task1 = {
    'id': f'coder-{int(datetime.now().timestamp())}',
    'type': 'code',
    'description': '实现一个带TTL的缓存装饰器，支持过期时间和LRU淘汰策略',
    'priority': 'normal',
    'enqueued_at': datetime.now().isoformat()
}
dispatcher.enqueue_task(task1)
print("✓ Coder 任务: 实现带TTL的缓存装饰器")

# 任务2: Analyst - 分析系统性能
task2 = {
    'id': f'analyst-{int(datetime.now().timestamp())}',
    'type': 'analysis',
    'description': '分析最近24小时的系统性能数据，识别性能瓶颈和优化机会',
    'priority': 'normal',
    'enqueued_at': datetime.now().isoformat()
}
dispatcher.enqueue_task(task2)
print("✓ Analyst 任务: 分析系统性能数据")

# 任务3: Monitor - 健康检查
task3 = {
    'id': f'monitor-{int(datetime.now().timestamp())}',
    'type': 'monitor',
    'description': '执行系统健康检查，监控CPU/内存/磁盘使用率，生成健康报告',
    'priority': 'high',
    'enqueued_at': datetime.now().isoformat()
}
dispatcher.enqueue_task(task3)
print("✓ Monitor 任务: 系统健康检查 (高优先级)")

print("\n=== 任务已入队 ===")
print("注意: 这些任务需要在 OpenClaw 主会话的心跳中处理")
print("      通过 sessions_spawn 创建子 Agent 执行")
