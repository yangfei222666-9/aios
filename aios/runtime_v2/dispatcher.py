"""
Dispatcher - Runtime Kernel

职责：
- tick() → 扫描 pending tasks + 检查 worker capacity + spawn worker
- 不做 queue logic / state logic / event logic

Scheduling 策略（第一版）：
- FIFO（先进先出）
- 不做 priority scheduling（等有真实负载再加）
- worker capacity = 5（最多 5 个并发任务）
"""

from typing import List, Dict, Any
import time

from .state import get_state
from .event_log import get_event_log


class Dispatcher:
    def __init__(self, max_workers: int = 5):
        self.state = get_state()
        self.event_log = get_event_log()
        self.max_workers = max_workers
    
    def tick(self) -> Dict[str, Any]:
        """
        Dispatcher 主循环（一次 tick）
        
        流程：
        1. 扫描 pending tasks
        2. 检查 worker capacity
        3. spawn worker（如果有空位）
        
        Returns:
            {
                "pending": 3,
                "running": 2,
                "spawned": 1
            }
        """
        pending_tasks = self.state.list_pending_tasks()
        running_tasks = self.state.list_running_tasks()
        
        # 检查 worker capacity
        available_slots = self.max_workers - len(running_tasks)
        
        spawned = 0
        if available_slots > 0 and len(pending_tasks) > 0:
            # FIFO：按 created_at 排序
            pending_tasks.sort(key=lambda t: t["task_data"]["created_at"])
            
            # Spawn workers
            for task in pending_tasks[:available_slots]:
                self.spawn_worker(task)
                spawned += 1
        
        return {
            "pending": len(pending_tasks),
            "running": len(running_tasks),
            "spawned": spawned
        }
    
    def spawn_worker(self, task: Dict[str, Any]) -> None:
        """
        Spawn 一个 worker 执行任务
        
        实际上应该：
        1. 写入 task_started event
        2. 调用 worker.execute(task)
        
        第一版先只写 event，worker 逻辑在 Step 5 实现
        """
        task_id = task["task_id"]
        
        # 写入 task_started event
        self.event_log.append_event(
            event_type="task_started",
            task_id=task_id,
            data={
                "started_at": time.time(),
                "worker_id": f"worker-{task_id}"
            }
        )
        
        # TODO: 调用 worker.execute(task)
        print(f"[DISPATCHER] Spawned worker for task: {task_id}")


# 全局单例
_dispatcher = None

def get_dispatcher() -> Dispatcher:
    """获取全局 Dispatcher 实例"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = Dispatcher()
    return _dispatcher
