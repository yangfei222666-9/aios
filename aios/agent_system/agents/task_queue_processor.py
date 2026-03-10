"""Task Queue Processor - 鑷姩澶勭悊浠诲姟闃熷垪"""
import json
import time
from datetime import datetime
from pathlib import Path

class TaskQueueProcessor:
    def __init__(self):
        self.queue_file = Path("task_queue.jsonl")
        self.execution_file = Path(TASK_EXECUTIONS)
        self.max_tasks_per_run = 5
        
    def process_queue(self):
        """澶勭悊闃熷垪涓殑寰呭鐞嗕换鍔?""
        print("=" * 80)
        print("Task Queue Processor - 寮€濮嬪鐞嗕换鍔￠槦鍒?)
        print("=" * 80)
        
        # 璇诲彇闃熷垪
        tasks = self._load_queue()
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        
        if not pending_tasks:
            print("\n鉁?闃熷垪涓虹┖锛屾棤寰呭鐞嗕换鍔?)
            return
        
        print(f"\n鍙戠幇 {len(pending_tasks)} 涓緟澶勭悊浠诲姟")
        print(f"鏈澶勭悊鍓?{min(len(pending_tasks), self.max_tasks_per_run)} 涓换鍔n")
        
        # 鎸変紭鍏堢骇鎺掑簭
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        pending_tasks.sort(key=lambda t: priority_order.get(t.get("priority", "normal"), 2))
        
        # 澶勭悊浠诲姟
        processed = 0
        for task in pending_tasks[:self.max_tasks_per_run]:
            try:
                self._process_task(task)
                processed += 1
            except Exception as e:
                print(f"鉁?浠诲姟澶勭悊澶辫触: {e}")
        
        print(f"\n{'=' * 80}")
        print(f"澶勭悊瀹屾垚: {processed}/{min(len(pending_tasks), self.max_tasks_per_run)} 涓换鍔?)
        print(f"鍓╀綑寰呭鐞? {len(pending_tasks) - processed} 涓换鍔?)
        print(f"{'=' * 80}")
    
    def _process_task(self, task):
        """澶勭悊鍗曚釜浠诲姟"""
        task_id = task.get("id", "unknown")
        task_type = task.get("type", "unknown")
        priority = task.get("priority", "normal")
        desc = task.get("description", "鏃犳弿杩?)
        
        print(f"\n[{priority.upper()}] 澶勭悊浠诲姟: {task_id}")
        print(f"  绫诲瀷: {task_type}")
        print(f"  鎻忚堪: {desc}")
        
        # 璺敱鍒板搴?Agent
        agent = self._route_to_agent(task_type)
        print(f"  璺敱鍒? {agent}")
        
        # 鍒涘缓 spawn 璇锋眰
        spawn_request = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "task": desc,
            "task_id": task_id,
            "priority": priority,
            "status": "spawned"
        }
        
        # 鍐欏叆 spawn 璇锋眰
        with open("spawn_requests.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")
        
        # 鏇存柊浠诲姟鐘舵€?        task["status"] = "processing"
        task["started_at"] = datetime.now().isoformat()
        task["agent"] = agent
        self._update_task(task)
        
        print(f"  鉁?宸插垱寤?spawn 璇锋眰")
    
    def _route_to_agent(self, task_type):
        """鏍规嵁浠诲姟绫诲瀷璺敱鍒板搴?Agent"""
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
        """鍔犺浇浠诲姟闃熷垪"""
        if not self.queue_file.exists():
            return []
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        return tasks
    
    def _update_task(self, task):
        """鏇存柊浠诲姟鐘舵€?""
        tasks = self._load_queue()
        updated_tasks = []
        
        for t in tasks:
            if t.get("id") == task.get("id"):
                updated_tasks.append(task)
            else:
                updated_tasks.append(t)
        
        # 閲嶅啓闃熷垪
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for t in updated_tasks:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    processor = TaskQueueProcessor()
    processor.process_queue()


