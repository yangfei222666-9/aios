#!/usr/bin/env python3
"""
AIOS Learner Agent - 涓撻棬璐熻矗瀛︿範鍜屾敼杩?AIOS 绯荤粺

鑱岃矗锛?1. 浠庡巻鍙叉暟鎹腑瀛︿範妯″紡
2. 鎻愬彇鏈€浣冲疄璺?3. 璇嗗埆鍙嶆ā寮忥紙搴旇閬垮厤鐨勫仛娉曪級
4. 鐢熸垚鐭ヨ瘑搴?5. 鏇存柊绯荤粺绛栫暐
6. 鎸佺画鏀硅繘

瀛︿範鍐呭锛?- Provider 鎬ц兘锛堝摢涓ā鍨嬫垚鍔熺巼楂橈級
- Playbook 鏁堟灉锛堝摢浜涜鍒欐湁鏁堬級
- Agent 琛屼负锛堝摢浜涚瓥鐣ユ垚鍔燂級
- 閿欒妯″紡锛堝摢浜涢敊璇噸澶嶅嚭鐜帮級
- 浼樺寲鏁堟灉锛堝摢浜涗紭鍖栨湁鏁堬級

宸ヤ綔妯″紡锛?- 姣忓ぉ鑷姩杩愯涓€娆?- 鍒嗘瀽鏈€杩?7 澶╃殑鏁版嵁
- 鐢熸垚瀛︿範鎶ュ憡
- 鏇存柊鐭ヨ瘑搴?- 鎻愬嚭鏀硅繘寤鸿
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter, defaultdict

# 娣诲姞 AIOS 璺緞
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class AIOSLearnerAgent:
    """AIOS 瀛︿範 Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data"
        self.knowledge_dir = self.data_dir / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = TraceAnalyzer()
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """杩愯瀹屾暣瀛︿範娴佺▼"""
        print("=" * 60)
        print("  AIOS Learner Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "learning": {}
        }

        # 1. 瀛︿範 Provider 鎬ц兘
        print("[1/6] 瀛︿範 Provider 鎬ц兘...")
        provider_learning = self._learn_provider_performance()
        report["learning"]["providers"] = provider_learning
        print(f"  鍒嗘瀽浜?{provider_learning['total_calls']} 娆¤皟鐢?)

        # 2. 瀛︿範 Playbook 鏁堟灉
        print("[2/6] 瀛︿範 Playbook 鏁堟灉...")
        playbook_learning = self._learn_playbook_effectiveness()
        report["learning"]["playbooks"] = playbook_learning
        print(f"  鍒嗘瀽浜?{playbook_learning['total_executions']} 娆℃墽琛?)

        # 3. 瀛︿範 Agent 琛屼负
        print("[3/6] 瀛︿範 Agent 琛屼负...")
        agent_learning = self._learn_agent_behavior()
        report["learning"]["agents"] = agent_learning
        print(f"  鍒嗘瀽浜?{agent_learning['total_agents']} 涓?Agent")

        # 4. 璇嗗埆閿欒妯″紡
        print("[4/6] 璇嗗埆閿欒妯″紡...")
        error_patterns = self._identify_error_patterns()
        report["learning"]["error_patterns"] = error_patterns
        print(f"  璇嗗埆浜?{len(error_patterns['patterns'])} 涓敊璇ā寮?)

        # 5. 璇勪及浼樺寲鏁堟灉
        print("[5/6] 璇勪及浼樺寲鏁堟灉...")
        optimization_learning = self._evaluate_optimizations()
        report["learning"]["optimizations"] = optimization_learning
        print(f"  璇勪及浜?{optimization_learning['total_optimizations']} 涓紭鍖?)

        # 6. 鐢熸垚鏀硅繘寤鸿
        print("[6/6] 鐢熸垚鏀硅繘寤鸿...")
        suggestions = self._generate_suggestions(report["learning"])
        report["suggestions"] = suggestions
        print(f"  鐢熸垚浜?{len(suggestions)} 鏉″缓璁?)

        # 淇濆瓨鎶ュ憡鍜岀煡璇嗗簱
        self._save_report(report)
        self._update_knowledge_base(report)

        print()
        print("=" * 60)
        print(f"  瀹屾垚锛佺敓鎴?{len(suggestions)} 鏉℃敼杩涘缓璁?)
        print("=" * 60)

        return report

    def _learn_provider_performance(self) -> Dict:
        """瀛︿範 Provider 鎬ц兘"""
        # 绠€鍖栫増锛氫粠 events.jsonl 璇诲彇 router 璋冪敤璁板綍
        provider_stats = defaultdict(lambda: {"calls": 0, "successes": 0, "failures": 0, "total_duration": 0})
        
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("type") == "router_call":
                            provider = event.get("provider", "unknown")
                            success = event.get("success", False)
                            duration = event.get("duration_ms", 0)
                            
                            provider_stats[provider]["calls"] += 1
                            if success:
                                provider_stats[provider]["successes"] += 1
                            else:
                                provider_stats[provider]["failures"] += 1
                            provider_stats[provider]["total_duration"] += duration
                    except:
                        continue

        # 璁＄畻鎴愬姛鐜囧拰骞冲潎鑰楁椂
        results = {}
        for provider, stats in provider_stats.items():
            if stats["calls"] > 0:
                results[provider] = {
                    "calls": stats["calls"],
                    "success_rate": stats["successes"] / stats["calls"],
                    "avg_duration_ms": stats["total_duration"] / stats["calls"]
                }

        return {
            "total_calls": sum(s["calls"] for s in provider_stats.values()),
            "providers": results
        }

    def _learn_playbook_effectiveness(self) -> Dict:
        """瀛︿範 Playbook 鏁堟灉"""
        playbook_stats = defaultdict(lambda: {"executions": 0, "successes": 0, "failures": 0})
        
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("type") == "reactor_action":
                            playbook = event.get("playbook_id", "unknown")
                            success = event.get("success", False)
                            
                            playbook_stats[playbook]["executions"] += 1
                            if success:
                                playbook_stats[playbook]["successes"] += 1
                            else:
                                playbook_stats[playbook]["failures"] += 1
                    except:
                        continue

        # 璁＄畻鎴愬姛鐜?        results = {}
        for playbook, stats in playbook_stats.items():
            if stats["executions"] > 0:
                results[playbook] = {
                    "executions": stats["executions"],
                    "success_rate": stats["successes"] / stats["executions"]
                }

        return {
            "total_executions": sum(s["executions"] for s in playbook_stats.values()),
            "playbooks": results
        }

    def _learn_agent_behavior(self) -> Dict:
        """瀛︿範 Agent 琛屼负"""
        # 浠?trace 鏁版嵁瀛︿範
        agent_stats = {}
        
        for trace in self.analyzer.traces:
            if trace.get("env", "prod") != "prod":
                continue
            
            agent_id = trace.get("agent_id", "unknown")
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "total_tasks": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_duration": 0,
                    "tools_used": Counter()
                }
            
            agent_stats[agent_id]["total_tasks"] += 1
            if trace.get("success", False):
                agent_stats[agent_id]["successes"] += 1
            else:
                agent_stats[agent_id]["failures"] += 1
            
            agent_stats[agent_id]["total_duration"] += trace.get("duration_sec", 0)
            
            # 缁熻宸ュ叿浣跨敤
            for tool_call in trace.get("tools_used", []):
                tool = tool_call.get("tool", "unknown")
                agent_stats[agent_id]["tools_used"][tool] += 1

        # 璁＄畻鎸囨爣
        results = {}
        for agent_id, stats in agent_stats.items():
            if stats["total_tasks"] > 0:
                results[agent_id] = {
                    "total_tasks": stats["total_tasks"],
                    "success_rate": stats["successes"] / stats["total_tasks"],
                    "avg_duration": stats["total_duration"] / stats["total_tasks"],
                    "most_used_tools": [tool for tool, _ in stats["tools_used"].most_common(3)]
                }

        return {
            "total_agents": len(agent_stats),
            "agents": results
        }

    def _identify_error_patterns(self) -> Dict:
        """璇嗗埆閿欒妯″紡"""
        # 浣跨敤 TraceAnalyzer 鐨勫け璐ユā寮忓垎鏋?        patterns = self.analyzer.get_failure_patterns(min_occurrences=3, env="prod")
        
        return {
            "patterns": patterns,
            "total_patterns": len(patterns)
        }

    def _evaluate_optimizations(self) -> Dict:
        """璇勪及浼樺寲鏁堟灉"""
        # 璇诲彇浼樺寲鎶ュ憡
        optimizer_reports_dir = self.data_dir / "optimizer_reports"
        
        if not optimizer_reports_dir.exists():
            return {"total_optimizations": 0, "evaluations": []}
        
        evaluations = []
        for report_file in sorted(optimizer_reports_dir.glob("optimizer_*.json")):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                results = report.get("phases", {}).get("results", {})
                evaluations.append({
                    "timestamp": report.get("timestamp"),
                    "applied": results.get("applied", 0),
                    "failed": results.get("failed", 0)
                })
            except:
                continue

        return {
            "total_optimizations": sum(e["applied"] for e in evaluations),
            "evaluations": evaluations[-5:]  # 鏈€杩?5 娆?        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """鐢熸垚鏀硅繘寤鸿"""
        suggestions = []

        # 1. Provider 寤鸿
        providers = learning.get("providers", {}).get("providers", {})
        for provider, stats in providers.items():
            if stats["success_rate"] < 0.8 and stats["calls"] >= 10:
                suggestions.append({
                    "type": "provider_reliability",
                    "priority": "high",
                    "description": f"{provider} 鎴愬姛鐜囪緝浣庯紙{stats['success_rate']:.1%}锛夛紝寤鸿妫€鏌ラ厤缃垨鍒囨崲 Provider",
                    "data": stats
                })

        # 2. Playbook 寤鸿
        playbooks = learning.get("playbooks", {}).get("playbooks", {})
        for playbook, stats in playbooks.items():
            if stats["success_rate"] < 0.7 and stats["executions"] >= 5:
                suggestions.append({
                    "type": "playbook_effectiveness",
                    "priority": "medium",
                    "description": f"Playbook {playbook} 鎴愬姛鐜囪緝浣庯紙{stats['success_rate']:.1%}锛夛紝寤鸿浼樺寲瑙勫垯",
                    "data": stats
                })

        # 3. Agent 寤鸿
        agents = learning.get("agents", {}).get("agents", {})
        for agent_id, stats in agents.items():
            if stats["success_rate"] < 0.7 and stats["total_tasks"] >= 10:
                suggestions.append({
                    "type": "agent_reliability",
                    "priority": "high",
                    "description": f"Agent {agent_id} 鎴愬姛鐜囪緝浣庯紙{stats['success_rate']:.1%}锛夛紝寤鸿鎻愬崌鍙潬鎬?,
                    "data": stats
                })

        # 4. 閿欒妯″紡寤鸿
        error_patterns = learning.get("error_patterns", {}).get("patterns", [])
        for pattern in error_patterns[:3]:  # 鍓?3 涓珮棰戦敊璇?            suggestions.append({
                "type": "error_pattern",
                "priority": "high",
                "description": f"閿欒妯″紡 '{pattern['error_signature']}' 鍑虹幇 {pattern['occurrences']} 娆★紝寤鸿鍒跺畾淇绛栫暐",
                "data": pattern
            })

        return suggestions

    def _save_report(self, report: Dict):
        """淇濆瓨瀛︿範鎶ュ憡"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.knowledge_dir / f"learning_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n馃搫 鎶ュ憡宸蹭繚瀛? {report_file}")

    def _update_knowledge_base(self, report: Dict):
        """鏇存柊鐭ヨ瘑搴?""
        kb_file = self.knowledge_dir / "knowledge_base.json"
        
        # 璇诲彇鐜版湁鐭ヨ瘑搴?        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                kb = json.load(f)
        else:
            kb = {
                "last_updated": None,
                "providers": {},
                "playbooks": {},
                "agents": {},
                "error_patterns": [],
                "best_practices": []
            }

        # 鏇存柊鐭ヨ瘑搴?        kb["last_updated"] = report["timestamp"]
        
        # 鏇存柊 Provider 鐭ヨ瘑
        providers = report["learning"].get("providers", {}).get("providers", {})
        for provider, stats in providers.items():
            if provider not in kb["providers"]:
                kb["providers"][provider] = {"history": []}
            kb["providers"][provider]["latest"] = stats
            kb["providers"][provider]["history"].append({
                "timestamp": report["timestamp"],
                "stats": stats
            })
            # 鍙繚鐣欐渶杩?30 鏉?            kb["providers"][provider]["history"] = kb["providers"][provider]["history"][-30:]

        # 鏇存柊 Agent 鐭ヨ瘑
        agents = report["learning"].get("agents", {}).get("agents", {})
        for agent_id, stats in agents.items():
            if agent_id not in kb["agents"]:
                kb["agents"][agent_id] = {"history": []}
            kb["agents"][agent_id]["latest"] = stats
            kb["agents"][agent_id]["history"].append({
                "timestamp": report["timestamp"],
                "stats": stats
            })
            kb["agents"][agent_id]["history"] = kb["agents"][agent_id]["history"][-30:]

        # 淇濆瓨鐭ヨ瘑搴?        with open(kb_file, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        
        print(f"馃摎 鐭ヨ瘑搴撳凡鏇存柊: {kb_file}")


def main():
    """涓诲嚱鏁?""
    agent = AIOSLearnerAgent()
    report = agent.run()
    
    # 杈撳嚭鎽樿
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nLEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nLEARNER_OK")


if __name__ == "__main__":
    main()

