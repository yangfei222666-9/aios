"""
State Projection - Event Log → Current State

职责：
- 从 event log 投影出当前状态
- 提供查询接口（pending/running/completed tasks）
- 不做 event 写入

实现方式：
events → group by task_id → last event → state

State Machine:
task_created → pending
task_started → running
task_completed → completed
task_failed → failed
task_timeout → timeout
"""

from typing import Dict, List, Any
from collections import defaultdict

from .event_log import get_event_log


class StateProjection:
    def __init__(self):
        self.event_log = get_event_log()
        # Incremental projection cache
        self._state_cache: Dict[str, Dict[str, Any]] = {}
        self._last_offset: int = 0  # 上次读取到的 event 数量
    
    def _apply_event(self, event: Dict[str, Any]) -> None:
        """
        将单个 event 应用到 state cache（增量更新）
        """
        task_id = event["task_id"]
        event_type = event["event_type"]

        # 状态映射
        state_map = {
            "task_created": "pending",
            "task_started": "running",
            "task_completed": "completed",
            "task_failed": "failed",
            "task_timeout": "timeout",
        }
        task_state = state_map.get(event_type, "unknown")

        if task_id not in self._state_cache:
            self._state_cache[task_id] = {
                "task_id": task_id,
                "state": task_state,
                "task_data": {},
                "last_event": event
            }
        else:
            self._state_cache[task_id]["state"] = task_state
            self._state_cache[task_id]["last_event"] = event

        # task_created 时保存原始 task_data
        if event_type == "task_created":
            self._state_cache[task_id]["task_data"] = event.get("data", {})

    def _project_state(self) -> Dict[str, Dict[str, Any]]:
        """
        增量投影：只读取新 events（O(delta) 而非 O(n)）
        """
        all_events = self.event_log.read_events()
        new_events = all_events[self._last_offset:]

        for event in new_events:
            self._apply_event(event)

        self._last_offset = len(all_events)
        return self._state_cache
    
    def get_task_state(self, task_id: str) -> Dict[str, Any]:
        """
        获取单个任务的状态
        
        Returns:
            {
                "task_id": "t123",
                "state": "pending|running|completed|failed|timeout",
                "task_data": {...},
                "last_event": {...}
            }
        """
        state = self._project_state()
        return state.get(task_id, None)
    
    def list_pending_tasks(self) -> List[Dict[str, Any]]:
        """列出所有 pending 任务"""
        state = self._project_state()
        return [
            task for task in state.values()
            if task["state"] == "pending"
        ]
    
    def list_running_tasks(self) -> List[Dict[str, Any]]:
        """列出所有 running 任务"""
        state = self._project_state()
        return [
            task for task in state.values()
            if task["state"] == "running"
        ]
    
    def list_completed_tasks(self) -> List[Dict[str, Any]]:
        """列出所有 completed 任务"""
        state = self._project_state()
        return [
            task for task in state.values()
            if task["state"] == "completed"
        ]
    
    def list_failed_tasks(self) -> List[Dict[str, Any]]:
        """列出所有 failed 任务"""
        state = self._project_state()
        return [
            task for task in state.values()
            if task["state"] == "failed"
        ]
    
    def list_stalled_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有 stalled 任务（running 超过 5 分钟）
        
        未来可以加更复杂的逻辑
        """
        from datetime import datetime, timedelta
        
        running_tasks = self.list_running_tasks()
        stalled = []
        
        now = datetime.utcnow()
        for task in running_tasks:
            last_event_time = datetime.fromisoformat(
                task["last_event"]["timestamp"].replace("Z", "")
            )
            if now - last_event_time > timedelta(minutes=5):
                stalled.append(task)
        
        return stalled


# 全局单例
_state = None

def get_state() -> StateProjection:
    """获取全局 StateProjection 实例"""
    global _state
    if _state is None:
        _state = StateProjection()
    return _state
