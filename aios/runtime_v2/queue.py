"""
Task Queue - Task Submission Interface

职责：
- enqueue(task) → 写入 task_created event
- list_tasks() → 返回所有任务（通过 state projection）
- 不做 dequeue（由 dispatcher 负责）

Task Schema:
{
    "task_id": "t123",
    "type": "code|analysis|monitor",
    "description": "refactor module",
    "priority": "high|normal|low",
    "created_at": "ISO8601",
    "source": "cli|heartbeat|user"
}
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from .event_log import get_event_log


class TaskQueue:
    def __init__(self):
        self.event_log = get_event_log()
    
    def enqueue(
        self,
        task_type: str,
        description: str,
        priority: str = "normal",
        source: str = "cli"
    ) -> str:
        """
        提交一个任务
        
        Args:
            task_type: code|analysis|monitor
            description: 任务描述
            priority: high|normal|low
            source: cli|heartbeat|user
        
        Returns:
            task_id
        """
        task_id = f"t-{uuid.uuid4().hex[:8]}"
        
        task_data = {
            "task_id": task_id,
            "type": task_type,
            "description": description,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "source": source
        }
        
        # 写入 task_created event
        self.event_log.append_event(
            event_type="task_created",
            task_id=task_id,
            data=task_data
        )
        
        return task_id
    
    def list_tasks(self) -> list:
        """
        列出所有任务（通过 state projection）
        
        注意：这个方法实际上应该调用 state.py 的 projection
        这里先返回空列表，等 state.py 实现后再补充
        """
        # TODO: 调用 state.list_all_tasks()
        return []


# 全局单例
_queue = None

def get_queue() -> TaskQueue:
    """获取全局 TaskQueue 实例"""
    global _queue
    if _queue is None:
        _queue = TaskQueue()
    return _queue
