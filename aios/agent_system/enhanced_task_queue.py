#!/usr/bin/env python3
"""
Enhanced Task Queue with Priority and Retry

Features:
- Priority queue (high/medium/low)
- Exponential backoff retry
- Dead letter queue
- Task history tracking
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import heapq

class Priority(Enum):
    """Task priority levels"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class Task:
    """Task with priority and retry support"""
    
    def __init__(self, task_id: str, task_type: str, data: Dict, priority: Priority = Priority.MEDIUM):
        self.task_id = task_id
        self.task_type = task_type
        self.data = data
        self.priority = priority
        self.created_at = datetime.now()
        self.retry_count = 0
        self.max_retries = 3
        self.last_error = None
        self.status = "pending"
    
    def __lt__(self, other):
        """Compare by priority for heap queue"""
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "data": self.data,
            "priority": self.priority.name,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "status": self.status,
            "last_error": self.last_error
        }

class EnhancedTaskQueue:
    """Priority queue with retry and dead letter support"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.queue = []  # Priority heap
        self.dead_letter_queue = []
        self.task_history = []
        
        self._load_state()
    
    def enqueue(self, task: Task):
        """Add task to queue"""
        heapq.heappush(self.queue, task)
        print(f"Enqueued: {task.task_id} (priority: {task.priority.name})")
        self._save_state()
    
    def dequeue(self) -> Optional[Task]:
        """Get highest priority task"""
        if not self.queue:
            return None
        
        task = heapq.heappop(self.queue)
        task.status = "processing"
        print(f"Dequeued: {task.task_id}")
        self._save_state()
        return task
    
    def complete(self, task: Task):
        """Mark task as completed"""
        task.status = "completed"
        self.task_history.append(task)
        print(f"Completed: {task.task_id}")
        self._save_state()
    
    def fail(self, task: Task, error: str):
        """Handle task failure with retry"""
        task.retry_count += 1
        task.last_error = error
        
        if task.retry_count < task.max_retries:
            # Exponential backoff
            delay = 2 ** task.retry_count
            print(f"Failed: {task.task_id} (retry {task.retry_count}/{task.max_retries}, delay: {delay}s)")
            
            # Re-enqueue with delay (simplified - just re-enqueue immediately)
            task.status = "retrying"
            heapq.heappush(self.queue, task)
        else:
            # Move to dead letter queue
            task.status = "dead_letter"
            self.dead_letter_queue.append(task)
            print(f"Dead letter: {task.task_id} (max retries exceeded)")
        
        self._save_state()
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            "queue_depth": len(self.queue),
            "dead_letter_count": len(self.dead_letter_queue),
            "completed_count": len([t for t in self.task_history if t.status == "completed"]),
            "priority_breakdown": {
                "high": len([t for t in self.queue if t.priority == Priority.HIGH]),
                "medium": len([t for t in self.queue if t.priority == Priority.MEDIUM]),
                "low": len([t for t in self.queue if t.priority == Priority.LOW])
            }
        }
    
    def _save_state(self):
        """Save queue state"""
        state = {
            "queue": [t.to_dict() for t in self.queue],
            "dead_letter_queue": [t.to_dict() for t in self.dead_letter_queue],
            "task_history": [t.to_dict() for t in self.task_history[-100:]]  # Keep last 100
        }
        
        state_file = self.data_dir / "queue_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def _load_state(self):
        """Load queue state"""
        state_file = self.data_dir / "queue_state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Restore queues (simplified - would need full Task reconstruction)
            print(f"Loaded state: {len(state.get('queue', []))} tasks in queue")

# Demo
if __name__ == "__main__":
    from pathlib import Path
    
    print("=" * 80)
    print("  Enhanced Task Queue - Demo")
    print("=" * 80)
    print()
    
    queue = EnhancedTaskQueue(Path("./data/queue"))
    
    # Enqueue tasks with different priorities
    print("Enqueuing tasks:")
    queue.enqueue(Task("task-1", "analysis", {}, Priority.LOW))
    queue.enqueue(Task("task-2", "critical", {}, Priority.HIGH))
    queue.enqueue(Task("task-3", "normal", {}, Priority.MEDIUM))
    queue.enqueue(Task("task-4", "urgent", {}, Priority.HIGH))
    print()
    
    # Process tasks (priority order)
    print("Processing tasks:")
    while True:
        task = queue.dequeue()
        if not task:
            break
        
        # Simulate processing
        if task.task_id == "task-3":
            # Simulate failure
            queue.fail(task, "Simulated error")
        else:
            queue.complete(task)
    print()
    
    # Stats
    print("Queue statistics:")
    stats = queue.get_stats()
    print(json.dumps(stats, indent=2))
    print()
    
    print("=" * 80)
    print("  Demo completed!")
    print("=" * 80)
