"""Task Scheduler Agent - 智能任务调度"""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class TaskScheduler:
    def __init__(self):
        self.queue_file = Path("task_queue.jsonl")
        self.agents_file = Path("agents.json")
        self.dependency_file = Path("data/dependencies/task_dependencies.json")
        
    def schedule(self):
        """智能调度任务"""
        print("=" * 80)
        print("Task Scheduler - 智能任务调度")
        print("=" * 80)
        
        # 1. 加载任务和资源
        tasks = self._load_tasks()
        agents = self._load_agents()
        dependencies = self._load_dependencies()
        
        print(f"\n📋 待调度任务: {len(tasks)} 个")
        print(f"🤖 可用 Agent: {len(agents)} 个")
        
        # 2. 过滤可执行任务
        ready_tasks = self._filter_ready_tasks(tasks, dependencies)
        print(f"✓ 可立即执行: {len(ready_tasks)} 个")
        
        if not ready_tasks:
            print("\n✓ 没有可执行的任务")
            return
        
        # 3. 计算优先级分数
        scored_tasks = self._score_tasks(ready_tasks, agents)
        
        # 4. 排序（按分数降序）
        sorted_tasks = sorted(scored_tasks, key=lambda x: x["score"], reverse=True)
        
        # 5. 生成调度计划
        schedule = self._generate_schedule(sorted_tasks, agents)
        
        # 6. 显示调度计划
        self._display_schedule(schedule)
        
        # 7. 执行调度（创建 spawn 请求）
        self._execute_schedule(schedule)
        
        print(f"\n{'=' * 80}")
    
    def _load_tasks(self):
        """加载任务队列"""
        if not self.queue_file.exists():
            return []
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    if task.get("status") == "pending":
                        tasks.append(task)
        return tasks
    
    def _load_agents(self):
        """加载可用 Agent"""
        if not self.agents_file.exists():
            return []
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        # 只返回启用的 Agent
        return [a for a in agents if a.get("enabled", True)]
    
    def _load_dependencies(self):
        """加载依赖关系"""
        if not self.dependency_file.exists():
            return {}
        
        with open(self.dependency_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _filter_ready_tasks(self, tasks, dependencies):
        """过滤可执行任务（无依赖或依赖已完成）"""
        # 简化实现：假设所有任务都可执行
        return tasks
    
    def _score_tasks(self, tasks, agents):
        """计算任务优先级分数"""
        scored = []
        
        for task in tasks:
            score = 0
            
            # 1. 优先级权重（40%）
            priority_scores = {"urgent": 100, "high": 75, "normal": 50, "low": 25}
            score += priority_scores.get(task.get("priority", "normal"), 50) * 0.4
            
            # 2. 等待时间权重（30%）
            created_at = datetime.fromisoformat(task.get("created_at", datetime.now().isoformat()))
            wait_hours = (datetime.now() - created_at).total_seconds() / 3600
            score += min(wait_hours * 5, 100) * 0.3  # 最多 20 小时 = 100 分
            
            # 3. Agent 可用性权重（20%）
            agent_available = self._check_agent_availability(task, agents)
            score += (100 if agent_available else 0) * 0.2
            
            # 4. 任务类型权重（10%）
            type_scores = {"urgent": 100, "code": 80, "analysis": 60, "monitor": 40, "test": 50}
            score += type_scores.get(task.get("type", "code"), 50) * 0.1
            
            scored.append({
                "task": task,
                "score": score
            })
        
        return scored
    
    def _check_agent_availability(self, task, agents):
        """检查 Agent 是否可用"""
        task_type = task.get("type", "code")
        
        # 路由规则
        routing = {
            "code": ["coder-dispatcher", "Coder"],
            "analysis": ["analyst-dispatcher", "Analyst"],
            "monitor": ["monitor-dispatcher", "Monitor"],
            "test": ["coder-dispatcher", "Coder"]
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
        max_concurrent = 5  # 最多同时执行 5 个任务
        
        for item in sorted_tasks[:max_concurrent]:
            task = item["task"]
            agent = self._route_to_agent(task)
            
            schedule.append({
                "task": task,
                "agent": agent,
                "score": item["score"],
                "estimated_duration": self._estimate_duration(task, agent)
            })
        
        return schedule
    
    def _route_to_agent(self, task):
        """路由到对应 Agent"""
        task_type = task.get("type", "code")
        
        routing = {
            "code": "coder-dispatcher",
            "analysis": "analyst-dispatcher",
            "monitor": "monitor-dispatcher",
            "test": "coder-dispatcher",
            "refactor": "coder-dispatcher"
        }
        
        return routing.get(task_type, "coder-dispatcher")
    
    def _estimate_duration(self, task, agent):
        """估算任务耗时"""
        # 简化实现：根据任务类型估算
        durations = {
            "code": 60,
            "analysis": 30,
            "monitor": 20,
            "test": 45,
            "refactor": 90
        }
        
        return durations.get(task.get("type", "code"), 60)
    
    def _display_schedule(self, schedule):
        """显示调度计划"""
        print(f"\n📊 调度计划 ({len(schedule)} 个任务):\n")
        
        for i, item in enumerate(schedule, 1):
            task = item["task"]
            print(f"{i}. [{task.get('priority', 'normal').upper()}] {task.get('id')}")
            print(f"   描述: {task.get('description', '无描述')[:60]}...")
            print(f"   Agent: {item['agent']}")
            print(f"   评分: {item['score']:.1f}")
            print(f"   预计耗时: {item['estimated_duration']}秒\n")
    
    def _execute_schedule(self, schedule):
        """执行调度（创建 spawn 请求）"""
        print("🚀 执行调度...\n")
        
        for item in schedule:
            task = item["task"]
            agent = item["agent"]
            
            # 创建 spawn 请求
            spawn_request = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "task": task.get("description", ""),
                "task_id": task.get("id"),
                "priority": task.get("priority", "normal"),
                "status": "scheduled"
            }
            
            # 写入 spawn 请求
            with open("spawn_requests.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")
            
            # 更新任务状态
            task["status"] = "scheduled"
            task["scheduled_at"] = datetime.now().isoformat()
            task["agent"] = agent
            
            print(f"✓ 已调度: {task.get('id')} → {agent}")
        
        # 重写队列
        self._update_queue()
    
    def _update_queue(self):
        """更新任务队列"""
        if not self.queue_file.exists():
            return
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        
        # 重写
        with open(self.queue_file, "w", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.schedule()
