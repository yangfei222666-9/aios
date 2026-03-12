"""
Task Queue Manager - 统一任务队列写入接口
提供幂等保护和来源追踪
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from core.status_adapter import get_task_status


class TaskQueueManager:
    """任务队列管理器 - 统一写入入口，提供幂等保护"""
    
    def __init__(self, queue_file: Path = None, dedup_window_minutes: int = 60):
        """
        Args:
            queue_file: 队列文件路径，默认 data/task_queue.jsonl
            dedup_window_minutes: 去重时间窗口（分钟）
        """
        if queue_file is None:
            queue_file = Path(__file__).parent / "data" / "task_queue.jsonl"
        
        self.queue_file = queue_file
        self.dedup_window = timedelta(minutes=dedup_window_minutes)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
    
    def enqueue_task(self, task: Dict, source: str) -> Dict:
        """
        统一任务入队接口
        
        Args:
            task: 任务对象（必须包含 id/description/type）
            source: 来源标识（auto_dispatcher/task_scheduler/heartbeat/manual/recovery_agent）
        
        Returns:
            {
                "success": bool,
                "action": "enqueued" | "skipped_duplicate" | "skipped_pending",
                "task_id": str,
                "dedup_key": str,
                "reason": str (if skipped)
            }
        """
        # 1. 补充元数据
        task_id = task.get("id")
        if not task_id:
            return {
                "success": False,
                "action": "error",
                "reason": "Missing task id"
            }
        
        # 2. 计算 dedup_key
        dedup_key = self._calculate_dedup_key(task)
        
        # 3. 检查是否已存在
        existing = self._check_existing(task_id, dedup_key)
        if existing:
            return {
                "success": False,
                "action": existing["action"],
                "task_id": task_id,
                "dedup_key": dedup_key,
                "reason": existing["reason"]
            }
        
        # 4. 补充来源和时间戳
        task["source"] = source
        task["created_by"] = f"{source}.py"
        task["enqueued_at"] = datetime.now().isoformat()
        task["dedup_key"] = dedup_key
        
        # 5. 写入队列
        with open(self.queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
        
        return {
            "success": True,
            "action": "enqueued",
            "task_id": task_id,
            "dedup_key": dedup_key
        }
    
    def _calculate_dedup_key(self, task: Dict) -> str:
        """
        计算去重键
        
        优先使用 task_id，如果不可靠则使用 hash(task_type + description + workflow_id)
        """
        task_id = task.get("id")
        if task_id:
            return f"id:{task_id}"
        
        # 退化方案：基于内容 hash
        task_type = task.get("type", "")
        description = task.get("description", "")
        workflow_id = task.get("workflow_id", "")
        
        content = f"{task_type}|{description}|{workflow_id}"
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"hash:{content_hash}"
    
    def _check_existing(self, task_id: str, dedup_key: str) -> Optional[Dict]:
        """
        检查是否已存在
        
        Returns:
            None if not exists, else {"action": str, "reason": str}
        """
        if not self.queue_file.exists():
            return None
        
        now = datetime.now()
        
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    existing_task = json.loads(line)
                except Exception:
                    continue
                
                # 检查 1：相同 task_id 且状态未终结
                if existing_task.get("id") == task_id:
                    status = get_task_status(existing_task)
                    if status not in ["completed", "failed", "cancelled"]:
                        return {
                            "action": "skipped_pending",
                            "reason": f"Task {task_id} already exists with status={status}"
                        }
                
                # 检查 2：相同 dedup_key 且时间窗口很近
                if existing_task.get("dedup_key") == dedup_key:
                    enqueued_at = existing_task.get("enqueued_at") or existing_task.get("created_at")
                    if enqueued_at:
                        try:
                            if isinstance(enqueued_at, (int, float)):
                                enqueued_time = datetime.fromtimestamp(enqueued_at)
                            else:
                                enqueued_time = datetime.fromisoformat(enqueued_at)
                            
                            if now - enqueued_time < self.dedup_window:
                                return {
                                    "action": "skipped_duplicate",
                                    "reason": f"Duplicate task within {self.dedup_window.total_seconds()/60:.0f}min window (dedup_key={dedup_key})"
                                }
                        except Exception:
                            pass
        
        return None
    
    def get_pending_tasks(self, limit: int = None) -> List[Dict]:
        """获取待处理任务"""
        if not self.queue_file.exists():
            return []
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    task = json.loads(line)
                    if get_task_status(task) in ["queued", "pending", None]:
                        tasks.append(task)
                        if limit and len(tasks) >= limit:
                            break
                except Exception:
                    continue
        
        return tasks


class SpawnRequestManager:
    """Spawn 请求管理器 - 统一写入入口，提供幂等保护"""
    
    def __init__(self, spawn_file: Path = None, dedup_window_minutes: int = 60):
        """
        Args:
            spawn_file: spawn 请求文件路径，默认 data/spawn_requests.jsonl
            dedup_window_minutes: 去重时间窗口（分钟）
        """
        if spawn_file is None:
            spawn_file = Path(__file__).parent / "data" / "spawn_requests.jsonl"
        
        self.spawn_file = spawn_file
        self.dedup_window = timedelta(minutes=dedup_window_minutes)
        self.spawn_file.parent.mkdir(parents=True, exist_ok=True)
    
    def create_spawn_request(self, request: Dict, source: str) -> Dict:
        """
        统一 spawn 请求创建接口
        
        Args:
            request: spawn 请求对象（必须包含 task_id/agent_id）
            source: 来源标识（auto_dispatcher/task_scheduler/recovery_agent）
        
        Returns:
            {
                "success": bool,
                "action": "created" | "skipped_duplicate",
                "spawn_id": str,
                "dedup_key": str,
                "reason": str (if skipped)
            }
        """
        # 1. 补充元数据
        task_id = request.get("task_id")
        if not task_id:
            return {
                "success": False,
                "action": "error",
                "reason": "Missing task_id"
            }
        
        # 2. 计算 dedup_key
        dedup_key = self._calculate_dedup_key(request)
        
        # 3. 检查是否已存在
        existing = self._check_existing(task_id, dedup_key)
        if existing:
            return {
                "success": False,
                "action": existing["action"],
                "spawn_id": request.get("spawn_id", task_id),
                "dedup_key": dedup_key,
                "reason": existing["reason"]
            }
        
        # 4. 补充来源和时间戳
        request["source"] = source
        request["created_by"] = f"{source}.py"
        request["timestamp"] = datetime.now().isoformat()
        request["dedup_key"] = dedup_key
        
        # 5. 写入 spawn 请求
        with open(self.spawn_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(request, ensure_ascii=False) + "\n")
        
        # Tracing: spawn_requested
        try:
            from tracer import trace_event
            trace_event(
                trace_id=request.get("trace_id", f"trace-{task_id}"),
                task_id=task_id,
                step_name="spawn_requested",
                source=source,
                agent_name=request.get("agent_id", ""),
                result_summary=f"spawn request created, dedup_key={dedup_key}",
            )
        except Exception:
            pass  # trace 写失败不阻塞主流程
        
        return {
            "success": True,
            "action": "created",
            "spawn_id": request.get("spawn_id", task_id),
            "dedup_key": dedup_key
        }
    
    def _calculate_dedup_key(self, request: Dict) -> str:
        """
        计算去重键
        
        优先使用 task_id + workflow_id，如果不可靠则使用 hash(agent_id + task + label)
        """
        task_id = request.get("task_id")
        workflow_id = request.get("workflow_id")
        
        if task_id:
            if workflow_id:
                return f"id:{task_id}:wf:{workflow_id}"
            return f"id:{task_id}"
        
        # 退化方案：基于内容 hash
        agent_id = request.get("agent_id", "")
        task = request.get("task", "")
        label = request.get("label", "")
        
        content = f"{agent_id}|{task}|{label}"
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"hash:{content_hash}"
    
    def _check_existing(self, task_id: str, dedup_key: str) -> Optional[Dict]:
        """
        检查是否已存在
        
        Returns:
            None if not exists, else {"action": str, "reason": str}
        """
        if not self.spawn_file.exists():
            return None
        
        now = datetime.now()
        
        with open(self.spawn_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    existing_request = json.loads(line)
                except Exception:
                    continue
                
                # 检查 1：相同 task_id/workflow_id
                if existing_request.get("task_id") == task_id:
                    return {
                        "action": "skipped_duplicate",
                        "reason": f"Spawn request for task_id={task_id} already exists"
                    }
                
                # 检查 2：相同 dedup_key 且时间窗口很近
                if existing_request.get("dedup_key") == dedup_key:
                    timestamp = existing_request.get("timestamp")
                    if timestamp:
                        try:
                            if isinstance(timestamp, (int, float)):
                                request_time = datetime.fromtimestamp(timestamp)
                            else:
                                request_time = datetime.fromisoformat(timestamp)
                            
                            if now - request_time < self.dedup_window:
                                return {
                                    "action": "skipped_duplicate",
                                    "reason": f"Duplicate spawn request within {self.dedup_window.total_seconds()/60:.0f}min window (dedup_key={dedup_key})"
                                }
                        except Exception:
                            pass
        
        return None


# 使用示例
if __name__ == "__main__":
    # 测试任务队列管理器
    queue_mgr = TaskQueueManager()
    
    task = {
        "id": "test-task-001",
        "description": "Test task",
        "type": "code",
        "priority": "normal"
    }
    
    result = queue_mgr.enqueue_task(task, source="auto_dispatcher")
    print(f"Enqueue result: {result}")
    
    # 测试重复入队
    result2 = queue_mgr.enqueue_task(task, source="task_scheduler")
    print(f"Duplicate enqueue result: {result2}")
    
    # 测试 spawn 请求管理器
    spawn_mgr = SpawnRequestManager()
    
    spawn_request = {
        "task_id": "test-task-001",
        "agent_id": "coder-dispatcher",
        "task": "Test spawn request",
        "label": "test-spawn"
    }
    
    result3 = spawn_mgr.create_spawn_request(spawn_request, source="auto_dispatcher")
    print(f"Spawn request result: {result3}")
    
    # 测试重复 spawn
    result4 = spawn_mgr.create_spawn_request(spawn_request, source="task_scheduler")
    print(f"Duplicate spawn request result: {result4}")
