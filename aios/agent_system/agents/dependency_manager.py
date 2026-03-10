"""Dependency Manager - 浠诲姟渚濊禆鍏崇郴绠＄悊鍜岀紪鎺?""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

class DependencyManager:
    def __init__(self):
        self.queue_file = Path("task_queue.jsonl")
        self.dependency_file = Path("data/dependencies/task_dependencies.json")
        self.execution_file = Path(TASK_EXECUTIONS)
        
    def manage_dependencies(self):
        """绠＄悊浠诲姟渚濊禆鍏崇郴"""
        print("=" * 80)
        print("Dependency Manager - 浠诲姟渚濊禆绠＄悊")
        print("=" * 80)
        
        # 1. 鍔犺浇浠诲姟鍜屼緷璧?        tasks = self._load_tasks()
        dependencies = self._load_dependencies()
        
        print(f"\n馃搵 浠诲姟鎬绘暟: {len(tasks)}")
        print(f"馃敆 渚濊禆鍏崇郴: {len(dependencies)} 鏉?)
        
        # 2. 鏋勫缓渚濊禆鍥?        dep_graph = self._build_dependency_graph(tasks, dependencies)
        
        # 3. 鎷撴墤鎺掑簭锛堟壘鍑哄彲鎵ц椤哄簭锛?        execution_order = self._topological_sort(dep_graph)
        
        if not execution_order:
            print("\n鉁?妫€娴嬪埌寰幆渚濊禆锛屾棤娉曟墽琛?)
            return
        
        print(f"\n鉁?鎵ц椤哄簭宸茶绠?({len(execution_order)} 涓换鍔?")
        
        # 4. 鎵惧嚭鍙珛鍗虫墽琛岀殑浠诲姟
        ready_tasks = self._find_ready_tasks(tasks, dependencies)
        
        print(f"\n馃殌 鍙珛鍗虫墽琛岀殑浠诲姟 ({len(ready_tasks)} 涓?:")
        for task in ready_tasks[:5]:
            print(f"  鈥?{task['id']}: {task.get('description', '鏃犳弿杩?)}")
        
        # 5. 鎵惧嚭琚樆濉炵殑浠诲姟
        blocked_tasks = self._find_blocked_tasks(tasks, dependencies)
        
        if blocked_tasks:
            print(f"\n鈴革笍  琚樆濉炵殑浠诲姟 ({len(blocked_tasks)} 涓?:")
            for task, blocking in list(blocked_tasks.items())[:5]:
                print(f"  鈥?{task}: 绛夊緟 {', '.join(blocking)}")
        
        # 6. 鐢熸垚鎵ц璁″垝
        plan = self._generate_execution_plan(execution_order, dependencies)
        
        print(f"\n馃搳 鎵ц璁″垝:")
        for stage, stage_tasks in enumerate(plan, 1):
            print(f"  闃舵 {stage}: {len(stage_tasks)} 涓换鍔★紙鍙苟琛岋級")
        
        # 7. 淇濆瓨渚濊禆鍥惧拰鎵ц璁″垝
        self._save_dependency_graph(dep_graph, execution_order, plan)
        
        print(f"\n{'=' * 80}")
    
    def add_dependency(self, task_id, depends_on):
        """娣诲姞浠诲姟渚濊禆"""
        dependencies = self._load_dependencies()
        
        if task_id not in dependencies:
            dependencies[task_id] = []
        
        if depends_on not in dependencies[task_id]:
            dependencies[task_id].append(depends_on)
        
        self._save_dependencies(dependencies)
        print(f"鉁?宸叉坊鍔犱緷璧? {task_id} 鈫?{depends_on}")
    
    def _load_tasks(self):
        """鍔犺浇浠诲姟闃熷垪"""
        if not self.queue_file.exists():
            return []
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        return tasks
    
    def _load_dependencies(self):
        """鍔犺浇渚濊禆鍏崇郴"""
        if not self.dependency_file.exists():
            return {}
        
        with open(self.dependency_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_dependencies(self, dependencies):
        """淇濆瓨渚濊禆鍏崇郴"""
        self.dependency_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.dependency_file, "w", encoding="utf-8") as f:
            json.dump(dependencies, f, ensure_ascii=False, indent=2)
    
    def _build_dependency_graph(self, tasks, dependencies):
        """鏋勫缓渚濊禆鍥?""
        graph = defaultdict(list)
        
        for task in tasks:
            task_id = task.get("id")
            deps = dependencies.get(task_id, [])
            graph[task_id] = deps
        
        return dict(graph)
    
    def _topological_sort(self, graph):
        """鎷撴墤鎺掑簭锛堟娴嬪惊鐜緷璧栵級"""
        # 璁＄畻鍏ュ害
        in_degree = defaultdict(int)
        for node in graph:
            if node not in in_degree:
                in_degree[node] = 0
            for dep in graph[node]:
                in_degree[dep] += 1
        
        # 鎵惧嚭鍏ュ害涓?0 鐨勮妭鐐?        queue = deque([node for node in graph if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for dep in graph.get(node, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        # 濡傛灉缁撴灉闀垮害涓嶇瓑浜庤妭鐐规暟锛岃鏄庢湁寰幆渚濊禆
        if len(result) != len(graph):
            return None
        
        return result
    
    def _find_ready_tasks(self, tasks, dependencies):
        """鎵惧嚭鍙珛鍗虫墽琛岀殑浠诲姟锛堟棤渚濊禆鎴栦緷璧栧凡瀹屾垚锛?""
        completed = self._get_completed_tasks()
        ready = []
        
        for task in tasks:
            if task.get("status") != "pending":
                continue
            
            task_id = task.get("id")
            deps = dependencies.get(task_id, [])
            
            # 鏃犱緷璧栨垨鎵€鏈変緷璧栧凡瀹屾垚
            if not deps or all(dep in completed for dep in deps):
                ready.append(task)
        
        return ready
    
    def _find_blocked_tasks(self, tasks, dependencies):
        """鎵惧嚭琚樆濉炵殑浠诲姟"""
        completed = self._get_completed_tasks()
        blocked = {}
        
        for task in tasks:
            if task.get("status") != "pending":
                continue
            
            task_id = task.get("id")
            deps = dependencies.get(task_id, [])
            
            # 鏈夋湭瀹屾垚鐨勪緷璧?            blocking = [dep for dep in deps if dep not in completed]
            if blocking:
                blocked[task_id] = blocking
        
        return blocked
    
    def _get_completed_tasks(self):
        """鑾峰彇宸插畬鎴愮殑浠诲姟"""
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
        """鐢熸垚鍒嗛樁娈垫墽琛岃鍒掞紙鍚屼竴闃舵鐨勪换鍔″彲骞惰锛?""
        completed = set()
        plan = []
        
        while execution_order:
            # 鎵惧嚭褰撳墠鍙墽琛岀殑浠诲姟
            stage = []
            remaining = []
            
            for task_id in execution_order:
                deps = dependencies.get(task_id, [])
                if all(dep in completed for dep in deps):
                    stage.append(task_id)
                else:
                    remaining.append(task_id)
            
            if not stage:
                break  # 鏃犳硶缁х画
            
            plan.append(stage)
            completed.update(stage)
            execution_order = remaining
        
        return plan
    
    def _save_dependency_graph(self, graph, execution_order, plan):
        """淇濆瓨渚濊禆鍥惧拰鎵ц璁″垝"""
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
        
        print(f"\n鉁?渚濊禆鍒嗘瀽宸蹭繚瀛? {output_file}")

if __name__ == "__main__":
    import sys
    
    manager = DependencyManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        # 娣诲姞渚濊禆: python dependency_manager.py add task1 task2
        if len(sys.argv) == 4:
            manager.add_dependency(sys.argv[2], sys.argv[3])
        else:
            print("鐢ㄦ硶: python dependency_manager.py add <task_id> <depends_on>")
    else:
        # 鍒嗘瀽渚濊禆
        manager.manage_dependencies()


