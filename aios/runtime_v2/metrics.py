"""
Runtime Instrumentation - Telemetry & Metrics

从 event log 提取关键指标：
1. Queue wait time (task_started - task_created)
2. Execution time (task_completed - task_started)
3. Throughput (tasks / minute)
4. Worker utilization (running_workers / max_workers)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from .event_log import get_event_log
from .state import get_state


class RuntimeMetrics:
    def __init__(self):
        self.event_log = get_event_log()
        self.state = get_state()
    
    def get_queue_wait_time(self, task_id: str) -> float:
        """
        计算任务的队列等待时间（秒）
        
        Returns:
            wait_time (seconds) or None
        """
        events = self.event_log.read_events()
        
        task_created_time = None
        task_started_time = None
        
        for event in events:
            if event["task_id"] == task_id:
                if event["event_type"] == "task_created":
                    task_created_time = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
                elif event["event_type"] == "task_started":
                    task_started_time = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
        
        if task_created_time and task_started_time:
            return (task_started_time - task_created_time).total_seconds()
        return None
    
    def get_execution_time(self, task_id: str) -> float:
        """
        计算任务的执行时间（秒）
        
        Returns:
            execution_time (seconds) or None
        """
        events = self.event_log.read_events()
        
        task_started_time = None
        task_completed_time = None
        
        for event in events:
            if event["task_id"] == task_id:
                if event["event_type"] == "task_started":
                    task_started_time = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
                elif event["event_type"] in ["task_completed", "task_failed", "task_timeout"]:
                    task_completed_time = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
        
        if task_started_time and task_completed_time:
            return (task_completed_time - task_started_time).total_seconds()
        return None
    
    def get_throughput(self, window_minutes: int = 5) -> float:
        """
        计算吞吐量（tasks / minute）
        
        Args:
            window_minutes: 时间窗口（分钟）
        
        Returns:
            throughput (tasks/min)
        """
        events = self.event_log.read_events()
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        completed_count = 0
        for event in events:
            if event["event_type"] in ["task_completed", "task_failed"]:
                event_time = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
                if event_time >= window_start:
                    completed_count += 1
        
        return completed_count / window_minutes if window_minutes > 0 else 0
    
    def get_worker_utilization(self, max_workers: int = 5) -> float:
        """
        计算 worker 利用率
        
        Returns:
            utilization (0.0 - 1.0)
        """
        running_tasks = self.state.list_running_tasks()
        return len(running_tasks) / max_workers if max_workers > 0 else 0
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标
        
        Returns:
            {
                "queue_wait_time_avg": 1.23,
                "execution_time_avg": 0.45,
                "throughput": 12.5,
                "worker_utilization": 0.6,
                "pending_tasks": 3,
                "running_tasks": 2,
                "completed_tasks": 10,
                "failed_tasks": 1
            }
        """
        # 计算平均队列等待时间
        completed_tasks = self.state.list_completed_tasks()
        failed_tasks = self.state.list_failed_tasks()
        all_finished = completed_tasks + failed_tasks
        
        wait_times = []
        exec_times = []
        
        for task in all_finished:
            task_id = task["task_id"]
            
            wait_time = self.get_queue_wait_time(task_id)
            if wait_time is not None:
                wait_times.append(wait_time)
            
            exec_time = self.get_execution_time(task_id)
            if exec_time is not None:
                exec_times.append(exec_time)
        
        return {
            "queue_wait_time_avg": sum(wait_times) / len(wait_times) if wait_times else 0,
            "execution_time_avg": sum(exec_times) / len(exec_times) if exec_times else 0,
            "throughput": self.get_throughput(window_minutes=5),
            "worker_utilization": self.get_worker_utilization(),
            "pending_tasks": len(self.state.list_pending_tasks()),
            "running_tasks": len(self.state.list_running_tasks()),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks)
        }
    
    def print_metrics(self):
        """打印所有指标"""
        metrics = self.get_all_metrics()
        
        print("=" * 60)
        print("Runtime Metrics")
        print("=" * 60)
        print(f"Queue Wait Time (avg): {metrics['queue_wait_time_avg']:.3f}s")
        print(f"Execution Time (avg): {metrics['execution_time_avg']:.3f}s")
        print(f"Throughput: {metrics['throughput']:.2f} tasks/min")
        print(f"Worker Utilization: {metrics['worker_utilization']:.1%}")
        print()
        print(f"Pending: {metrics['pending_tasks']}")
        print(f"Running: {metrics['running_tasks']}")
        print(f"Completed: {metrics['completed_tasks']}")
        print(f"Failed: {metrics['failed_tasks']}")
        print("=" * 60)


# 全局单例
_metrics = None

def get_metrics() -> RuntimeMetrics:
    """获取全局 RuntimeMetrics 实例"""
    global _metrics
    if _metrics is None:
        _metrics = RuntimeMetrics()
    return _metrics


if __name__ == "__main__":
    # 直接运行：python -m aios.runtime_v2.metrics
    metrics = get_metrics()
    metrics.print_metrics()
