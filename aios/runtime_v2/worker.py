"""
Worker - Task Executor

职责：
- execute(task) → 执行任务 + 写入 event（completed/failed/timeout）
- 不做 scheduling logic

执行流程：
1. 根据 task.type 路由到对应 Agent
2. 执行任务
3. 写入 task_completed / task_failed event
"""

import time
from typing import Dict, Any

from .event_log import get_event_log


class Worker:
    def __init__(self):
        self.event_log = get_event_log()
    
    def execute(self, task: Dict[str, Any]) -> bool:
        """
        执行任务
        
        Args:
            task: {
                "task_id": "t123",
                "task_data": {
                    "type": "code|analysis|monitor",
                    "description": "...",
                    ...
                }
            }
        
        Returns:
            success: True/False
        """
        task_id = task["task_id"]
        task_data = task["task_data"]
        task_type = task_data.get("type", "unknown")
        
        print(f"[WORKER] Executing task: {task_id} (type: {task_type})")
        
        try:
            # 根据 task_type 路由
            if task_type == "code":
                result = self._execute_code_task(task_data)
            elif task_type == "analysis":
                result = self._execute_analysis_task(task_data)
            elif task_type == "monitor":
                result = self._execute_monitor_task(task_data)
            else:
                result = {"success": False, "error": f"Unknown task type: {task_type}"}
            
            # 写入 event
            if result.get("success", False):
                self.event_log.append_event(
                    event_type="task_completed",
                    task_id=task_id,
                    data={
                        "completed_at": time.time(),
                        "result": result
                    }
                )
                print(f"[WORKER] Task completed: {task_id}")
                return True
            else:
                self.event_log.append_event(
                    event_type="task_failed",
                    task_id=task_id,
                    data={
                        "failed_at": time.time(),
                        "error": result.get("error", "Unknown error")
                    }
                )
                print(f"[WORKER] Task failed: {task_id}")
                return False
        
        except Exception as e:
            # 异常处理
            self.event_log.append_event(
                event_type="task_failed",
                task_id=task_id,
                data={
                    "failed_at": time.time(),
                    "error": str(e)
                }
            )
            print(f"[WORKER] Task failed with exception: {task_id} - {e}")
            return False
    
    def _execute_code_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 code 任务
        
        第一版：模拟执行（返回成功）
        未来：调用真实 coder-dispatcher
        """
        # TODO: 调用真实 Agent
        time.sleep(0.1)  # 模拟执行
        return {"success": True, "output": "Code task completed"}
    
    def _execute_analysis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 analysis 任务
        
        第一版：模拟执行（返回成功）
        未来：调用真实 analyst-dispatcher
        """
        # TODO: 调用真实 Agent
        time.sleep(0.1)  # 模拟执行
        return {"success": True, "output": "Analysis task completed"}
    
    def _execute_monitor_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 monitor 任务
        
        第一版：模拟执行（返回成功）
        未来：调用真实 monitor-dispatcher
        """
        # TODO: 调用真实 Agent
        time.sleep(0.1)  # 模拟执行
        return {"success": True, "output": "Monitor task completed"}


# 全局单例
_worker = None

def get_worker() -> Worker:
    """获取全局 Worker 实例"""
    global _worker
    if _worker is None:
        _worker = Worker()
    return _worker
