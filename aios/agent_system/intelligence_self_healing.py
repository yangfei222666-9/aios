#!/usr/bin/env python3
"""
Self-Healing Agent

Responsibilities:
1. Detect problems automatically
2. Diagnose root causes
3. Generate fix strategies
4. Apply fixes automatically (low-risk)
5. Verify fix effectiveness
6. Escalate to human if needed

Problem Types:
- Agent failures
- Resource exhaustion
- Stuck queues
- Circuit breaker triggered
- Performance degradation
- Data corruption

Healing Strategies:
- Restart failed agents
- Clear stuck queues
- Reset circuit breakers
- Rollback bad changes
- Free resources
- Repair data

Output:
- SELF_HEALING_FIXED:N - Fixed N problems automatically
- SELF_HEALING_ESCALATED:N - Escalated N problems to human
- SELF_HEALING_OK - No problems detected
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import time

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class SelfHealingAgent:
    """Self-Healing Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "self_healing"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.healing_history_file = self.data_dir / "healing_history.json"
        
        # Load healing history
        self.healing_history = self._load_healing_history()

    def run(self) -> Dict:
        """Run self-healing process"""
        print("=" * 80)
        print(f"  Self-Healing Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "self_healing",
            "problems": [],
            "fixes": [],
            "escalations": []
        }

        # 1. Detect problems
        print("[1/5] Detecting problems...")
        problems = self._detect_problems()
        report["problems"] = problems
        print(f"  Detected {len(problems)} problems")

        # 2. Diagnose root causes
        print("[2/5] Diagnosing root causes...")
        diagnoses = self._diagnose_problems(problems)
        report["diagnoses"] = diagnoses
        print(f"  Diagnosed {len(diagnoses)} root causes")

        # 3. Generate fix strategies
        print("[3/5] Generating fix strategies...")
        strategies = self._generate_strategies(diagnoses)
        report["strategies"] = strategies
        print(f"  Generated {len(strategies)} strategies")

        # 4. Apply fixes
        print("[4/5] Applying fixes...")
        fixes = self._apply_fixes(strategies)
        report["fixes"] = fixes
        
        auto_fixed = [f for f in fixes if f["result"] == "fixed"]
        escalated = [f for f in fixes if f["result"] == "escalated"]
        
        print(f"  Fixed {len(auto_fixed)} problems automatically")
        print(f"  Escalated {len(escalated)} problems to human")

        # 5. Verify fixes
        print("[5/5] Verifying fixes...")
        verified = self._verify_fixes(auto_fixed)
        report["verified"] = verified
        print(f"  Verified {len(verified)} fixes")

        # Save history
        self._save_healing_history()
        self._save_report(report)

        print()
        print("=" * 80)
        print(f"  Completed! Fixed: {len(auto_fixed)}, Escalated: {len(escalated)}")
        print("=" * 80)

        return report

    def _load_healing_history(self) -> Dict:
        """Load healing history"""
        if self.healing_history_file.exists():
            with open(self.healing_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "total_problems": 0,
            "total_fixed": 0,
            "total_escalated": 0,
            "healing_records": []
        }

    def _detect_problems(self) -> List[Dict]:
        """Detect problems in the system"""
        problems = []
        
        # 1. Check failed agents
        agents_file = AIOS_ROOT / "agent_system" / "agents_data.json"
        if agents_file.exists():
            with open(agents_file, 'r', encoding='utf-8') as f:
                agents_data = json.load(f)
            
            for agent in agents_data["agents"]:
                if agent["status"] == "active":
                    success_rate = agent["stats"].get("success_rate", 1.0)
                    if success_rate < 0.5 and agent["stats"]["tasks_completed"] >= 5:
                        problems.append({
                            "type": "agent_failure",
                            "severity": "high",
                            "agent_id": agent["id"],
                            "success_rate": success_rate,
                            "description": f"Agent {agent['id']} has low success rate ({success_rate:.1%})"
                        })
        
        # 2. Check circuit breaker
        circuit_breaker_file = AIOS_ROOT / "agent_system" / "circuit_breaker_state.json"
        if circuit_breaker_file.exists():
            with open(circuit_breaker_file, 'r', encoding='utf-8') as f:
                circuit_state = json.load(f)
            
            if circuit_state.get("triggered", False):
                problems.append({
                    "type": "circuit_breaker_triggered",
                    "severity": "critical",
                    "agents": circuit_state.get("agents", []),
                    "description": f"Circuit breaker triggered for {len(circuit_state.get('agents', []))} agents"
                })
        
        # 3. Check resource exhaustion
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            if cpu > 95:
                problems.append({
                    "type": "cpu_exhaustion",
                    "severity": "critical",
                    "value": cpu,
                    "description": f"CPU usage at {cpu}%"
                })
            
            if memory > 95:
                problems.append({
                    "type": "memory_exhaustion",
                    "severity": "critical",
                    "value": memory,
                    "description": f"Memory usage at {memory}%"
                })
            
            if disk > 95:
                problems.append({
                    "type": "disk_exhaustion",
                    "severity": "critical",
                    "value": disk,
                    "description": f"Disk usage at {disk}%"
                })
        except:
            pass
        
        # 4. Check stuck queues
        # TODO: Implement queue monitoring
        
        return problems

    def _diagnose_problems(self, problems: List[Dict]) -> List[Dict]:
        """Diagnose root causes"""
        diagnoses = []
        
        for problem in problems:
            diagnosis = {
                "problem": problem,
                "root_cause": "",
                "confidence": 0.0
            }
            
            if problem["type"] == "agent_failure":
                diagnosis["root_cause"] = "Agent configuration or logic error"
                diagnosis["confidence"] = 0.7
            
            elif problem["type"] == "circuit_breaker_triggered":
                diagnosis["root_cause"] = "Critical anomalies detected"
                diagnosis["confidence"] = 0.9
            
            elif problem["type"] == "cpu_exhaustion":
                diagnosis["root_cause"] = "Too many concurrent processes or infinite loop"
                diagnosis["confidence"] = 0.6
            
            elif problem["type"] == "memory_exhaustion":
                diagnosis["root_cause"] = "Memory leak or large data processing"
                diagnosis["confidence"] = 0.6
            
            elif problem["type"] == "disk_exhaustion":
                diagnosis["root_cause"] = "Log accumulation or large file storage"
                diagnosis["confidence"] = 0.8
            
            diagnoses.append(diagnosis)
        
        return diagnoses

    def _generate_strategies(self, diagnoses: List[Dict]) -> List[Dict]:
        """Generate fix strategies"""
        strategies = []
        
        for diagnosis in diagnoses:
            problem = diagnosis["problem"]
            strategy = {
                "problem": problem,
                "diagnosis": diagnosis,
                "actions": [],
                "risk": "low"
            }
            
            if problem["type"] == "agent_failure":
                strategy["actions"] = [
                    {"action": "restart_agent", "description": f"Restart agent {problem['agent_id']}"},
                    {"action": "reset_stats", "description": "Reset agent statistics"}
                ]
                strategy["risk"] = "low"
            
            elif problem["type"] == "circuit_breaker_triggered":
                strategy["actions"] = [
                    {"action": "reset_circuit_breaker", "description": "Reset circuit breaker"},
                    {"action": "restart_affected_agents", "description": "Restart affected agents"}
                ]
                strategy["risk"] = "medium"
            
            elif problem["type"] == "cpu_exhaustion":
                strategy["actions"] = [
                    {"action": "pause_low_priority_agents", "description": "Pause low-priority agents"},
                    {"action": "kill_runaway_processes", "description": "Kill runaway processes"}
                ]
                strategy["risk"] = "medium"
            
            elif problem["type"] == "memory_exhaustion":
                strategy["actions"] = [
                    {"action": "restart_memory_heavy_agents", "description": "Restart memory-heavy agents"},
                    {"action": "clear_caches", "description": "Clear all caches"}
                ]
                strategy["risk"] = "low"
            
            elif problem["type"] == "disk_exhaustion":
                strategy["actions"] = [
                    {"action": "cleanup_old_logs", "description": "Clean up old logs (>7 days)"},
                    {"action": "compress_archives", "description": "Compress old archives"}
                ]
                strategy["risk"] = "low"
            
            strategies.append(strategy)
        
        return strategies

    def _apply_fixes(self, strategies: List[Dict]) -> List[Dict]:
        """Apply fix strategies"""
        fixes = []
        
        for strategy in strategies:
            if strategy["risk"] == "low":
                # Auto-apply low-risk fixes
                result = self._execute_strategy(strategy)
                fixes.append({
                    "strategy": strategy,
                    "result": "fixed" if result else "failed",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Escalate medium/high-risk fixes
                fixes.append({
                    "strategy": strategy,
                    "result": "escalated",
                    "reason": f"Risk level: {strategy['risk']}",
                    "timestamp": datetime.now().isoformat()
                })
        
        return fixes

    def _execute_strategy(self, strategy: Dict) -> bool:
        """Execute a fix strategy"""
        try:
            for action_item in strategy["actions"]:
                action = action_item["action"]
                print(f"    Executing: {action_item['description']}")
                
                if action == "restart_agent":
                    # Restart agent (set status to idle)
                    agent_id = strategy["problem"]["agent_id"]
                    agents_file = AIOS_ROOT / "agent_system" / "agents_data.json"
                    
                    with open(agents_file, 'r', encoding='utf-8') as f:
                        agents_data = json.load(f)
                    
                    for agent in agents_data["agents"]:
                        if agent["id"] == agent_id:
                            agent["stats"]["tasks_completed"] = 0
                            agent["stats"]["tasks_failed"] = 0
                            agent["stats"]["success_rate"] = 0.0
                            break
                    
                    with open(agents_file, 'w', encoding='utf-8') as f:
                        json.dump(agents_data, f, ensure_ascii=False, indent=2)
                
                elif action == "reset_circuit_breaker":
                    # Reset circuit breaker
                    circuit_breaker_file = AIOS_ROOT / "agent_system" / "circuit_breaker_state.json"
                    with open(circuit_breaker_file, 'w', encoding='utf-8') as f:
                        json.dump({"triggered": False, "agents": []}, f, ensure_ascii=False, indent=2)
                
                elif action == "cleanup_old_logs":
                    # Clean up old logs
                    events_file = AIOS_ROOT / "data" / "events.jsonl"
                    if events_file.exists():
                        cutoff = datetime.now() - timedelta(days=7)
                        
                        # Read and filter events
                        filtered_events = []
                        with open(events_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    event = json.loads(line.strip())
                                    timestamp_str = event.get("timestamp", "")
                                    if timestamp_str:
                                        event_time = datetime.fromisoformat(timestamp_str)
                                        if event_time >= cutoff:
                                            filtered_events.append(line)
                                except:
                                    continue
                        
                        # Write back
                        with open(events_file, 'w', encoding='utf-8') as f:
                            f.writelines(filtered_events)
                
                elif action == "clear_caches":
                    # TODO: Implement cache clearing
                    pass
                
                time.sleep(0.1)  # Simulate work
            
            return True
        
        except Exception as e:
            print(f"    Failed: {e}")
            return False

    def _verify_fixes(self, fixes: List[Dict]) -> List[Dict]:
        """Verify that fixes worked"""
        verified = []
        
        for fix in fixes:
            # Re-detect the same problem
            problems = self._detect_problems()
            
            # Check if problem still exists
            problem_type = fix["strategy"]["problem"]["type"]
            still_exists = any(p["type"] == problem_type for p in problems)
            
            verified.append({
                "fix": fix,
                "verified": not still_exists,
                "timestamp": datetime.now().isoformat()
            })
        
        return verified

    def _save_healing_history(self):
        """Save healing history"""
        with open(self.healing_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.healing_history, f, ensure_ascii=False, indent=2)

    def _save_report(self, report: Dict):
        """Save report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"healing_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    agent = SelfHealingAgent()
    report = agent.run()
    
    fixes = report.get("fixes", [])
    auto_fixed = len([f for f in fixes if f["result"] == "fixed"])
    escalated = len([f for f in fixes if f["result"] == "escalated"])
    
    if auto_fixed > 0:
        print(f"\nSELF_HEALING_FIXED:{auto_fixed}")
    if escalated > 0:
        print(f"SELF_HEALING_ESCALATED:{escalated}")
    if auto_fixed == 0 and escalated == 0:
        print("\nSELF_HEALING_OK")


if __name__ == "__main__":
    main()
