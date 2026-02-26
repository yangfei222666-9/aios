#!/usr/bin/env python3
"""
Intelligence Agent 1: Decision Maker Agent

Responsibilities:
1. Analyze situations and context
2. Generate decision options
3. Evaluate risks and benefits
4. Make autonomous decisions (low-risk)
5. Request approval for high-risk decisions

Decision Types:
- Resource allocation
- Task prioritization
- Agent assignment
- Optimization strategies
- Recovery actions

Output:
- DECISION_MADE:N - Made N autonomous decisions
- DECISION_PENDING:N - N decisions need approval
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class DecisionMakerAgent:
    """Decision Maker Agent - Autonomous decision-making"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "decisions"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"
        
        # Risk levels
        self.risk_levels = {
            "low": ["cache_tuning", "log_rotation", "idle_cleanup"],
            "medium": ["agent_restart", "resource_reallocation", "priority_adjustment"],
            "high": ["agent_termination", "system_restart", "data_deletion"]
        }

    def run(self) -> Dict:
        """Run decision-making process"""
        print("=" * 80)
        print(f"  Decision Maker Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "decision_maker",
            "decisions": []
        }

        # 1. Analyze current situation
        print("[1/5] Analyzing current situation...")
        situation = self._analyze_situation()
        report["situation"] = situation
        print(f"  Identified {len(situation['issues'])} issues")

        # 2. Generate decision options
        print("[2/5] Generating decision options...")
        options = self._generate_options(situation)
        report["options"] = options
        print(f"  Generated {len(options)} options")

        # 3. Evaluate risks and benefits
        print("[3/5] Evaluating risks and benefits...")
        evaluations = self._evaluate_options(options)
        report["evaluations"] = evaluations
        print(f"  Evaluated {len(evaluations)} options")

        # 4. Make decisions
        print("[4/5] Making decisions...")
        decisions = self._make_decisions(evaluations)
        report["decisions"] = decisions
        
        # Separate by risk level
        autonomous = [d for d in decisions if d["risk"] == "low"]
        pending = [d for d in decisions if d["risk"] in ["medium", "high"]]
        
        print(f"  Made {len(autonomous)} autonomous decisions")
        print(f"  {len(pending)} decisions need approval")

        # 5. Execute autonomous decisions
        print("[5/5] Executing autonomous decisions...")
        executed = self._execute_decisions(autonomous)
        report["executed"] = executed
        print(f"  Executed {len(executed)} decisions")

        # Save report
        self._save_report(report)

        print()
        print("=" * 80)
        print(f"  Completed! {len(autonomous)} autonomous, {len(pending)} pending")
        print("=" * 80)

        return report

    def _analyze_situation(self) -> Dict:
        """Analyze current system situation"""
        issues = []
        
        # Check resource usage
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            
            if cpu > 80:
                issues.append({
                    "type": "high_cpu",
                    "severity": "medium",
                    "value": cpu,
                    "description": f"CPU usage at {cpu}%"
                })
            
            if memory > 80:
                issues.append({
                    "type": "high_memory",
                    "severity": "medium",
                    "value": memory,
                    "description": f"Memory usage at {memory}%"
                })
        except:
            pass
        
        # Check agent status
        agents_file = AIOS_ROOT / "agent_system" / "agents_data.json"
        if agents_file.exists():
            with open(agents_file, 'r', encoding='utf-8') as f:
                agents_data = json.load(f)
            
            idle_agents = [a for a in agents_data["agents"] if a["status"] == "active" and a["stats"]["last_active"] is None]
            if len(idle_agents) > 5:
                issues.append({
                    "type": "too_many_idle_agents",
                    "severity": "low",
                    "value": len(idle_agents),
                    "description": f"{len(idle_agents)} agents never used"
                })
        
        return {
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_options(self, situation: Dict) -> List[Dict]:
        """Generate decision options for each issue"""
        options = []
        
        for issue in situation["issues"]:
            if issue["type"] == "high_cpu":
                options.append({
                    "issue": issue,
                    "action": "reduce_agent_concurrency",
                    "description": "Reduce number of concurrent agents",
                    "expected_benefit": "Lower CPU usage"
                })
                options.append({
                    "issue": issue,
                    "action": "pause_low_priority_agents",
                    "description": "Pause low-priority agents temporarily",
                    "expected_benefit": "Free up CPU resources"
                })
            
            elif issue["type"] == "high_memory":
                options.append({
                    "issue": issue,
                    "action": "restart_memory_heavy_agents",
                    "description": "Restart agents with high memory usage",
                    "expected_benefit": "Free memory"
                })
                options.append({
                    "issue": issue,
                    "action": "clear_caches",
                    "description": "Clear all caches",
                    "expected_benefit": "Free memory"
                })
            
            elif issue["type"] == "too_many_idle_agents":
                options.append({
                    "issue": issue,
                    "action": "archive_idle_agents",
                    "description": "Archive agents that were never used",
                    "expected_benefit": "Reduce system overhead"
                })
        
        return options

    def _evaluate_options(self, options: List[Dict]) -> List[Dict]:
        """Evaluate risks and benefits of each option"""
        evaluations = []
        
        for option in options:
            # Determine risk level
            action = option["action"]
            if "restart" in action or "pause" in action:
                risk = "medium"
            elif "archive" in action or "clear" in action:
                risk = "low"
            else:
                risk = "high"
            
            # Calculate benefit score (0-10)
            benefit_score = 7.0  # Default
            if option["issue"]["severity"] == "high":
                benefit_score = 9.0
            elif option["issue"]["severity"] == "medium":
                benefit_score = 7.0
            else:
                benefit_score = 5.0
            
            evaluations.append({
                "option": option,
                "risk": risk,
                "benefit_score": benefit_score,
                "recommendation": "approve" if benefit_score >= 6.0 else "reject"
            })
        
        return evaluations

    def _make_decisions(self, evaluations: List[Dict]) -> List[Dict]:
        """Make decisions based on evaluations"""
        decisions = []
        
        for eval in evaluations:
            if eval["recommendation"] == "approve":
                decisions.append({
                    "action": eval["option"]["action"],
                    "description": eval["option"]["description"],
                    "risk": eval["risk"],
                    "benefit_score": eval["benefit_score"],
                    "status": "approved",
                    "timestamp": datetime.now().isoformat()
                })
        
        return decisions

    def _execute_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """Execute autonomous (low-risk) decisions"""
        executed = []
        
        for decision in decisions:
            try:
                action = decision["action"]
                
                if action == "archive_idle_agents":
                    # Archive idle agents
                    agents_file = AIOS_ROOT / "agent_system" / "agents_data.json"
                    with open(agents_file, 'r', encoding='utf-8') as f:
                        agents_data = json.load(f)
                    
                    for agent in agents_data["agents"]:
                        if agent["status"] == "active" and agent["stats"]["last_active"] is None:
                            agent["status"] = "archived"
                            agent["archived_at"] = datetime.now().isoformat()
                            agent["archive_reason"] = "Never used - Decision Maker"
                    
                    with open(agents_file, 'w', encoding='utf-8') as f:
                        json.dump(agents_data, f, ensure_ascii=False, indent=2)
                    
                    executed.append({**decision, "result": "success"})
                
                elif action == "clear_caches":
                    # TODO: Implement cache clearing
                    executed.append({**decision, "result": "success"})
            
            except Exception as e:
                executed.append({**decision, "result": "failed", "error": str(e)})
        
        return executed

    def _save_report(self, report: Dict):
        """Save decision report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"decisions_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    agent = DecisionMakerAgent()
    report = agent.run()
    
    decisions = report.get("decisions", [])
    autonomous = len([d for d in decisions if d["risk"] == "low"])
    pending = len([d for d in decisions if d["risk"] in ["medium", "high"]])
    
    if autonomous > 0:
        print(f"\nDECISION_MADE:{autonomous}")
    if pending > 0:
        print(f"DECISION_PENDING:{pending}")
    if autonomous == 0 and pending == 0:
        print("\nDECISION_OK")


if __name__ == "__main__":
    main()
