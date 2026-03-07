"""Task Queue Processor - 自动处理任务队列"""
import json
import time
from datetime import datetime
from pathlib import Path

class TaskQueueProcessor:
    def __init__(self):
        self.queue_file = Path("task_queue.jsonl")
        self.execution_file = Path("task_executions.jsonl")
        self.max_tasks_per_run = 5
        
    def process_queue(self):
        """处理队列中的待处理任务"""
        print("=" * 80)
        print("Task Queue Processor - 开始处理任务队列")
        print("=" * 80)
        
        # 读取队列
        tasks = self._load_queue()
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        
        if not pending_tasks:
            print("\n✓ 队列为空，无待处理任务")
            return
        
        print(f"\n发现 {len(pending_tasks)} 个待处理任务")
        print(f"本次处理前 {min(len(pending_tasks), self.max_tasks_per_run)} 个任务\n")
        
        # 按优先级排序
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        pending_tasks.sort(key=lambda t: priority_order.get(t.get("priority", "normal"), 2))
        
        # 处理任务
        processed = 0
        for task in pending_tasks[:self.max_tasks_per_run]:
            try:
                self._process_task(task)
                processed += 1
            except Exception as e:
                print(f"✗ 任务处理失败: {e}")
        
        print(f"\n{'=' * 80}")
        print(f"处理完成: {processed}/{min(len(pending_tasks), self.max_tasks_per_run)} 个任务")
        print(f"剩余待处理: {len(pending_tasks) - processed} 个任务")
        print(f"{'=' * 80}")
    
    def _process_task(self, task):
        """处理单个任务"""
        task_id = task.get("id", "unknown")
        task_type = task.get("type", "unknown")
        priority = task.get("priority", "normal")
        desc = task.get("description", "无描述")
        
        print(f"\n[{priority.upper()}] 处理任务: {task_id}")
        print(f"  类型: {task_type}")
        print(f"  描述: {desc}")
        
        # 路由到对应 Agent
        agent = self._route_to_agent(task_type)
        print(f"  路由到: {agent}")
        
        # 创建 spawn 请求
        spawn_request = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "task": desc,
            "task_id": task_id,
            "priority": priority,
            "status": "spawned"
        }
        
        # 写入 spawn 请求
        with open("spawn_requests.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")
        
        # 更新任务状态
        task["status"] = "processing"
        task["started_at"] = datetime.now().isoformat()
        task["agent"] = agent
        self._update_task(task)
        
        print(f"  ✓ 已创建 spawn 请求")
    
    def _route_to_agent(self, task_type):
        """根据任务类型路由到对应 Agent"""
        routing = {
            "code": "coder-dispatcher",
            "analysis": "analyst-dispatcher",
            "monitor": "monitor-dispatcher",
            "test": "coder-dispatcher",
            "refactor": "coder-dispatcher",
            "debug": "coder-dispatcher",
            "review": "analyst-dispatcher",
            "report": "analyst-dispatcher"
        }
        return routing.get(task_type, "coder-dispatcher")
    
    def _load_queue(self):
        """加载任务队列"""
        if not self.queue_file.exists():
            return []
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        return tasks
    
    def _update_task(self, task):
        """更新任务状态"""
        tasks = self._load_queue()
        updated_tasks = []
        
        for t in tasks:
            if t.get("id") == task.get("id"):
                updated_tasks.append(task)
            else:
                updated_tasks.append(t)
        
        # 重写队列
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for t in updated_tasks:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    processor = TaskQueueProcessor()
    processor.process_queue()
