"""
Real Agent Integration - Phase 2

只接入 coder_agent，验证真实 workload。

集成方式：
- type=code → 调用真实 coder-dispatcher（通过 sessions_spawn）
- 其他 type → 模拟执行（保持原样）
"""

import time
import json
from pathlib import Path
from typing import Dict, Any

from .event_log import get_event_log


class RealWorker:
    def __init__(self):
        self.event_log = get_event_log()
        self.spawn_requests_path = Path(__file__).parent.parent / "agent_system" / "spawn_requests.jsonl"
    
    def execute(self, task: Dict[str, Any]) -> bool:
        """
        执行任务（真实 Agent 集成）
        
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
                result = self._execute_real_coder(task_data)
            elif task_type == "analysis":
                result = self._execute_simulation(task_data, "analysis")
            elif task_type == "monitor":
                result = self._execute_simulation(task_data, "monitor")
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
    
    def _execute_real_coder(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行真实 coder_agent（通过 sessions_spawn）
        
        流程：
        1. 生成 spawn_request
        2. 写入 spawn_requests.jsonl
        3. 等待 OpenClaw 主会话执行
        4. 轮询结果（简化版：直接返回成功）
        """
        description = task_data.get("description", "")
        
        # 生成 spawn_request
        spawn_request = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent_id": "coder-dispatcher",
            "task": description,
            "label": f"runtime-v2-{task_data.get('task_id', 'unknown')}",
            "cleanup": "keep",
            "runTimeoutSeconds": 120,
            "source": "runtime_v2"
        }
        
        # 写入 spawn_requests.jsonl
        self.spawn_requests_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.spawn_requests_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")
        
        print(f"[WORKER] Spawn request created: {spawn_request['label']}")
        
        # 简化版：直接返回成功（真实版本应该轮询 spawn_results.jsonl）
        # TODO: 实现真实的结果轮询
        return {"success": True, "output": "Spawn request created (pending execution)"}
    
    def _execute_simulation(self, task_data: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        模拟执行（保持原样）
        """
        time.sleep(0.1)  # 模拟执行
        return {"success": True, "output": f"{task_type.capitalize()} task completed (simulation)"}


# 全局单例
_real_worker = None

def get_real_worker() -> RealWorker:
    """获取全局 RealWorker 实例"""
    global _real_worker
    if _real_worker is None:
        _real_worker = RealWorker()
    return _real_worker
