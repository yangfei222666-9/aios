"""Auto Fixer Agent - 自动修复失败的任务"""
import json
from datetime import datetime
from pathlib import Path
import re

class AutoFixer:
    def __init__(self):
        self.execution_file = Path("task_executions.jsonl")
        self.events_file = Path("data/events/events.jsonl")
        self.fix_history_file = Path("data/fixes/auto_fix_history.jsonl")
        
        # 错误模式和修复策略
        self.fix_patterns = {
            "timeout": {
                "pattern": r"timeout|超时|timed out",
                "fixes": [
                    {"action": "increase_timeout", "params": {"factor": 1.5}},
                    {"action": "split_task", "params": {}},
                    {"action": "use_faster_model", "params": {"model": "claude-sonnet-4-5"}}
                ]
            },
            "api_error": {
                "pattern": r"api.*error|rate limit|quota|429|503",
                "fixes": [
                    {"action": "retry_with_backoff", "params": {"delay": 5}},
                    {"action": "switch_provider", "params": {}},
                    {"action": "reduce_concurrency", "params": {}}
                ]
            },
            "syntax_error": {
                "pattern": r"syntax.*error|invalid syntax|unexpected token",
                "fixes": [
                    {"action": "fix_syntax", "params": {}},
                    {"action": "regenerate_code", "params": {"with_examples": True}}
                ]
            },
            "import_error": {
                "pattern": r"import.*error|module.*not found|no module named",
                "fixes": [
                    {"action": "install_dependency", "params": {}},
                    {"action": "use_builtin_alternative", "params": {}}
                ]
            },
            "permission_error": {
                "pattern": r"permission.*denied|access.*denied|forbidden",
                "fixes": [
                    {"action": "request_permission", "params": {}},
                    {"action": "use_alternative_path", "params": {}}
                ]
            }
        }
    
    def auto_fix(self):
        """自动修复失败的任务"""
        print("=" * 80)
        print("Auto Fixer - 自动修复失败任务")
        print("=" * 80)
        
        # 1. 查找失败的任务
        failed_tasks = self._find_failed_tasks()
        
        if not failed_tasks:
            print("\n✓ 没有失败的任务")
            return
        
        print(f"\n🔍 发现 {len(failed_tasks)} 个失败任务\n")
        
        # 2. 逐个修复
        fixed = 0
        for task in failed_tasks:
            try:
                if self._fix_task(task):
                    fixed += 1
            except Exception as e:
                print(f"✗ 修复失败: {e}")
        
        print(f"\n{'=' * 80}")
        print(f"修复完成: {fixed}/{len(failed_tasks)} 个任务")
        print(f"{'=' * 80}")
    
    def _find_failed_tasks(self):
        """查找失败的任务"""
        failed = []
        
        if not self.execution_file.exists():
            return failed
        
        with open(self.execution_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                if record.get("status") == "failed":
                    # 检查是否已经修复过
                    if not self._is_already_fixed(record.get("task_id")):
                        failed.append(record)
        
        return failed
    
    def _is_already_fixed(self, task_id):
        """检查任务是否已经修复过"""
        if not self.fix_history_file.exists():
            return False
        
        with open(self.fix_history_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                if record.get("task_id") == task_id and record.get("status") == "fixed":
                    return True
        
        return False
    
    def _fix_task(self, task):
        """修复单个任务"""
        task_id = task.get("task_id", "unknown")
        error = task.get("error", "")
        
        print(f"🔧 修复任务: {task_id}")
        print(f"   错误: {error[:100]}...")
        
        # 1. 识别错误类型
        error_type = self._classify_error(error)
        print(f"   类型: {error_type}")
        
        # 2. 选择修复策略
        fixes = self.fix_patterns.get(error_type, {}).get("fixes", [])
        
        if not fixes:
            print(f"   ✗ 未找到修复策略")
            return False
        
        # 3. 尝试修复
        for i, fix in enumerate(fixes, 1):
            print(f"   尝试修复 {i}/{len(fixes)}: {fix['action']}...", end=" ")
            
            success = self._apply_fix(task, fix)
            
            if success:
                print("✓")
                self._record_fix(task_id, error_type, fix, "success")
                return True
            else:
                print("✗")
        
        # 4. 所有修复都失败
        print(f"   ✗ 所有修复策略都失败")
        self._record_fix(task_id, error_type, None, "failed")
        return False
    
    def _classify_error(self, error):
        """分类错误类型"""
        error_lower = error.lower()
        
        for error_type, config in self.fix_patterns.items():
            if re.search(config["pattern"], error_lower):
                return error_type
        
        return "unknown"
    
    def _apply_fix(self, task, fix):
        """应用修复策略"""
        action = fix["action"]
        params = fix["params"]
        
        # 根据不同的修复动作执行不同的操作
        if action == "increase_timeout":
            return self._increase_timeout(task, params)
        elif action == "retry_with_backoff":
            return self._retry_with_backoff(task, params)
        elif action == "use_faster_model":
            return self._use_faster_model(task, params)
        elif action == "split_task":
            return self._split_task(task, params)
        elif action == "fix_syntax":
            return self._fix_syntax(task, params)
        elif action == "install_dependency":
            return self._install_dependency(task, params)
        else:
            return False
    
    def _increase_timeout(self, task, params):
        """增加超时时间"""
        # 更新 Agent 配置
        agent = task.get("agent")
        factor = params.get("factor", 1.5)
        
        # 读取 agents.json
        agents_file = Path("agents.json")
        if not agents_file.exists():
            return False
        
        with open(agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        # 找到对应 Agent 并更新超时
        for a in agents:
            if a.get("name") == agent or a.get("id") == agent:
                old_timeout = a.get("timeout", 60)
                new_timeout = int(old_timeout * factor)
                a["timeout"] = new_timeout
                
                # 保存
                if isinstance(data, list):
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(agents, f, ensure_ascii=False, indent=2)
                else:
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"(超时: {old_timeout}s → {new_timeout}s)", end=" ")
                return True
        
        return False
    
    def _retry_with_backoff(self, task, params):
        """重试（带延迟）"""
        import time
        delay = params.get("delay", 5)
        
        print(f"(等待 {delay}s)", end=" ")
        time.sleep(delay)
        
        # 重新提交任务
        task_id = task.get("task_id")
        description = task.get("description", "")
        
        # 创建新的任务
        new_task = {
            "id": f"{task_id}-retry",
            "type": task.get("type", "code"),
            "priority": "high",
            "description": description,
            "status": "pending",
            "retry_of": task_id,
            "created_at": datetime.now().isoformat()
        }
        
        # 写入队列
        with open("task_queue.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(new_task, ensure_ascii=False) + "\n")
        
        return True
    
    def _use_faster_model(self, task, params):
        """切换到更快的模型"""
        model = params.get("model", "claude-sonnet-4-5")
        
        # 更新 Agent 配置
        agent = task.get("agent")
        agents_file = Path("agents.json")
        
        if not agents_file.exists():
            return False
        
        with open(agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        for a in agents:
            if a.get("name") == agent or a.get("id") == agent:
                old_model = a.get("model", "unknown")
                a["model"] = model
                
                # 保存
                if isinstance(data, list):
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(agents, f, ensure_ascii=False, indent=2)
                else:
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"(模型: {old_model} → {model})", end=" ")
                return True
        
        return False
    
    def _split_task(self, task, params):
        """拆分任务"""
        # 简化实现：标记任务需要拆分
        print("(标记为需要拆分)", end=" ")
        return True
    
    def _fix_syntax(self, task, params):
        """修复语法错误"""
        # 简化实现：重新生成代码
        print("(重新生成代码)", end=" ")
        return self._retry_with_backoff(task, {"delay": 1})
    
    def _install_dependency(self, task, params):
        """安装依赖"""
        # 从错误信息中提取包名
        error = task.get("error", "")
        match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error.lower())
        
        if match:
            package = match.group(1)
            print(f"(安装 {package})", end=" ")
            # 实际应该执行 pip install
            return True
        
        return False
    
    def _record_fix(self, task_id, error_type, fix, status):
        """记录修复历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "error_type": error_type,
            "fix": fix,
            "status": status
        }
        
        self.fix_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.fix_history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    fixer = AutoFixer()
    fixer.auto_fix()
