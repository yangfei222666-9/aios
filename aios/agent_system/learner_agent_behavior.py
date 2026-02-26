#!/usr/bin/env python3
"""
AIOS Agent Behavior Learner - 涓撻棬瀛︿範 Agent 琛屼负

鑱岃矗锛?1. 鐩戞帶鎵€鏈?Agent 鐨勪换鍔℃墽琛岃褰?2. 鍒嗘瀽 Agent 鎴愬姛鐜囥€佸伐鍏蜂娇鐢ㄣ€佽€楁椂
3. 璇嗗埆鏈€浣冲疄璺靛拰鍙嶆ā寮?4. 鐢熸垚 Agent 浼樺寲寤鸿
5. 杩借釜 Agent 琛屼负瓒嬪娍

瀛︿範鍐呭锛?- 鍝簺 Agent 鎴愬姛鐜囨渶楂?- 鍝簺宸ュ叿缁勫悎鏈€鏈夋晥
- 鍝簺绛栫暐鏈€鎴愬姛
- 涓嶅悓浠诲姟绫诲瀷閫傚悎鍝釜 Agent
- Agent 琛屼负闅忔椂闂寸殑鍙樺寲

杈撳嚭锛?- AGENT_LEARNER_OK - 鏃犻噸瑕佸彂鐜?- AGENT_LEARNER_SUGGESTIONS:N - 鐢熸垚浜?N 鏉″缓璁?"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict, Counter

# 娣诲姞 AIOS 璺緞
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer

class AgentBehaviorLearner:
    """Agent 琛屼负瀛︿範 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = TraceAnalyzer()

    def run(self) -> Dict:
        """杩愯瀛︿範娴佺▼"""
        print("=" * 60)
        print("  Agent Behavior Learner")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "agent_behavior_learner",
            "learning": {}
        }

        # 1. 鏀堕泦 Agent 琛屼负鏁版嵁
        print("[1/6] 鏀堕泦 Agent 琛屼负鏁版嵁...")
        agent_data = self._collect_agent_data()
        report["learning"]["raw_data"] = agent_data
        print(f"  鏀堕泦浜?{agent_data['total_agents']} 涓?Agent 鐨勬暟鎹?)

        # 2. 鍒嗘瀽鎴愬姛鐜?        print("[2/6] 鍒嗘瀽鎴愬姛鐜?..")
        success_analysis = self._analyze_success_rate(agent_data)
        report["learning"]["success_rate"] = success_analysis
        print(f"  鏈€浣?Agent: {success_analysis.get('best_agent', 'N/A')}")

        # 3. 鍒嗘瀽宸ュ叿浣跨敤
        print("[3/6] 鍒嗘瀽宸ュ叿浣跨敤...")
        tool_analysis = self._analyze_tool_usage(agent_data)
        report["learning"]["tool_usage"] = tool_analysis
        print(f"  璇嗗埆浜?{len(tool_analysis.get('effective_combinations', []))} 涓湁鏁堝伐鍏风粍鍚?)

        # 4. 鍒嗘瀽浠诲姟鑰楁椂
        print("[4/6] 鍒嗘瀽浠诲姟鑰楁椂...")
        duration_analysis = self._analyze_duration(agent_data)
        report["learning"]["duration"] = duration_analysis
        print(f"  鏈€蹇?Agent: {duration_analysis.get('fastest_agent', 'N/A')}")

        # 5. 璇嗗埆鏈€浣冲疄璺?        print("[5/6] 璇嗗埆鏈€浣冲疄璺?..")
        best_practices = self._identify_best_practices(agent_data)
        report["learning"]["best_practices"] = best_practices
        print(f"  璇嗗埆浜?{len(best_practices.get('practices', []))} 涓渶浣冲疄璺?)

        # 6. 鐢熸垚寤鸿
        print("[6/6] 鐢熸垚寤鸿...")
        suggestions = self._generate_suggestions(report["learning"])
        report["suggestions"] = suggestions
        print(f"  鐢熸垚浜?{len(suggestions)} 鏉″缓璁?)

        # 淇濆瓨鎶ュ憡
        self._save_report(report)

        print()
        print("=" * 60)
        if suggestions:
            print(f"  瀹屾垚锛佺敓鎴?{len(suggestions)} 鏉″缓璁?)
        else:
            print("  瀹屾垚锛佹棤閲嶈鍙戠幇")
        print("=" * 60)

        return report

    def _collect_agent_data(self) -> Dict:
        """鏀堕泦 Agent 琛屼负鏁版嵁"""
        agent_stats = defaultdict(lambda: {
            "total_tasks": 0,
            "successes": 0,
            "failures": 0,
            "total_duration": 0,
            "durations": [],
            "tools_used": Counter(),
            "tool_sequences": [],
            "task_types": Counter()
        })
        
        # 浠?trace 鏁版嵁鏀堕泦
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            agent_id = trace.get("agent_id", "unknown")
            success = trace.get("success", False)
            duration = trace.get("duration_sec", 0)
            task_type = trace.get("task_type", "unknown")
            
            agent_stats[agent_id]["total_tasks"] += 1
            if success:
                agent_stats[agent_id]["successes"] += 1
            else:
                agent_stats[agent_id]["failures"] += 1
            
            agent_stats[agent_id]["total_duration"] += duration
            agent_stats[agent_id]["durations"].append(duration)
            agent_stats[agent_id]["task_types"][task_type] += 1
            
            # 缁熻宸ュ叿浣跨敤
            tools_in_task = []
            for tool_call in trace.get("tools_used", []):
                tool = tool_call.get("tool", "unknown")
                agent_stats[agent_id]["tools_used"][tool] += 1
                tools_in_task.append(tool)
            
            # 璁板綍宸ュ叿搴忓垪锛堢敤浜庡垎鏋愬伐鍏风粍鍚堬級
            if len(tools_in_task) > 1:
                agent_stats[agent_id]["tool_sequences"].append({
                    "tools": tools_in_task,
                    "success": success
                })

        return {
            "total_agents": len(agent_stats),
            "agents": dict(agent_stats)
        }

    def _analyze_success_rate(self, data: Dict) -> Dict:
        """鍒嗘瀽鎴愬姛鐜?""
        agents = data.get("agents", {})
        
        success_rates = {}
        for agent_id, stats in agents.items():
            if stats["total_tasks"] >= 5:
                success_rates[agent_id] = {
                    "total_tasks": stats["total_tasks"],
                    "success_rate": stats["successes"] / stats["total_tasks"],
                    "failures": stats["failures"]
                }
        
        # 鎵惧嚭鏈€浣冲拰鏈€宸?        if success_rates:
            best = max(success_rates.items(), key=lambda x: x[1]["success_rate"])
            worst = min(success_rates.items(), key=lambda x: x[1]["success_rate"])
            
            return {
                "agents": success_rates,
                "best_agent": best[0],
                "best_rate": best[1]["success_rate"],
                "worst_agent": worst[0],
                "worst_rate": worst[1]["success_rate"]
            }
        
        return {"agents": {}}

    def _analyze_tool_usage(self, data: Dict) -> Dict:
        """鍒嗘瀽宸ュ叿浣跨敤"""
        agents = data.get("agents", {})
        
        # 鍏ㄥ眬宸ュ叿浣跨敤缁熻
        global_tools = Counter()
        effective_combinations = []
        
        for agent_id, stats in agents.items():
            global_tools.update(stats["tools_used"])
            
            # 鍒嗘瀽宸ュ叿缁勫悎鏁堟灉
            for seq in stats["tool_sequences"]:
                if seq["success"] and len(seq["tools"]) >= 2:
                    combo = " 鈫?".join(seq["tools"][:3])  # 鍓?3 涓伐鍏?                    effective_combinations.append(combo)
        
        # 缁熻鏈€鏈夋晥鐨勫伐鍏风粍鍚?        combo_counter = Counter(effective_combinations)
        
        return {
            "most_used_tools": [tool for tool, _ in global_tools.most_common(10)],
            "effective_combinations": [combo for combo, _ in combo_counter.most_common(5)],
            "total_tool_calls": sum(global_tools.values())
        }

    def _analyze_duration(self, data: Dict) -> Dict:
        """鍒嗘瀽浠诲姟鑰楁椂"""
        agents = data.get("agents", {})
        
        duration_stats = {}
        for agent_id, stats in agents.items():
            if stats["total_tasks"] >= 5:
                durations = stats["durations"]
                duration_stats[agent_id] = {
                    "total_tasks": stats["total_tasks"],
                    "avg_sec": stats["total_duration"] / stats["total_tasks"],
                    "min_sec": min(durations),
                    "max_sec": max(durations),
                    "p50_sec": sorted(durations)[len(durations) // 2]
                }
        
        # 鎵惧嚭鏈€蹇拰鏈€鎱?        if duration_stats:
            fastest = min(duration_stats.items(), key=lambda x: x[1]["avg_sec"])
            slowest = max(duration_stats.items(), key=lambda x: x[1]["avg_sec"])
            
            return {
                "agents": duration_stats,
                "fastest_agent": fastest[0],
                "fastest_avg_sec": fastest[1]["avg_sec"],
                "slowest_agent": slowest[0],
                "slowest_avg_sec": slowest[1]["avg_sec"]
            }
        
        return {"agents": {}}

    def _identify_best_practices(self, data: Dict) -> Dict:
        """璇嗗埆鏈€浣冲疄璺?""
        agents = data.get("agents", {})
        practices = []
        
        for agent_id, stats in agents.items():
            if stats["total_tasks"] >= 10 and stats["successes"] / stats["total_tasks"] >= 0.8:
                # 楂樻垚鍔熺巼 Agent 鐨勭壒寰?                practices.append({
                    "agent": agent_id,
                    "success_rate": stats["successes"] / stats["total_tasks"],
                    "most_used_tools": [tool for tool, _ in stats["tools_used"].most_common(3)],
                    "avg_duration": stats["total_duration"] / stats["total_tasks"],
                    "task_types": [task for task, _ in stats["task_types"].most_common(3)]
                })
        
        return {
            "practices": practices,
            "count": len(practices)
        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """鐢熸垚寤鸿"""
        suggestions = []

        # 1. 鎴愬姛鐜囧缓璁?        success_data = learning.get("success_rate", {})
        if success_data.get("worst_rate", 1.0) < 0.6:
            suggestions.append({
                "type": "low_success_rate",
                "priority": "high",
                "agent": success_data["worst_agent"],
                "description": f"Agent '{success_data['worst_agent']}' 鎴愬姛鐜囦粎 {success_data['worst_rate']:.1%}",
                "action": f"鍙傝€?{success_data.get('best_agent', 'N/A')}锛坽success_data.get('best_rate', 0):.1%}锛夌殑绛栫暐"
            })

        # 2. 鑰楁椂寤鸿
        duration_data = learning.get("duration", {})
        if duration_data.get("slowest_avg_sec", 0) > duration_data.get("fastest_avg_sec", 0) * 3:
            suggestions.append({
                "type": "high_duration",
                "priority": "medium",
                "agent": duration_data["slowest_agent"],
                "description": f"Agent '{duration_data['slowest_agent']}' 骞冲潎鑰楁椂 {duration_data['slowest_avg_sec']:.1f}s锛屾瘮 {duration_data['fastest_agent']}锛坽duration_data['fastest_avg_sec']:.1f}s锛夋參 3 鍊嶄互涓?,
                "action": "浼樺寲浠诲姟鎵ц娴佺▼鎴栧噺灏戜笉蹇呰鐨勫伐鍏疯皟鐢?
            })

        # 3. 宸ュ叿浣跨敤寤鸿
        tool_data = learning.get("tool_usage", {})
        if tool_data.get("effective_combinations"):
            suggestions.append({
                "type": "tool_combination",
                "priority": "low",
                "description": f"鍙戠幇鏈夋晥宸ュ叿缁勫悎锛歿', '.join(tool_data['effective_combinations'][:3])}",
                "action": "鍦ㄦ柊 Agent 涓帹骞胯繖浜涘伐鍏风粍鍚?
            })

        # 4. 鏈€浣冲疄璺靛缓璁?        best_practices = learning.get("best_practices", {})
        if best_practices.get("count", 0) > 0:
            top_practice = best_practices["practices"][0]
            suggestions.append({
                "type": "best_practice",
                "priority": "low",
                "agent": top_practice["agent"],
                "description": f"Agent '{top_practice['agent']}' 琛ㄧ幇浼樼锛堟垚鍔熺巼 {top_practice['success_rate']:.1%}锛夛紝甯哥敤宸ュ叿锛歿', '.join(top_practice['most_used_tools'])}",
                "action": "灏嗗叾绛栫暐鎺ㄥ箍鍒板叾浠?Agent"
            })

        return suggestions

    def _save_report(self, report: Dict):
        """淇濆瓨鎶ュ憡"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"agent_behavior_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 鎶ュ憡宸蹭繚瀛? {report_file}")


def main():
    """涓诲嚱鏁?""
    agent = AgentBehaviorLearner()
    report = agent.run()
    
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nAGENT_LEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nAGENT_LEARNER_OK")


if __name__ == "__main__":
    main()

