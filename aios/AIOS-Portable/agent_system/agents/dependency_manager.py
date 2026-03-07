"""Dependency Manager - 任务依赖关系管理和编排"""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

class DependencyManager:
    def __init__(self):
        self.queue_file = Path("task_queue.jsonl")
        self.dependency_file = Path("data/dependencies/task_dependencies.json")
        self.execution_file = Path("task_executions.jsonl")
        
    def manage_dependencies(self):
        """管理任务依赖关系"""
        print("=" * 80)
        print("Dependency Manager - 任务依赖管理")
        print("=" * 80)
        
        # 1. 加载任务和依赖
        tasks = self._load_tasks()
        dependencies = self._load_dependencies()
        
        print(f"\n📋 任务总数: {len(tasks)}")
        print(f"🔗 依赖关系: {len(dependencies)} 条")
        
        # 2. 构建依赖图
        dep_graph = self._build_dependency_graph(tasks, dependencies)
        
        # 3. 拓扑排序（找出可执行顺序）
        execution_order = self._topological_sort(dep_graph)
        
        if not execution_order:
            print("\n✗ 检测到循环依赖，无法执行")
            return
        
        print(f"\n✓ 执行顺序已计算 ({len(execution_order)} 个任务)")
        
        # 4. 找出可立即执行的任务
        ready_tasks = self._find_ready_tasks(tasks, dependencies)
        
        print(f"\n🚀 可立即执行的任务 ({len(ready_tasks)} 个):")
        for task in ready_tasks[:5]:
            print(f"  • {task['id']}: {task.get('description', '无描述')}")
        
        # 5. 找出被阻塞的任务
        blocked_tasks = self._find_blocked_tasks(tasks, dependencies)
        
        if blocked_tasks:
            print(f"\n⏸️  被阻塞的任务 ({len(blocked_tasks)} 个):")
            for task, blocking in list(blocked_tasks.items())[:5]:
                print(f"  • {task}: 等待 {', '.join(blocking)}")
        
        # 6. 生成执行计划
        plan = self._generate_execution_plan(execution_order, dependencies)
        
        print(f"\n📊 执行计划:")
        for stage, stage_tasks in enumerate(plan, 1):
            print(f"  阶段 {stage}: {len(stage_tasks)} 个任务（可并行）")
        
        # 7. 保存依赖图和执行计划
        self._save_dependency_graph(dep_graph, execution_order, plan)
        
        print(f"\n{'=' * 80}")
    
    def add_dependency(self, task_id, depends_on):
        """添加任务依赖"""
        dependencies = self._load_dependencies()
        
        if task_id not in dependencies:
            dependencies[task_id] = []
        
        if depends_on not in dependencies[task_id]:
            dependencies[task_id].append(depends_on)
        
        self._save_dependencies(dependencies)
        print(f"✓ 已添加依赖: {task_id} → {depends_on}")
    
    def _load_tasks(self):
        """加载任务队列"""
        if not self.queue_file.exists():
            return []
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        return tasks
    
    def _load_dependencies(self):
        """加载依赖关系"""
        if not self.dependency_file.exists():
            return {}
        
        with open(self.dependency_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_dependencies(self, dependencies):
        """保存依赖关系"""
        self.dependency_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.dependency_file, "w", encoding="utf-8") as f:
            json.dump(dependencies, f, ensure_ascii=False, indent=2)
    
    def _build_dependency_graph(self, tasks, dependencies):
        """构建依赖图"""
        graph = defaultdict(list)
        
        for task in tasks:
            task_id = task.get("id")
            deps = dependencies.get(task_id, [])
            graph[task_id] = deps
        
        return dict(graph)
    
    def _topological_sort(self, graph):
        """拓扑排序（检测循环依赖）"""
        # 计算入度
        in_degree = defaultdict(int)
        for node in graph:
            if node not in in_degree:
                in_degree[node] = 0
            for dep in graph[node]:
                in_degree[dep] += 1
        
        # 找出入度为 0 的节点
        queue = deque([node for node in graph if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for dep in graph.get(node, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        # 如果结果长度不等于节点数，说明有循环依赖
        if len(result) != len(graph):
            return None
        
        return result
    
    def _find_ready_tasks(self, tasks, dependencies):
        """找出可立即执行的任务（无依赖或依赖已完成）"""
        completed = self._get_completed_tasks()
        ready = []
        
        for task in tasks:
            if task.get("status") != "pending":
                continue
            
            task_id = task.get("id")
            deps = dependencies.get(task_id, [])
            
            # 无依赖或所有依赖已完成
            if not deps or all(dep in completed for dep in deps):
                ready.append(task)
        
        return ready
    
    def _find_blocked_tasks(self, tasks, dependencies):
        """找出被阻塞的任务"""
        completed = self._get_completed_tasks()
        blocked = {}
        
        for task in tasks:
            if task.get("status") != "pending":
                continue
            
            task_id = task.get("id")
            deps = dependencies.get(task_id, [])
            
            # 有未完成的依赖
            blocking = [dep for dep in deps if dep not in completed]
            if blocking:
                blocked[task_id] = blocking
        
        return blocked
    
    def _get_completed_tasks(self):
        """获取已完成的任务"""
        if not self.execution_file.exists():
            return set()
        
        completed = set()
        with open(self.execution_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record.get("status") == "completed":
                        completed.add(record.get("task_id"))
        
        return completed
    
    def _generate_execution_plan(self, execution_order, dependencies):
        """生成分阶段执行计划（同一阶段的任务可并行）"""
        completed = set()
        plan = []
        
        while execution_order:
            # 找出当前可执行的任务
            stage = []
            remaining = []
            
            for task_id in execution_order:
                deps = dependencies.get(task_id, [])
                if all(dep in completed for dep in deps):
                    stage.append(task_id)
                else:
                    remaining.append(task_id)
            
            if not stage:
                break  # 无法继续
            
            plan.append(stage)
            completed.update(stage)
            execution_order = remaining
        
        return plan
    
    def _save_dependency_graph(self, graph, execution_order, plan):
        """保存依赖图和执行计划"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "dependency_graph": graph,
            "execution_order": execution_order,
            "execution_plan": plan
        }
        
        output_file = Path("data/dependencies/dependency_analysis.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 依赖分析已保存: {output_file}")

if __name__ == "__main__":
    import sys
    
    manager = DependencyManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        # 添加依赖: python dependency_manager.py add task1 task2
        if len(sys.argv) == 4:
            manager.add_dependency(sys.argv[2], sys.argv[3])
        else:
            print("用法: python dependency_manager.py add <task_id> <depends_on>")
    else:
        # 分析依赖
        manager.manage_dependencies()
