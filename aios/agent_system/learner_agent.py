#!/usr/bin/env python3
"""
AIOS Learner Agent - Responsible for learning and improving the AIOS system

Responsibilities:
1. Learn patterns from historical data
2. Extract best practices
3. Identify anti-patterns (practices to avoid)
4. Generate knowledge base
5. Update system strategies
6. Continuous improvement

Learning content:
- Provider performance (which model has higher success rate)
- Playbook effectiveness (which rules are effective)
- Agent behavior (which strategies succeed)
- Error patterns (which errors repeat)
- Optimization results (which optimizations are effective)

Working mode:
- Run automatically once per day
- Analyze data from the last 7 days
- Generate learning report
- Update knowledge base
- Propose improvement suggestions
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter, defaultdict

# Add AIOS path
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))
sys.path.insert(0, str(AIOS_ROOT / "agent_system"))

from agent_tracer import TraceAnalyzer


class AIOSLearnerAgent:
    """AIOS Learner Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data"
        self.knowledge_dir = self.data_dir / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = TraceAnalyzer()
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"

    def run(self) -> Dict:
        """Run the complete learning workflow"""
        print("=" * 60)
        print("  AIOS Learner Agent")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "learning": {}
        }

        # 1. Learn Provider performance
        print("[1/6] Learning Provider performance...")
        provider_learning = self._learn_provider_performance()
        report["learning"]["providers"] = provider_learning
        print(f"  Analyzed {provider_learning['total_calls']} calls")

        # 2. Learn Playbook effectiveness
        print("[2/6] Learning Playbook effectiveness...")
        playbook_learning = self._learn_playbook_effectiveness()
        report["learning"]["playbooks"] = playbook_learning
        print(f"  Analyzed {playbook_learning['total_executions']} executions")

        # 3. Learn Agent behavior
        print("[3/6] Learning Agent behavior...")
        agent_learning = self._learn_agent_behavior()
        report["learning"]["agents"] = agent_learning
        print(f"  Analyzed {agent_learning['total_agents']} Agents")

        # 4. Identify error patterns
        print("[4/6] Identifying error patterns...")
        error_patterns = self._identify_error_patterns()
        report["learning"]["error_patterns"] = error_patterns
        print(f"  Identified {len(error_patterns['patterns'])} error patterns")

        # 5. Evaluate optimization results
        print("[5/6] Evaluating optimization results...")
        optimization_learning = self._evaluate_optimizations()
        report["learning"]["optimizations"] = optimization_learning
        print(f"  Evaluated {optimization_learning['total_optimizations']} optimizations")

        # 6. Generate improvement suggestions
        print("[6/6] Generating improvement suggestions...")
        suggestions = self._generate_suggestions(report["learning"])
        report["suggestions"] = suggestions
        print(f"  Generated {len(suggestions)} suggestions")

        # Save report and knowledge base
        self._save_report(report)
        self._update_knowledge_base(report)

        print()
        print("=" * 60)
        print(f"  Done! Generated {len(suggestions)} improvement suggestions")
        print("=" * 60)

        return report

    def _learn_provider_performance(self) -> Dict:
        """Learn Provider performance"""
        # Simplified: read router call records from events.jsonl
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

        # Calculate success rate and average duration
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
        """Learn Playbook effectiveness"""
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

        # Calculate success rate
        results = {}
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
        """Learn Agent behavior"""
        # Learn from trace data
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
            
            # Count tool usage
            for tool_call in trace.get("tools_used", []):
                tool = tool_call.get("tool", "unknown")
                agent_stats[agent_id]["tools_used"][tool] += 1

        # Calculate metrics
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
        """Identify error patterns"""
        # Use TraceAnalyzer failure pattern analysis
        patterns = self.analyzer.get_failure_patterns(min_occurrences=3, env="prod")
        
        return {
            "patterns": patterns,
            "total_patterns": len(patterns)
        }

    def _evaluate_optimizations(self) -> Dict:
        """Evaluate optimization results"""
        # Read optimization reports
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
            "evaluations": evaluations[-5:]  # Last 5
        }

    def _generate_suggestions(self, learning: Dict) -> List[Dict]:
        """Generate improvement suggestions"""
        suggestions = []

        # 1. Provider suggestions
        providers = learning.get("providers", {}).get("providers", {})
        for provider, stats in providers.items():
            if stats["success_rate"] < 0.8 and stats["calls"] >= 10:
                suggestions.append({
                    "type": "provider_reliability",
                    "priority": "high",
                    "description": f"{provider} success rate is low ({stats['success_rate']:.1%}), suggest checking config or switching Provider",
                    "data": stats
                })

        # 2. Playbook suggestions
        playbooks = learning.get("playbooks", {}).get("playbooks", {})
        for playbook, stats in playbooks.items():
            if stats["success_rate"] < 0.7 and stats["executions"] >= 5:
                suggestions.append({
                    "type": "playbook_effectiveness",
                    "priority": "medium",
                    "description": f"Playbook {playbook} success rate is low ({stats['success_rate']:.1%}), suggest optimizing rules",
                    "data": stats
                })

        # 3. Agent suggestions
        agents = learning.get("agents", {}).get("agents", {})
        for agent_id, stats in agents.items():
            if stats["success_rate"] < 0.7 and stats["total_tasks"] >= 10:
                suggestions.append({
                    "type": "agent_reliability",
                    "priority": "high",
                    "description": f"Agent {agent_id} success rate is low ({stats['success_rate']:.1%}), suggest improving reliability",
                    "data": stats
                })

        # 4. Error pattern suggestions
        error_patterns = learning.get("error_patterns", {}).get("patterns", [])
        for pattern in error_patterns[:3]:  # Top 3 frequent errors
            suggestions.append({
                "type": "error_pattern",
                "priority": "high",
                "description": f"Error pattern '{pattern['error_signature']}' occurred {pattern['occurrences']} times, suggest creating fix strategy",
                "data": pattern
            })

        return suggestions

    def _save_report(self, report: Dict):
        """Save learning report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.knowledge_dir / f"learning_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")

    def _update_knowledge_base(self, report: Dict):
        """Update knowledge base"""
        kb_file = self.knowledge_dir / "knowledge_base.json"
        
        # Read existing knowledge base
        if kb_file.exists():
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

        # Update knowledge base
        kb["last_updated"] = report["timestamp"]
        
        # Update Provider knowledge
        providers = report["learning"].get("providers", {}).get("providers", {})
        for provider, stats in providers.items():
            if provider not in kb["providers"]:
                kb["providers"][provider] = {"history": []}
            kb["providers"][provider]["latest"] = stats
            kb["providers"][provider]["history"].append({
                "timestamp": report["timestamp"],
                "stats": stats
            })
            # Keep only last 30 entries
            kb["providers"][provider]["history"] = kb["providers"][provider]["history"][-30:]

        # Update Agent knowledge
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

        # Save knowledge base
        with open(kb_file, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        
        print(f"Knowledge base updated: {kb_file}")


def main():
    """Main function"""
    agent = AIOSLearnerAgent()
    report = agent.run()
    
    # Output summary
    suggestions = report.get("suggestions", [])
    if suggestions:
        print(f"\nLEARNER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nLEARNER_OK")


if __name__ == "__main__":
    main()
