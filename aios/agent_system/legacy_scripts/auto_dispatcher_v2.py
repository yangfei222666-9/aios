"""
AIOS Agent System - Auto Dispatcher (可观测层注入版)
自动任务分发器：监听事件 → 识别任务 → 路由到 Agent

[FIRE] 新增：完整可观测性（Tracer + Metrics + Logger）
"""

import json
import time
import sys
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ========== 可观测层导入（新增）==========
try:
    from aios.observability.tracer import start_trace, span, ensure_task_id, current_trace_id
    from aios.observability.metrics import METRICS
    from aios.observability.logger import get_logger
    OBSERVABILITY_ENABLED = True
except ImportError:
    OBSERVABILITY_ENABLED = False
    print("[WARN] Observability layer not available")
# ==========================================

# 添加当前目录到路径
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# 原有导入
try:
    from aios.core.event_bus import EventBus
except ImportError:
    EventBus = None

try:
    from aios.agent_system.circuit_breaker import CircuitBreaker
except ImportError:
    CircuitBreaker = None

SelfImprovingLoop = None
try:
    from self_improving_loop import SelfImprovingLoop
except ImportError:
    pass


class AutoDispatcher:
    """自动任务分发器（可观测增强版）"""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.queue_file = self.workspace / "aios" / "agent_system" / "task_queue.jsonl"
        self.state_file = self.workspace / "memory" / "agent_dispatch_state.json"
        self.log_file = self.workspace / "aios" / "agent_system" / "dispatcher.log"
        self.event_bus = EventBus() if EventBus else None
        self.improving_loop = SelfImprovingLoop() if SelfImprovingLoop else None
        
        # ========== 可观测层初始化（新增）==========
        if OBSERVABILITY_ENABLED:
            self._obs_logger = get_logger("auto_dispatcher", level="INFO")
        else:
            self._obs_logger = None
        # ==========================================
        
        # 熔断器
        breaker_file = self.workspace / "aios" / "agent_system" / "circuit_breaker_state.json"
        self.circuit_breaker = (
            CircuitBreaker(threshold=3, timeout=300, state_file=breaker_file)
            if CircuitBreaker else None
        )

        # Agent 模板配置
        self.agent_templates = {
            "code": {"model": "claude-opus-4-5", "label": "coder"},
            "analysis": {"model": "claude-sonnet-4-5", "label": "analyst"},
            "monitor": {"model": "claude-sonnet-4-5", "label": "monitor"},
            "research": {"model": "claude-sonnet-4-5", "label": "researcher"},
            "design": {"model": "claude-opus-4-5", "label": "designer"},
            "test": {"model": "claude-sonnet-4-5", "label": "tester"},
            "document": {"model": "claude-sonnet-4-5", "label": "documenter"},
            "debug": {"model": "claude-opus-4-5", "label": "debugger"},
            "search": {"model": "perplexity-sonar-pro", "label": "perplexity_search"},
            "deep_research": {"model": "perplexity-sonar-pro", "label": "perplexity_researcher"},
        }

        self.agent_configs = self._load_agent_configs()

        if self.event_bus:
            self._subscribe_events()

    def _load_agent_configs(self) -> Dict:
        """加载 Agent 配置"""
        config_file = self.workspace / "aios" / "agent_system" / "data" / "agent_configs.json"
        if not config_file.exists():
            return {}
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("agents", {})
        except Exception as e:
            self._log("error", f"Failed to load agent configs: {e}")
            return {}

    def _log(self, level: str, message: str, **kwargs):
        """写日志（兼容旧版）"""
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

        self.event_bus.subscribe("sensor.file.*", self._on_file_change)
        self.event_bus.subscribe("alert.*", self._on_alert)
        self.event_bus.subscribe("sensor.data.*", self._on_data_arrival)

    def _on_file_change(self, event: Dict):
        """文件变化处理"""
        path = event.get("path", "")
        if not any(path.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".rs"]):
            return

        if "test" in path.lower():
            self.enqueue_task({
                "type": "code",
                "message": f"Run tests: {path}",
                "priority": "high",
                "source": "file_watcher",
            })

    def _on_alert(self, event: Dict):
        """告警处理"""
        severity = event.get("severity", "info")
        if severity in ["warn", "crit"]:
            self.enqueue_task({
                "type": "monitor",
                "message": f"Handle alert: {event.get('message', '')}",
                "priority": "high" if severity == "crit" else "normal",
                "source": "alert_system",
            })

    def _on_data_arrival(self, event: Dict):
        """数据到达处理"""
        data_type = event.get("data_type", "")
        self.enqueue_task({
            "type": "analysis",
            "message": f"Analyze new data: {data_type}",
            "priority": "normal",
            "source": "data_sensor",
        })

    def enqueue_task(self, task: Dict):
        """任务入队"""
        task["enqueued_at"] = datetime.now().isoformat()
        task["id"] = f"{int(time.time() * 1000)}"
        task["status"] = "pending"
        
        if "priority" not in task:
            task["priority"] = "normal"

        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
        
        self._log("info", "Task enqueued", task_id=task["id"], type=task.get("type"), priority=task["priority"])

    def process_queue(self, max_tasks: int = 5) -> List[Dict]:
        """处理队列"""
        if not self.queue_file.exists():
            return []

        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    if "next_retry_after" in task:
                        retry_time = datetime.fromisoformat(task["next_retry_after"])
                        if datetime.now() < retry_time:
                            continue
                    tasks.append(task)

        if not tasks:
            return []

        # 按优先级排序
        priority_order = {"high": 0, "normal": 1, "low": 2}
        tasks.sort(key=lambda t: (
            priority_order.get(t.get("priority", "normal"), 1),
            t.get("enqueued_at", "")
        ))

        # 低优先级延迟处理
        high_normal_count = sum(1 for t in tasks if t.get("priority") in ["high", "normal"])
        if high_normal_count > 0:
            tasks = [t for t in tasks if t.get("priority") != "low"]

        processed = []
        remaining = []

        for i, task in enumerate(tasks):
            if i < max_tasks:
                try:
                    result = self._dispatch_task(task)
                    task["status"] = "dispatched"
                    processed.append({**task, "result": result})
                    
                    self._log("info", "Task dispatched", task_id=task.get("id"), priority=task.get("priority"), type=task.get("type"))
                    
                except Exception as e:
                    error_msg = str(e)
                    task_type = task.get("type", "monitor")
                    
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure(task_type)
                    
                    result = {"status": "error", "message": error_msg}
                    retry_count = task.get("retry_count", 0)
                    max_retries = 3

                    if retry_count < max_retries:
                        task["retry_count"] = retry_count + 1
                        task["last_error"] = error_msg
                        task["status"] = "retry_pending"
                        task["next_retry_after"] = (datetime.now() + timedelta(minutes=2**retry_count)).isoformat()
                        remaining.append(task)
                        self._log("warn", "Task retry scheduled", task_id=task.get("id"), retry=retry_count + 1, max=max_retries, next_retry=task["next_retry_after"][:19])
                    else:
                        task["status"] = "failed"
                        self._log("error", "Task failed permanently", task_id=task.get("id"), retries=retry_count)

                    processed.append({**task, "result": result})
            else:
                remaining.append(task)

        # 写回未处理的任务
        all_remaining = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    if "next_retry_after" in task and task not in tasks:
                        all_remaining.append(task)
        
        all_remaining.extend(remaining)
        
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for task in all_remaining:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")

        return processed

    def _dispatch_task(self, task: Dict) -> Dict:
        """
        分发单个任务（可观测增强版）
        
        [FIRE] 新增：完整的 Trace + Metrics + Logger + Events
        """
        # ========== 可观测层注入开始 ==========
        if OBSERVABILITY_ENABLED:
            # 强约束：task_id 永远非空
            task_id = ensure_task_id(task)
            task_type = task.get("type", "monitor")
            message = task.get("message", "")
            priority = task.get("priority", "normal")
            
            logger = self._obs_logger
            
            # 开始 Trace
            with start_trace("dispatch_task", attributes={"task_id": task_id, "type": task_type, "priority": priority}):
                t0 = time.perf_counter()
                
                logger.info("Task received", task_id=task_id, type=task_type, priority=priority)
                logger.emit_event("task_received", task_id=task_id, severity="info", payload={
                    "type": task_type,
                    "priority": priority,
                })
                METRICS.inc_counter("tasks.received", labels={"type": task_type, "priority": priority})
                
                try:
                    # ========== 原有逻辑 ==========
                    agent_id = f"{task_type}-dispatcher"

                    if self.improving_loop:
                        result = self.improving_loop.execute_with_improvement(
                            agent_id=agent_id,
                            task=message,
                            execute_fn=lambda: self._do_dispatch(task, task_type, message),
                            context={"task_id": task_id, "task_type": task_type}
                        )

                        if result.get("improvement_triggered"):
                            self._log("info", "Self-improvement triggered", agent_id=agent_id, improvements=result.get("improvement_applied", 0))

                        if result["success"]:
                            final_result = result["result"]
                        else:
                            final_result = {"status": "error", "message": result.get("error", "unknown")}
                    else:
                        final_result = self._do_dispatch(task, task_type, message)
                    # ========== 原有逻辑结束 ==========
                    
                    # ========== 可观测层：成功 ==========
                    logger.info("Task dispatched", task_id=task_id, type=task_type, priority=priority)
                    logger.emit_event("task_dispatched", task_id=task_id, severity="info", payload={
                        "type": task_type,
                        "priority": priority,
                    })
                    METRICS.inc_counter("tasks.dispatched", labels={"type": task_type, "priority": priority})
                    
                    return final_result
                    
                except Exception as e:
                    # ========== 可观测层：失败 ==========
                    logger.exception("Dispatch failed", task_id=task_id, type=task_type, priority=priority, 
                                   error_type=type(e).__name__, message=str(e))
                    logger.emit_event("error", task_id=task_id, severity="error", payload={
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                        "type": task_type,
                        "priority": priority,
                    })
                    METRICS.inc_counter("tasks.failed", labels={"type": task_type, "priority": priority})
                    raise
                    
                finally:
                    # ========== 可观测层：指标 ==========
                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    METRICS.observe("dispatch.latency_ms", latency_ms, labels={"type": task_type, "priority": priority})
        else:
            # 可观测层未启用，使用原有逻辑
            task_type = task.get("type", "monitor")
            message = task.get("message", "")
            task_id = task.get("id", "unknown")
            agent_id = f"{task_type}-dispatcher"

            if self.improving_loop:
                result = self.improving_loop.execute_with_improvement(
                    agent_id=agent_id,
                    task=message,
                    execute_fn=lambda: self._do_dispatch(task, task_type, message),
                    context={"task_id": task_id, "task_type": task_type}
                )

                if result.get("improvement_triggered"):
                    self._log("info", "Self-improvement triggered", agent_id=agent_id, improvements=result.get("improvement_applied", 0))

                if result["success"]:
                    return result["result"]
                else:
                    return {"status": "error", "message": result.get("error", "unknown")}
            else:
                return self._do_dispatch(task, task_type, message)
        # ========== 可观测层注入结束 ==========

    def _do_dispatch(self, task: Dict, task_type: str, message: str) -> Dict:
        """
        实际的任务分发逻辑（可观测增强版）
        
        [FIRE] 新增：Circuit Breaker 结构化日志
        """
        # ========== 可观测层：ensure_task_id（新增）==========
        if OBSERVABILITY_ENABLED:
            task_id = ensure_task_id(task)
            logger = self._obs_logger
        else:
            task_id = task.get("id", "unknown")
            logger = None
        # ==========================================
        
        # 熔断器检查（增强版）
        if self.circuit_breaker and not self.circuit_breaker.should_execute(task_type):
            breaker_status = self.circuit_breaker.get_status().get(task_type, {})
            retry_after = breaker_status.get("retry_after", 300)
            fail_count = breaker_status.get("failure_count", 0)
            
            # ========== 可观测层：Circuit Breaker 日志（新增）==========
            if logger:
                logger.warn(
                    "Circuit breaker open",
                    task_id=task_id,
                    task_type=task_type,
                    retry_after=retry_after,
                    reason="consecutive_failures",
                    fail_count=fail_count,
                    cooldown_sec=retry_after,
                )
                logger.emit_event("circuit_breaker_open", task_id=task_id, agent_id=f"{task_type}-dispatcher", 
                                severity="warn", payload={
                                    "task_type": task_type,
                                    "retry_after": retry_after,
                                    "fail_count": fail_count,
                                })
                METRICS.inc_counter("circuit_breaker.open", labels={"type": task_type})
            # ==========================================
            
            self._log("warn", "Circuit breaker open", task_id=task_id, task_type=task_type, retry_after=retry_after)
            raise Exception(f"Circuit breaker open for {task_type}, retry after {retry_after}s")

        # 获取模板配置
        template = self.agent_templates.get(task_type, self.agent_templates["monitor"])

        # 查找 Agent 配置
        agent_config = None
        for agent_id, config in self.agent_configs.items():
            if config.get("type") == template["label"] and config.get("env") == "prod":
                agent_config = config
                break

        # 构建增强消息
        enhanced_message = message
        if agent_config:
            role = agent_config.get("role", "")
            goal = agent_config.get("goal", "")
            backstory = agent_config.get("backstory", "")
            
            if role or goal or backstory:
                role_prompt = f"""
# Your Role
{f"**Role:** {role}" if role else ""}
{f"**Goal:** {goal}" if goal else ""}
{f"**Backstory:** {backstory}" if backstory else ""}

# Your Task
{message}
"""
                enhanced_message = role_prompt.strip()

        # 创建 spawn request
        spawn_request = {
            "task_id": task_id,
            "task_type": task_type,
            "message": enhanced_message,
            "model": template["model"],
            "label": template["label"],
            "timestamp": datetime.now().isoformat(),
            "role": agent_config.get("role") if agent_config else None,
            "goal": agent_config.get("goal") if agent_config else None,
        }

        spawn_file = self.workspace / "aios" / "agent_system" / "spawn_requests.jsonl"
        spawn_file.parent.mkdir(parents=True, exist_ok=True)

        with open(spawn_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")

        self._log("info", "Spawn request created", task_id=task_id, task_type=task_type, model=template["model"], label=template["label"], role=agent_config.get("role") if agent_config else None)

        # 记录成功（重置熔断器）
        if self.circuit_breaker:
            self.circuit_breaker.record_success(task_type)

        return {
            "status": "pending",
            "agent": template["label"],
            "note": "Spawn request created, waiting for main agent to execute",
        }

    def check_scheduled_tasks(self) -> List[Dict]:
        """检查定时任务"""
        state = self._load_state()
        now = datetime.now()
        triggered = []

        if self._should_run(state, "daily_code_review", hours=24):
            self.enqueue_task({"type": "code", "message": "Run daily code review", "priority": "normal", "source": "cron_daily"})
            triggered.append("daily_code_review")
            state["daily_code_review"] = now.isoformat()

        if self._should_run(state, "weekly_performance", hours=168):
            self.enqueue_task({"type": "analysis", "message": "Generate weekly performance report", "priority": "normal", "source": "cron_weekly"})
            triggered.append("weekly_performance")
            state["weekly_performance"] = now.isoformat()

        if self._should_run(state, "hourly_todo_check", hours=1):
            self.enqueue_task({"type": "monitor", "message": "Check todos and deadlines", "priority": "low", "source": "cron_hourly"})
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

        breaker_status = {}
        if self.circuit_breaker:
            breaker_status = self.circuit_breaker.get_status()

        improvement_stats = {}
        if self.improving_loop:
            improvement_stats = self.improving_loop.get_improvement_stats()

        return {
            "queue_size": queue_size,
            "last_scheduled_tasks": state,
            "event_subscriptions": 3 if self.event_bus else 0,
            "circuit_breaker": breaker_status,
            "self_improving": improvement_stats,
            "observability": "enabled" if OBSERVABILITY_ENABLED else "disabled",  # 新增
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
        results = dispatcher.process_queue(max_tasks=5)
        if results:
            print(f"OK processed {len(results)} tasks")
            for r in results:
                status = r["result"]["status"]
                task_type = r.get("type") or r.get("task_type", "unknown")
                desc = r.get("description", r.get("message", ""))[:50]
                print(f"  - {task_type}: {desc}... -> {status}")
        else:
            print("SKIP queue empty")

    elif cmd == "cron":
        triggered = dispatcher.check_scheduled_tasks()
        if triggered:
            print(f"OK triggered {len(triggered)} scheduled tasks")
            for t in triggered:
                print(f"  - {t}")
        else:
            print("SKIP no tasks due")

    elif cmd == "status":
        status = dispatcher.status()
        print(f"Auto Dispatcher Status")
        print(f"  Queue size: {status['queue_size']}")
        print(f"  Event subscriptions: {status['event_subscriptions']}")
        print(f"  Observability: {status.get('observability', 'unknown')}")  # 新增
        print(f"  Last scheduled tasks:")
        for task, time in status["last_scheduled_tasks"].items():
            print(f"    - {task}: {time}")

        breaker = status.get("circuit_breaker", {})
        if breaker:
            print(f"  Circuit Breaker:")
            for task_type, info in breaker.items():
                state = "OPEN" if info["circuit_open"] else "HEALTHY"
                print(f"    - {task_type}: {state} (failures: {info['failure_count']}, retry: {info['retry_after']}s)")
        else:
            print(f"  Circuit Breaker: All healthy")

        improving = status.get("self_improving", {})
        if improving:
            print(f"  Self-Improving Loop:")
            print(f"    - Total agents: {improving.get('total_agents', 0)}")
            print(f"    - Total improvements: {improving.get('total_improvements', 0)}")
            improved = improving.get("agents_improved", [])
            if improved:
                print(f"    - Improved agents: {', '.join(improved[:5])}")
                if len(improved) > 5:
                    print(f"      ... and {len(improved) - 5} more")
        else:
            print(f"  Self-Improving Loop: Not available")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
