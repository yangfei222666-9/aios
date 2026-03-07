"""Task Scheduler Agent - 智能任务调度"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from task_queue_manager import TaskQueueManager, SpawnRequestManager


class TaskScheduler:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.queue_file = self.base_dir / "data" / "task_queue.jsonl"
        self.spawn_file = self.base_dir / "data" / "spawn_requests.jsonl"
        self.duplicate_log = self.base_dir / "data" / "duplicate_enqueue_attempts.jsonl"
        self.agents_file = self.base_dir / "agents.json"
        self.dependency_file = self.base_dir / "data" / "dependencies" / "task_dependencies.json"
        self.queue_manager = TaskQueueManager(queue_file=self.queue_file)
        self.spawn_manager = SpawnRequestManager(spawn_file=self.spawn_file)

    def schedule(self):
        """智能调度任务"""
        print("=" * 80)
        print("Task Scheduler - 智能任务调度")
        print("=" * 80)

        tasks = self._load_tasks()
        agents = self._load_agents()
        dependencies = self._load_dependencies()

        print(f"\n📋 待调度任务: {len(tasks)} 个")
        print(f"🤖 可用 Agent: {len(agents)} 个")

        ready_tasks = self._filter_ready_tasks(tasks, dependencies)
        print(f"✓ 可立即执行: {len(ready_tasks)} 个")

        if not ready_tasks:
            print("\n✓ 没有可执行的任务")
            return

        scored_tasks = self._score_tasks(ready_tasks, agents)
        sorted_tasks = sorted(scored_tasks, key=lambda x: x["score"], reverse=True)
        schedule = self._generate_schedule(sorted_tasks, agents)
        self._display_schedule(schedule)
        self._execute_schedule(schedule)

        print(f"\n{'=' * 80}")

    def _load_tasks(self) -> List[Dict]:
        """加载任务队列"""
        return self.queue_manager.get_pending_tasks()

    def _load_agents(self):
        """加载可用 Agent"""
        if not self.agents_file.exists():
            return []

        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        agents = data if isinstance(data, list) else data.get("agents", [])
        return [a for a in agents if a.get("enabled", True)]

    def _load_dependencies(self):
        """加载依赖关系"""
        if not self.dependency_file.exists():
            return {}

        with open(self.dependency_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _filter_ready_tasks(self, tasks, dependencies):
        """过滤可执行任务（无依赖或依赖已完成）"""
        return tasks

    def _score_tasks(self, tasks, agents):
        """计算任务优先级分数"""
        scored = []

        for task in tasks:
            score = 0
            priority_scores = {"urgent": 100, "high": 75, "normal": 50, "low": 25}
            score += priority_scores.get(task.get("priority", "normal"), 50) * 0.4

            created_at_raw = task.get("created_at") or task.get("enqueued_at") or datetime.now().isoformat()
            try:
                created_at = datetime.fromisoformat(created_at_raw)
            except Exception:
                created_at = datetime.now()
            wait_hours = (datetime.now() - created_at).total_seconds() / 3600
            score += min(wait_hours * 5, 100) * 0.3

            agent_available = self._check_agent_availability(task, agents)
            score += (100 if agent_available else 0) * 0.2

            type_scores = {"urgent": 100, "code": 80, "analysis": 60, "monitor": 40, "test": 50}
            score += type_scores.get(task.get("type", "code"), 50) * 0.1

            scored.append({"task": task, "score": score})

        return scored

    def _check_agent_availability(self, task, agents):
        """检查 Agent 是否可用"""
        task_type = task.get("type", "code")
        routing = {
            "code": ["coder-dispatcher", "Coder"],
            "analysis": ["analyst-dispatcher", "Analyst"],
            "monitor": ["monitor-dispatcher", "Monitor"],
            "test": ["coder-dispatcher", "Coder"],
        }
        required_agents = routing.get(task_type, [])

        for agent in agents:
            agent_name = agent.get("name", "")
            if any(req in agent_name for req in required_agents):
                return True
        return False

    def _generate_schedule(self, sorted_tasks, agents):
        """生成调度计划（考虑并发限制）"""
        schedule = []
        max_concurrent = 5

        for item in sorted_tasks[:max_concurrent]:
            task = item["task"]
            agent = self._route_to_agent(task)
            schedule.append(
                {
                    "task": task,
                    "agent": agent,
                    "score": item["score"],
                    "estimated_duration": self._estimate_duration(task, agent),
                }
            )

        return schedule

    def _route_to_agent(self, task):
        """路由到对应 Agent"""
        task_type = task.get("type", "code")
        routing = {
            "code": "coder-dispatcher",
            "analysis": "analyst-dispatcher",
            "monitor": "monitor-dispatcher",
            "test": "coder-dispatcher",
            "refactor": "coder-dispatcher",
        }
        return routing.get(task_type, "coder-dispatcher")

    def _estimate_duration(self, task, agent):
        """估算任务耗时"""
        durations = {"code": 60, "analysis": 30, "monitor": 20, "test": 45, "refactor": 90}
        return durations.get(task.get("type", "code"), 60)

    def _display_schedule(self, schedule):
        """显示调度计划"""
        print(f"\n📊 调度计划 ({len(schedule)} 个任务):\n")

        for i, item in enumerate(schedule, 1):
            task = item["task"]
            desc = task.get("description") or task.get("message") or "无描述"
            print(f"{i}. [{task.get('priority', 'normal').upper()}] {task.get('id')}")
            print(f"   描述: {desc[:60]}...")
            print(f"   Agent: {item['agent']}")
            print(f"   评分: {item['score']:.1f}")
            print(f"   预计耗时: {item['estimated_duration']}秒\n")

    def _execute_schedule(self, schedule):
        """执行调度（创建 spawn 请求 + 通过 TaskQueueManager 更新状态）"""
        print("🚀 执行调度...\n")

        scheduled_task_ids = set()

        for item in schedule:
            task = item["task"]
            agent = item["agent"]
            task_id = task.get("id")

            spawn_request = {
                "agent_id": agent,
                "agent": agent,
                "task": task.get("description") or task.get("message", ""),
                "message": task.get("description") or task.get("message", ""),
                "task_id": task_id,
                "priority": task.get("priority", "normal"),
                "status": "scheduled",
                "workflow_id": task.get("workflow_id"),
                "label": agent,
            }

            spawn_result = self.spawn_manager.create_spawn_request(spawn_request, source="task_scheduler")
            if not spawn_result.get("success"):
                self._log_duplicate(
                    target="spawn_requests",
                    payload=spawn_request,
                    result=spawn_result,
                    source="task_scheduler",
                    created_by="task_scheduler.py",
                )
                print(f"⚠️ spawn 已拦截: {task_id} ({spawn_result.get('reason')})")
                continue

            updated_task = dict(task)
            updated_task["status"] = "scheduled"
            updated_task["scheduled_at"] = datetime.now().isoformat()
            updated_task["agent"] = agent
            updated_task["spawn_dedup_key"] = spawn_result.get("dedup_key")
            scheduled_task_ids.add(task_id)

            print(f"✓ 已调度: {task_id} → {agent}")

        if scheduled_task_ids:
            self._rewrite_queue_with_updates(scheduled_task_ids, schedule)

    def _rewrite_queue_with_updates(self, scheduled_task_ids, schedule):
        """重写任务队列，仅更新已成功创建 spawn 的任务状态"""
        if not self.queue_file.exists():
            return

        update_by_id = {}
        for item in schedule:
            task = item["task"]
            task_id = task.get("id")
            if task_id in scheduled_task_ids:
                updated_task = dict(task)
                updated_task["status"] = "scheduled"
                updated_task["scheduled_at"] = datetime.now().isoformat()
                updated_task["agent"] = item["agent"]
                update_by_id[task_id] = updated_task

        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = record.get("id")
                if record_id in update_by_id:
                    merged = dict(record)
                    merged.update(update_by_id[record_id])
                    tasks.append(merged)
                else:
                    tasks.append(record)

        with open(self.queue_file, "w", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")

    def _log_duplicate(self, target: str, payload: Dict, result: Dict, source: str, created_by: str):
        """统一 duplicate 日志"""
        self.duplicate_log.parent.mkdir(parents=True, exist_ok=True)

        reason_text = (result.get("reason") or "").lower()
        duplicate_reason = "same_task_id"
        if "window" in reason_text:
            duplicate_reason = "same_payload_window"
        elif "dedup_key" in reason_text or result.get("action") == "skipped_duplicate":
            duplicate_reason = "same_dedup_key"

        entry = {
            "target": target,
            "task_id": payload.get("task_id") or payload.get("id"),
            "workflow_id": payload.get("workflow_id"),
            "dedup_key": result.get("dedup_key"),
            "source": source,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "duplicate_reason": duplicate_reason,
            "existing_record_hint": result.get("reason"),
        }

        with open(self.duplicate_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.schedule()
