"""Coder Failure Analyzer - 鍒嗘瀽 Coder Agent 澶辫触鍘熷洜"""
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

class CoderFailureAnalyzer:
    def __init__(self):
        self.agents_file = Path("agents.json")
        self.execution_file = Path(TASK_EXECUTIONS)
        self.events_file = Path("data/events/events.jsonl")
        
    def analyze(self):
        """鍒嗘瀽 Coder Agent 澶辫触鍘熷洜"""
        print("=" * 80)
        print("Coder Failure Analyzer - 澶辫触鍘熷洜鍒嗘瀽")
        print("=" * 80)
        
        # 1. 璇诲彇 Coder Agent 鐘舵€?        coder_stats = self._get_coder_stats()
        if not coder_stats:
            print("\n鉁?鏈壘鍒?Coder Agent")
            return
        
        print(f"\n馃搳 Coder Agent 缁熻:")
        print(f"  鎴愬姛: {coder_stats.get('tasks_completed', 0)}")
        print(f"  澶辫触: {coder_stats.get('tasks_failed', 0)}")
        print(f"  鎬昏: {coder_stats.get('tasks_total', 0)}")
        print(f"  鎴愬姛鐜? {coder_stats.get('success_rate', 0):.1f}%")
        print(f"  骞冲潎鑰楁椂: {coder_stats.get('avg_duration', 0):.1f}绉?)
        
        # 2. 鍒嗘瀽澶辫触浜嬩欢
        failures = self._get_failure_events()
        if not failures:
            print("\n鉁?鏈壘鍒板け璐ヨ褰?)
            return
        
        print(f"\n馃攳 澶辫触浜嬩欢鍒嗘瀽 (鍏?{len(failures)} 鏉?:")
        
        # 3. 澶辫触鍘熷洜鍒嗙被
        error_types = Counter()
        error_messages = []
        
        for failure in failures:
            error = failure.get("error", "")
            error_type = self._classify_error(error)
            error_types[error_type] += 1
            error_messages.append({
                "type": error_type,
                "message": error[:200],
                "timestamp": failure.get("timestamp", "")
            })
        
        print("\n馃搵 澶辫触鍘熷洜鍒嗗竷:")
        for error_type, count in error_types.most_common():
            print(f"  {error_type}: {count} 娆?)
        
        # 4. 璇︾粏閿欒淇℃伅
        print("\n馃摑 璇︾粏閿欒淇℃伅:")
        for i, error in enumerate(error_messages[:3], 1):
            print(f"\n  [{i}] {error['type']}")
            print(f"      鏃堕棿: {error['timestamp']}")
            print(f"      淇℃伅: {error['message']}")
        
        # 5. 鐢熸垚璇婃柇鎶ュ憡
        diagnosis = self._generate_diagnosis(error_types, coder_stats)
        
        print(f"\n{'=' * 80}")
        print("馃敡 璇婃柇鎶ュ憡:")
        print(f"{'=' * 80}")
        for i, item in enumerate(diagnosis, 1):
            print(f"\n{i}. {item['problem']}")
            print(f"   鍘熷洜: {item['cause']}")
            print(f"   寤鸿: {item['solution']}")
        
        # 6. 淇濆瓨鎶ュ憡
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": coder_stats,
            "error_types": dict(error_types),
            "diagnosis": diagnosis
        }
        
        report_file = Path("data/analysis/coder_failure_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n鉁?鎶ュ憡宸蹭繚瀛? {report_file}")
    
    def _get_coder_stats(self):
        """鑾峰彇 Coder Agent 缁熻"""
        if not self.agents_file.exists():
            return None
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 鏀寔涓ょ鏍煎紡
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        for agent in agents:
            if agent.get("name") == "coder-dispatcher":
                return agent.get("stats", {})
        return None
    
    def _get_failure_events(self):
        """鑾峰彇澶辫触浜嬩欢"""
        failures = []
        
        # 浠?events.jsonl 璇诲彇
        if self.events_file.exists():
            with open(self.events_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event.get("type") == "task_failed" and "coder" in event.get("agent", "").lower():
                            failures.append(event)
        
        # 浠?task_executions_v2.jsonl 璇诲彇
        if self.execution_file.exists():
            with open(self.execution_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        exec_record = json.loads(line)
                        if exec_record.get("status") == "failed" and "coder" in exec_record.get("agent", "").lower():
                            failures.append(exec_record)
        
        return failures
    
    def _classify_error(self, error):
        """鍒嗙被閿欒绫诲瀷"""
        error_lower = error.lower()
        
        if "timeout" in error_lower or "瓒呮椂" in error_lower:
            return "瓒呮椂閿欒"
        elif "api" in error_lower or "rate limit" in error_lower:
            return "API 閿欒"
        elif "syntax" in error_lower or "璇硶" in error_lower:
            return "璇硶閿欒"
        elif "import" in error_lower or "module" in error_lower:
            return "渚濊禆閿欒"
        elif "permission" in error_lower or "鏉冮檺" in error_lower:
            return "鏉冮檺閿欒"
        elif "memory" in error_lower or "鍐呭瓨" in error_lower:
            return "鍐呭瓨閿欒"
        else:
            return "鍏朵粬閿欒"
    
    def _generate_diagnosis(self, error_types, stats):
        """鐢熸垚璇婃柇寤鸿"""
        diagnosis = []
        
        # 瓒呮椂闂
        if "瓒呮椂閿欒" in error_types:
            diagnosis.append({
                "problem": "浠诲姟瓒呮椂",
                "cause": f"褰撳墠瓒呮椂璁剧疆 120 绉掞紝骞冲潎鑰楁椂 {stats.get('avg_duration', 0):.1f} 绉?,
                "solution": "寤鸿锛?) 澧炲姞瓒呮椂鍒?180 绉掞紱2) 鎷嗗垎澶嶆潅浠诲姟锛?) 浣跨敤鏇村揩鐨勬ā鍨?
            })
        
        # API 閿欒
        if "API 閿欒" in error_types:
            diagnosis.append({
                "problem": "API 璋冪敤澶辫触",
                "cause": "鍙兘鏄?API Key 鏃犳晥銆佷綑棰濅笉瓒虫垨閫熺巼闄愬埗",
                "solution": "寤鸿锛?) 妫€鏌?API Key锛?) 妫€鏌ヤ綑棰濓紱3) 娣诲姞閲嶈瘯鏈哄埗"
            })
        
        # 鎴愬姛鐜囦綆
        if stats.get("success_rate", 0) < 50:
            diagnosis.append({
                "problem": "鎴愬姛鐜囪繃浣?,
                "cause": f"褰撳墠鎴愬姛鐜?{stats.get('success_rate', 0):.1f}%",
                "solution": "寤鸿锛?) 绠€鍖栦换鍔℃弿杩帮紱2) 娣诲姞绀轰緥浠ｇ爜锛?) 浣跨敤鏇村己鐨勬ā鍨?
            })
        
        # 濡傛灉娌℃湁鏄庣‘闂
        if not diagnosis:
            diagnosis.append({
                "problem": "鏈煡闂",
                "cause": "闇€瑕佹煡鐪嬭缁嗘棩蹇?,
                "solution": "寤鸿锛氭煡鐪?logs/ 鐩綍鐨勮缁嗘棩蹇楁枃浠?
            })
        
        return diagnosis

if __name__ == "__main__":
    analyzer = CoderFailureAnalyzer()
    analyzer.analyze()


