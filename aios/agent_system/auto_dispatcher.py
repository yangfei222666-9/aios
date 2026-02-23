"""
AIOS Agent System - Auto Dispatcher
自动任务分发器：监听事件 → 识别任务 → 路由到 Agent

集成点：
1. EventBus 订阅（感知层触发）
2. Heartbeat 轮询（定期检查）
3. Cron 定时（周期任务）
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 假设这些模块存在
try:
    from aios.core.event_bus import EventBus
except ImportError:
    EventBus = None

try:
    from aios.agent_system.circuit_breaker import CircuitBreaker
except ImportError:
    CircuitBreaker = None


class AutoDispatcher:
    """自动任务分发器"""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.queue_file = self.workspace / "aios" / "agent_system" / "task_queue.jsonl"
        self.state_file = self.workspace / "memory" / "agent_dispatch_state.json"
        self.log_file = self.workspace / "aios" / "agent_system" / "dispatcher.log"
        self.event_bus = EventBus() if EventBus else None

        # 熔断器
        breaker_file = (
            self.workspace / "aios" / "agent_system" / "circuit_breaker_state.json"
        )
        self.circuit_breaker = (
            CircuitBreaker(threshold=3, timeout=300, state_file=breaker_file)
            if CircuitBreaker
            else None
        )

        # Agent 模板配置
        self.agent_templates = {
            "code": {"model": "claude-opus-4-5", "label": "coder"},
            "analysis": {"model": "claude-sonnet-4-5", "label": "analyst"},
            "monitor": {"model": "claude-sonnet-4-5", "label": "monitor"},
            "research": {"model": "claude-sonnet-4-5", "label": "researcher"},
        }

        # 订阅事件
        if self.event_bus:
            self._subscribe_events()

    def _log(self, level: str, message: str, **kwargs):
        """写日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _subscribe_events(self):
        """订阅感知层事件"""
        if not self.event_bus:
            return

        # 文件变化 → coder
        self.event_bus.subscribe("sensor.file.*", self._on_file_change)

        # 系统告警 → monitor
        self.event_bus.subscribe("alert.*", self._on_alert)

        # 数据到达 → analyst
        self.event_bus.subscribe("sensor.data.*", self._on_data_arrival)

    def _on_file_change(self, event: Dict):
        """文件变化处理"""
        path = event.get("path", "")

        # 只处理代码文件
        if not any(path.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".rs"]):
            return

        # 如果是测试文件变化，触发测试任务
        if "test" in path.lower():
            self.enqueue_task(
                {
                    "type": "code",
                    "message": f"Run tests: {path}",
                    "priority": "high",
                    "source": "file_watcher",
                }
            )

    def _on_alert(self, event: Dict):
        """告警处理"""
        severity = event.get("severity", "info")

        if severity in ["warn", "crit"]:
            self.enqueue_task(
                {
                    "type": "monitor",
                    "message": f"Handle alert: {event.get('message', '')}",
                    "priority": "high" if severity == "crit" else "normal",
                    "source": "alert_system",
                }
            )

    def _on_data_arrival(self, event: Dict):
        """数据到达处理"""
        data_type = event.get("data_type", "")

        # 新数据需要分析
        self.enqueue_task(
            {
                "type": "analysis",
                "message": f"Analyze new data: {data_type}",
                "priority": "normal",
                "source": "data_sensor",
            }
        )

    def enqueue_task(self, task: Dict):
        """任务入队"""
        task["enqueued_at"] = datetime.now().isoformat()
        task["id"] = f"{int(time.time() * 1000)}"

        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

    def process_queue(self, max_tasks: int = 5) -> List[Dict]:
        """处理队列（心跳调用）"""
        if not self.queue_file.exists():
            return []

        # 读取所有待处理任务
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))

        if not tasks:
            return []

        # 按优先级排序
        priority_order = {"high": 0, "normal": 1, "low": 2}
        tasks.sort(key=lambda t: priority_order.get(t.get("priority", "normal"), 1))

        # 处理前 N 个任务
        processed = []
        remaining = []

        for i, task in enumerate(tasks):
            if i < max_tasks:
                result = self._dispatch_task(task)

                # 失败重试逻辑
                if result["status"] == "error":
                    retry_count = task.get("retry_count", 0)
                    max_retries = 3

                    if retry_count < max_retries:
                        # 重新入队，增加重试计数
                        task["retry_count"] = retry_count + 1
                        task["last_error"] = result.get("message", "unknown")
                        task["next_retry_after"] = (
                            datetime.now() + timedelta(minutes=2**retry_count)
                        ).isoformat()
                        remaining.append(task)
                        self._log(
                            "warn",
                            "Task retry scheduled",
                            task_id=task.get("id"),
                            retry=retry_count + 1,
                            max=max_retries,
                        )
                    else:
                        # 超过最大重试次数，记录失败
                        self._log(
                            "error",
                            "Task failed permanently",
                            task_id=task.get("id"),
                            retries=retry_count,
                        )

                processed.append({**task, "result": result})
            else:
                remaining.append(task)

        # 写回未处理的任务
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for task in remaining:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")

        return processed

    def _dispatch_task(self, task: Dict) -> Dict:
        """分发单个任务到 Agent（通过 sessions_spawn）"""
        task_type = task.get("type", "monitor")
        message = task["message"]

        # 熔断器检查
        if self.circuit_breaker and not self.circuit_breaker.should_execute(task_type):
            retry_after = (
                self.circuit_breaker.get_status()
                .get(task_type, {})
                .get("retry_after", 300)
            )
            self._log(
                "warn",
                "Circuit breaker open",
                task_id=task.get("id"),
                task_type=task_type,
                retry_after=retry_after,
            )
            return {
                "status": "circuit_open",
                "message": f"Circuit breaker open for {task_type}, retry after {retry_after}s",
            }

        # 获取模板配置
        template = self.agent_templates.get(task_type, self.agent_templates["monitor"])

        try:
            # 调用 OpenClaw sessions_spawn
            # 注意：这需要在 OpenClaw 环境中运行，不是独立 Python 脚本
            # 这里使用文件标记的方式，让主 Agent 在心跳时检测并执行

            spawn_request = {
                "task_id": task.get("id"),
                "task_type": task_type,
                "message": message,
                "model": template["model"],
                "label": template["label"],
                "timestamp": datetime.now().isoformat(),
            }

            # 写入待执行文件
            spawn_file = (
                self.workspace / "aios" / "agent_system" / "spawn_requests.jsonl"
            )
            spawn_file.parent.mkdir(parents=True, exist_ok=True)

            with open(spawn_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")

            self._log(
                "info",
                "Spawn request created",
                task_id=task.get("id"),
                task_type=task_type,
                model=template["model"],
                label=template["label"],
            )

            # 记录成功（重置熔断器）
            if self.circuit_breaker:
                self.circuit_breaker.record_success(task_type)

            return {
                "status": "pending",
                "agent": template["label"],
                "note": "Spawn request created, waiting for main agent to execute",
            }

        except Exception as e:
            error_msg = str(e)

            # 记录失败（触发熔断器）
            if self.circuit_breaker:
                self.circuit_breaker.record_failure(task_type)

            self._log(
                "error",
                "Dispatch exception",
                task_id=task.get("id"),
                error=error_msg,
                task_type=task_type,
            )

            return {"status": "error", "message": error_msg}

    def check_scheduled_tasks(self) -> List[Dict]:
        """检查定时任务（cron 调用）"""
        state = self._load_state()
        now = datetime.now()
        triggered = []

        # 每日任务：代码审查
        if self._should_run(state, "daily_code_review", hours=24):
            self.enqueue_task(
                {
                    "type": "code",
                    "message": "Run daily code review",
                    "priority": "normal",
                    "source": "cron_daily",
                }
            )
            triggered.append("daily_code_review")
            state["daily_code_review"] = now.isoformat()

        # 每周任务：性能分析
        if self._should_run(state, "weekly_performance", hours=168):
            self.enqueue_task(
                {
                    "type": "analysis",
                    "message": "Generate weekly performance report",
                    "priority": "normal",
                    "source": "cron_weekly",
                }
            )
            triggered.append("weekly_performance")
            state["weekly_performance"] = now.isoformat()

        # 每小时任务：待办检查
        if self._should_run(state, "hourly_todo_check", hours=1):
            self.enqueue_task(
                {
                    "type": "monitor",
                    "message": "Check todos and deadlines",
                    "priority": "low",
                    "source": "cron_hourly",
                }
            )
            triggered.append("hourly_todo_check")
            state["hourly_todo_check"] = now.isoformat()

        self._save_state(state)
        return triggered

    def _should_run(self, state: Dict, task_name: str, hours: int) -> bool:
        """判断任务是否应该运行"""
        last_run = state.get(task_name)
        if not last_run:
            return True

        last_time = datetime.fromisoformat(last_run)
        return datetime.now() - last_time >= timedelta(hours=hours)

    def _load_state(self) -> Dict:
        """加载状态"""
        if not self.state_file.exists():
            return {}

        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_state(self, state: Dict):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def status(self) -> Dict:
        """获取状态"""
        queue_size = 0
        if self.queue_file.exists():
            with open(self.queue_file, "r", encoding="utf-8") as f:
                queue_size = sum(1 for line in f if line.strip())

        state = self._load_state()

        # 熔断器状态
        breaker_status = {}
        if self.circuit_breaker:
            breaker_status = self.circuit_breaker.get_status()

        return {
            "queue_size": queue_size,
            "last_scheduled_tasks": state,
            "event_subscriptions": 3 if self.event_bus else 0,
            "circuit_breaker": breaker_status,
        }


def main():
    """CLI 入口"""
    import sys

    workspace = Path(__file__).parent.parent.parent
    dispatcher = AutoDispatcher(workspace)

    if len(sys.argv) < 2:
        print("Usage: python auto_dispatcher.py [heartbeat|cron|status]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "heartbeat":
        # 心跳调用：处理队列
        results = dispatcher.process_queue(max_tasks=5)
        if results:
            print(f"OK processed {len(results)} tasks")
            for r in results:
                status = r["result"]["status"]
                task_type = r["type"]
                print(f"  - {task_type}: {r['message'][:50]}... -> {status}")
        else:
            print("SKIP queue empty")

    elif cmd == "cron":
        # Cron 调用：检查定时任务
        triggered = dispatcher.check_scheduled_tasks()
        if triggered:
            print(f"OK triggered {len(triggered)} scheduled tasks")
            for t in triggered:
                print(f"  - {t}")
        else:
            print("SKIP no tasks due")

    elif cmd == "status":
        # 状态查询
        status = dispatcher.status()
        print(f"Auto Dispatcher Status")
        print(f"  Queue size: {status['queue_size']}")
        print(f"  Event subscriptions: {status['event_subscriptions']}")
        print(f"  Last scheduled tasks:")
        for task, time in status["last_scheduled_tasks"].items():
            print(f"    - {task}: {time}")

        # 熔断器状态
        breaker = status.get("circuit_breaker", {})
        if breaker:
            print(f"  Circuit Breaker:")
            for task_type, info in breaker.items():
                state = "🔴 OPEN" if info["circuit_open"] else "🟡 DEGRADED"
                print(
                    f"    - {task_type}: {state} (failures: {info['failure_count']}, retry: {info['retry_after']}s)"
                )
        else:
            print(f"  Circuit Breaker: All healthy")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
