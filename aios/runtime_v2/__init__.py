"""
Runtime v2 - Event-Driven Task Execution Runtime

核心模块：
- event_log: Append-only event storage
- queue: Task submission interface
- state: Event log → current state projection
- dispatcher: Runtime kernel (scheduling)
- worker: Task executor
- runner: Shadow loop

使用方式：
    # 提交任务
    from aios.runtime_v2 import get_queue
    queue = get_queue()
    task_id = queue.enqueue(task_type="code", description="refactor module")
    
    # 启动 runtime
    from aios.runtime_v2 import run_runtime
    run_runtime()
"""

from .event_log import EventLog, get_event_log
from .queue import TaskQueue, get_queue
from .state import StateProjection, get_state
from .dispatcher import Dispatcher, get_dispatcher
from .worker import Worker, get_worker
from .runner import RuntimeRunner, run_runtime
from .metrics import RuntimeMetrics, get_metrics

__all__ = [
    "EventLog",
    "get_event_log",
    "TaskQueue",
    "get_queue",
    "StateProjection",
    "get_state",
    "Dispatcher",
    "get_dispatcher",
    "Worker",
    "get_worker",
    "RuntimeRunner",
    "run_runtime",
    "RuntimeMetrics",
    "get_metrics",
]
