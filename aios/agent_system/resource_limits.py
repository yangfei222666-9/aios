# resource_limits.py - AIOS 资源限制配置
import os
import asyncio
from collections import defaultdict

# 环境变量配置（可通过 .env 或启动脚本覆盖）
MAX_AGENT_CONCURRENCY = int(os.getenv("AIOS_MAX_AGENT_CONCURRENCY", "3"))
MAX_GLOBAL_SPAWN_QUEUE = int(os.getenv("AIOS_MAX_GLOBAL_SPAWN_QUEUE", "100"))
MAX_SPAWN_PER_TICK = int(os.getenv("AIOS_MAX_SPAWN_PER_TICK", "5"))
DEFAULT_TASK_TIMEOUT_SEC = int(os.getenv("AIOS_DEFAULT_TASK_TIMEOUT_SEC", "300"))
MAX_STDOUT_BYTES = int(os.getenv("AIOS_MAX_STDOUT_BYTES", "1048576"))  # 1MB
MAX_STDERR_BYTES = int(os.getenv("AIOS_MAX_STDERR_BYTES", "1048576"))  # 1MB

# Agent 并发控制（Semaphore）
_agent_semaphores = defaultdict(lambda: asyncio.Semaphore(MAX_AGENT_CONCURRENCY))


def get_agent_semaphore(agent_id: str):
    """获取 Agent 的并发控制信号量"""
    return _agent_semaphores[agent_id]


def can_enqueue(current_queue_size: int) -> bool:
    """检查是否可以继续入队"""
    return current_queue_size < MAX_GLOBAL_SPAWN_QUEUE


def get_config():
    """获取当前资源限制配置"""
    return {
        "MAX_AGENT_CONCURRENCY": MAX_AGENT_CONCURRENCY,
        "MAX_GLOBAL_SPAWN_QUEUE": MAX_GLOBAL_SPAWN_QUEUE,
        "MAX_SPAWN_PER_TICK": MAX_SPAWN_PER_TICK,
        "DEFAULT_TASK_TIMEOUT_SEC": DEFAULT_TASK_TIMEOUT_SEC,
        "MAX_STDOUT_BYTES": MAX_STDOUT_BYTES,
        "MAX_STDERR_BYTES": MAX_STDERR_BYTES,
    }


if __name__ == "__main__":
    # 测试
    config = get_config()
    print("[OK] Resource Limits Config:")
    for k, v in config.items():
        print(f"  {k}: {v}")
    
    print(f"\n[OK] Can enqueue (0/100): {can_enqueue(0)}")
    print(f"[OK] Can enqueue (100/100): {can_enqueue(100)}")
    print(f"[OK] Can enqueue (101/100): {can_enqueue(101)}")
