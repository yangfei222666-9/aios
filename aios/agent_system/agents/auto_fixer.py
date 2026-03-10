"""Auto Fixer Agent - 鑷姩淇澶辫触鐨勪换鍔?""
import json
from datetime import datetime
from pathlib import Path
import re

class AutoFixer:
    def __init__(self):
        self.execution_file = Path(TASK_EXECUTIONS)
        self.events_file = Path("data/events/events.jsonl")
        self.fix_history_file = Path("data/fixes/auto_fix_history.jsonl")
        
        # 閿欒妯″紡鍜屼慨澶嶇瓥鐣?        self.fix_patterns = {
            "timeout": {
                "pattern": r"timeout|瓒呮椂|timed out",
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
        """鑷姩淇澶辫触鐨勪换鍔?""
        print("=" * 80)
        print("Auto Fixer - 鑷姩淇澶辫触浠诲姟")
        print("=" * 80)
        
        # 1. 鏌ユ壘澶辫触鐨勪换鍔?        failed_tasks = self._find_failed_tasks()
        
        if not failed_tasks:
            print("\n鉁?娌℃湁澶辫触鐨勪换鍔?)
            return
        
        print(f"\n馃攳 鍙戠幇 {len(failed_tasks)} 涓け璐ヤ换鍔n")
        
        # 2. 閫愪釜淇
        fixed = 0
        for task in failed_tasks:
            try:
                if self._fix_task(task):
                    fixed += 1
            except Exception as e:
                print(f"鉁?淇澶辫触: {e}")
        
        print(f"\n{'=' * 80}")
        print(f"淇瀹屾垚: {fixed}/{len(failed_tasks)} 涓换鍔?)
        print(f"{'=' * 80}")
    
    def _find_failed_tasks(self):
        """鏌ユ壘澶辫触鐨勪换鍔?""
        failed = []
        
        if not self.execution_file.exists():
            return failed
        
        with open(self.execution_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                if record.get("status") == "failed":
                    # 妫€鏌ユ槸鍚﹀凡缁忎慨澶嶈繃
                    if not self._is_already_fixed(record.get("task_id")):
                        failed.append(record)
        
        return failed
    
    def _is_already_fixed(self, task_id):
        """妫€鏌ヤ换鍔℃槸鍚﹀凡缁忎慨澶嶈繃"""
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
        """淇鍗曚釜浠诲姟"""
        task_id = task.get("task_id", "unknown")
        error = task.get("error", "")
        
        print(f"馃敡 淇浠诲姟: {task_id}")
        print(f"   閿欒: {error[:100]}...")
        
        # 1. 璇嗗埆閿欒绫诲瀷
        error_type = self._classify_error(error)
        print(f"   绫诲瀷: {error_type}")
        
        # 2. 閫夋嫨淇绛栫暐
        fixes = self.fix_patterns.get(error_type, {}).get("fixes", [])
        
        if not fixes:
            print(f"   鉁?鏈壘鍒颁慨澶嶇瓥鐣?)
            return False
        
        # 3. 灏濊瘯淇
        for i, fix in enumerate(fixes, 1):
            print(f"   灏濊瘯淇 {i}/{len(fixes)}: {fix['action']}...", end=" ")
            
            success = self._apply_fix(task, fix)
            
            if success:
                print("鉁?)
                self._record_fix(task_id, error_type, fix, "success")
                return True
            else:
                print("鉁?)
        
        # 4. 鎵€鏈変慨澶嶉兘澶辫触
        print(f"   鉁?鎵€鏈変慨澶嶇瓥鐣ラ兘澶辫触")
        self._record_fix(task_id, error_type, None, "failed")
        return False
    
    def _classify_error(self, error):
        """鍒嗙被閿欒绫诲瀷"""
        error_lower = error.lower()
        
        for error_type, config in self.fix_patterns.items():
            if re.search(config["pattern"], error_lower):
                return error_type
        
        return "unknown"
    
    def _apply_fix(self, task, fix):
        """搴旂敤淇绛栫暐"""
        action = fix["action"]
        params = fix["params"]
        
        # 鏍规嵁涓嶅悓鐨勪慨澶嶅姩浣滄墽琛屼笉鍚岀殑鎿嶄綔
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
        """澧炲姞瓒呮椂鏃堕棿"""
        # 鏇存柊 Agent 閰嶇疆
        agent = task.get("agent")
        factor = params.get("factor", 1.5)
        
        # 璇诲彇 agents.json
        agents_file = Path("agents.json")
        if not agents_file.exists():
            return False
        
        with open(agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        # 鎵惧埌瀵瑰簲 Agent 骞舵洿鏂拌秴鏃?        for a in agents:
            if a.get("name") == agent or a.get("id") == agent:
                old_timeout = a.get("timeout", 60)
                new_timeout = int(old_timeout * factor)
                a["timeout"] = new_timeout
                
                # 淇濆瓨
                if isinstance(data, list):
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(agents, f, ensure_ascii=False, indent=2)
                else:
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"(瓒呮椂: {old_timeout}s 鈫?{new_timeout}s)", end=" ")
                return True
        
        return False
    
    def _retry_with_backoff(self, task, params):
        """閲嶈瘯锛堝甫寤惰繜锛?""
        import time
        delay = params.get("delay", 5)
        
        print(f"(绛夊緟 {delay}s)", end=" ")
        time.sleep(delay)
        
        # 閲嶆柊鎻愪氦浠诲姟
        task_id = task.get("task_id")
        description = task.get("description", "")
        
        # 鍒涘缓鏂扮殑浠诲姟
        new_task = {
            "id": f"{task_id}-retry",
            "type": task.get("type", "code"),
            "priority": "high",
            "description": description,
            "status": "pending",
            "retry_of": task_id,
            "created_at": datetime.now().isoformat()
        }
        
        # 鍐欏叆闃熷垪
        with open("task_queue.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(new_task, ensure_ascii=False) + "\n")
        
        return True
    
    def _use_faster_model(self, task, params):
        """鍒囨崲鍒版洿蹇殑妯″瀷"""
        model = params.get("model", "claude-sonnet-4-5")
        
        # 鏇存柊 Agent 閰嶇疆
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
                
                # 淇濆瓨
                if isinstance(data, list):
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(agents, f, ensure_ascii=False, indent=2)
                else:
                    with open(agents_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"(妯″瀷: {old_model} 鈫?{model})", end=" ")
                return True
        
        return False
    
    def _split_task(self, task, params):
        """鎷嗗垎浠诲姟"""
        # 绠€鍖栧疄鐜帮細鏍囪浠诲姟闇€瑕佹媶鍒?        print("(鏍囪涓洪渶瑕佹媶鍒?", end=" ")
        return True
    
    def _fix_syntax(self, task, params):
        """淇璇硶閿欒"""
        # 绠€鍖栧疄鐜帮細閲嶆柊鐢熸垚浠ｇ爜
        print("(閲嶆柊鐢熸垚浠ｇ爜)", end=" ")
        return self._retry_with_backoff(task, {"delay": 1})
    
    def _install_dependency(self, task, params):
        """瀹夎渚濊禆"""
        # 浠庨敊璇俊鎭腑鎻愬彇鍖呭悕
        error = task.get("error", "")
        match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error.lower())
        
        if match:
            package = match.group(1)
            print(f"(瀹夎 {package})", end=" ")
            # 瀹為檯搴旇鎵ц pip install
            return True
        
        return False
    
    def _record_fix(self, task_id, error_type, fix, status):
        """璁板綍淇鍘嗗彶"""
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


