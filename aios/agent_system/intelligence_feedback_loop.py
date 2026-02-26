#!/usr/bin/env python3
"""
Feedback Loop Agent

Responsibilities:
1. Execute improvements/optimizations
2. Verify results (before/after comparison)
3. Learn from outcomes
4. Generate new improvements
5. Auto-rollback if worse

Feedback Cycle:
Execute → Verify → Learn → Improve → Re-execute

Metrics Tracked:
- Success rate
- Response time
- Error rate
- Resource usage
- User satisfaction

Output:
- FEEDBACK_IMPROVED:N - N improvements verified as effective
- FEEDBACK_ROLLED_BACK:N - N improvements rolled back
- FEEDBACK_OK - No feedback cycle needed
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import time

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class FeedbackLoopAgent:
    """Feedback Loop Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "feedback"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_state_file = self.data_dir / "feedback_state.json"
        
        # Load feedback state
        self.feedback_state = self._load_feedback_state()

    def run(self) -> Dict:
        """Run feedback loop"""
        print("=" * 80)
        print(f"  Feedback Loop Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "feedback_loop",
            "cycles": []
        }

        # 1. Check pending improvements
        print("[1/5] Checking pending improvements...")
        pending = self._get_pending_improvements()
        print(f"  Found {len(pending)} pending improvements")

        # 2. Execute improvements
        print("[2/5] Executing improvements...")
        executed = self._execute_improvements(pending)
        report["executed"] = executed
        print(f"  Executed {len(executed)} improvements")

        # 3. Verify results
        print("[3/5] Verifying results...")
        verified = self._verify_results(executed)
        report["verified"] = verified
        print(f"  Verified {len(verified)} improvements")

        # 4. Learn from outcomes
        print("[4/5] Learning from outcomes...")
        learned = self._learn_from_outcomes(verified)
        report["learned"] = learned
        print(f"  Learned {len(learned)} lessons")

        # 5. Generate new improvements
        print("[5/5] Generating new improvements...")
        new_improvements = self._generate_improvements(learned)
        report["new_improvements"] = new_improvements
        print(f"  Generated {len(new_improvements)} new improvements")

        # Save state
        self._save_feedback_state()
        self._save_report(report)

        print()
        print("=" * 80)
        improved = len([v for v in verified if v["result"] == "improved"])
        rolled_back = len([v for v in verified if v["result"] == "rolled_back"])
        print(f"  Completed! Improved: {improved}, Rolled back: {rolled_back}")
        print("=" * 80)

        return report

    def _load_feedback_state(self) -> Dict:
        """Load feedback state"""
        if self.feedback_state_file.exists():
            with open(self.feedback_state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "pending_improvements": [],
            "active_experiments": [],
            "completed_cycles": [],
            "lessons_learned": []
        }

    def _get_pending_improvements(self) -> List[Dict]:
        """Get pending improvements from various sources"""
        pending = []
        
        # From optimizer reports
        optimizer_dir = AIOS_ROOT / "agent_system" / "data" / "optimizer"
        if optimizer_dir.exists():
            optimizer_reports = sorted(optimizer_dir.glob("optimizer_*.json"))
            if optimizer_reports:
                with open(optimizer_reports[-1], 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                for opt in report.get("optimizations", []):
                    if opt["risk"] == "low":
                        pending.append({
                            "type": "optimization",
                            "action": opt["action"],
                            "description": opt["description"],
                            "expected_benefit": opt.get("expected_benefit", ""),
                            "source": "optimizer"
                        })
        
        # From learning reports
        learning_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        if learning_dir.exists():
            orchestrator_reports = sorted(learning_dir.glob("orchestrator_*.json"))
            if orchestrator_reports:
                with open(orchestrator_reports[-1], 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                for suggestion in report.get("all_suggestions", [])[:3]:  # Top 3
                    if suggestion.get("priority") == "high":
                        pending.append({
                            "type": "learning_suggestion",
                            "action": suggestion.get("type", ""),
                            "description": suggestion.get("description", ""),
                            "expected_benefit": "Improved system quality",
                            "source": "learning_agent"
                        })
        
        return pending[:5]  # Limit to 5 at a time

    def _execute_improvements(self, improvements: List[Dict]) -> List[Dict]:
        """Execute improvements and record baseline"""
        executed = []
        
        for improvement in improvements:
            # Record baseline metrics
            baseline = self._capture_metrics()
            
            # Execute improvement
            success = self._apply_improvement(improvement)
            
            if success:
                executed.append({
                    "improvement": improvement,
                    "baseline": baseline,
                    "executed_at": datetime.now().isoformat(),
                    "status": "active"
                })
                
                # Add to active experiments
                self.feedback_state["active_experiments"].append(executed[-1])
        
        return executed

    def _capture_metrics(self) -> Dict:
        """Capture current system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "error_rate": 0.0,
            "resource_usage": {}
        }
        
        # Calculate from recent events
        events_file = AIOS_ROOT / "data" / "events.jsonl"
        if events_file.exists():
            cutoff = datetime.now() - timedelta(hours=1)
            total = 0
            successes = 0
            
            with open(events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        timestamp_str = event.get("timestamp", "")
                        if not timestamp_str:
                            continue
                        
                        event_time = datetime.fromisoformat(timestamp_str)
                        if event_time < cutoff:
                            continue
                        
                        total += 1
                        if event.get("success", False):
                            successes += 1
                    except:
                        continue
            
            if total > 0:
                metrics["success_rate"] = successes / total
                metrics["error_rate"] = 1 - metrics["success_rate"]
        
        # Resource usage
        try:
            import psutil
            metrics["resource_usage"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent
            }
        except:
            pass
        
        return metrics

    def _apply_improvement(self, improvement: Dict) -> bool:
        """Apply an improvement"""
        try:
            action = improvement["action"]
            
            # Simulate improvement application
            # In real implementation, this would actually apply the change
            print(f"    Applying: {improvement['description']}")
            time.sleep(0.1)  # Simulate work
            
            return True
        except Exception as e:
            print(f"    Failed to apply: {e}")
            return False

    def _verify_results(self, executed: List[Dict]) -> List[Dict]:
        """Verify results of executed improvements"""
        verified = []
        
        for experiment in self.feedback_state["active_experiments"]:
            # Check if enough time has passed (at least 1 hour)
            executed_at = datetime.fromisoformat(experiment["executed_at"])
            if (datetime.now() - executed_at).total_seconds() < 3600:
                continue
            
            # Capture current metrics
            current = self._capture_metrics()
            baseline = experiment["baseline"]
            
            # Compare metrics
            improvement_score = self._calculate_improvement_score(baseline, current)
            
            if improvement_score > 0.1:  # 10% improvement
                result = "improved"
            elif improvement_score < -0.1:  # 10% degradation
                result = "rolled_back"
                self._rollback_improvement(experiment["improvement"])
            else:
                result = "neutral"
            
            verified.append({
                "experiment": experiment,
                "current_metrics": current,
                "improvement_score": improvement_score,
                "result": result,
                "verified_at": datetime.now().isoformat()
            })
            
            # Move to completed
            self.feedback_state["completed_cycles"].append(verified[-1])
            self.feedback_state["active_experiments"].remove(experiment)
        
        return verified

    def _calculate_improvement_score(self, baseline: Dict, current: Dict) -> float:
        """Calculate improvement score (-1 to 1)"""
        score = 0.0
        
        # Success rate improvement
        if baseline.get("success_rate", 0) > 0:
            success_delta = (current.get("success_rate", 0) - baseline["success_rate"]) / baseline["success_rate"]
            score += success_delta * 0.5
        
        # Error rate improvement (lower is better)
        if baseline.get("error_rate", 0) > 0:
            error_delta = (baseline["error_rate"] - current.get("error_rate", 0)) / baseline["error_rate"]
            score += error_delta * 0.3
        
        # Resource usage improvement (lower is better)
        baseline_cpu = baseline.get("resource_usage", {}).get("cpu_percent", 0)
        current_cpu = current.get("resource_usage", {}).get("cpu_percent", 0)
        if baseline_cpu > 0:
            cpu_delta = (baseline_cpu - current_cpu) / baseline_cpu
            score += cpu_delta * 0.2
        
        return score

    def _rollback_improvement(self, improvement: Dict):
        """Rollback an improvement"""
        print(f"    Rolling back: {improvement['description']}")
        # In real implementation, this would revert the change

    def _learn_from_outcomes(self, verified: List[Dict]) -> List[Dict]:
        """Learn from verified outcomes"""
        lessons = []
        
        for result in verified:
            if result["result"] == "improved":
                lessons.append({
                    "type": "success",
                    "improvement": result["experiment"]["improvement"]["description"],
                    "score": result["improvement_score"],
                    "lesson": f"Improvement '{result['experiment']['improvement']['action']}' was effective",
                    "timestamp": datetime.now().isoformat()
                })
            elif result["result"] == "rolled_back":
                lessons.append({
                    "type": "failure",
                    "improvement": result["experiment"]["improvement"]["description"],
                    "score": result["improvement_score"],
                    "lesson": f"Improvement '{result['experiment']['improvement']['action']}' degraded performance",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Add to lessons learned
        self.feedback_state["lessons_learned"].extend(lessons)
        
        return lessons

    def _generate_improvements(self, lessons: List[Dict]) -> List[Dict]:
        """Generate new improvements based on lessons"""
        new_improvements = []
        
        # Analyze successful patterns
        successful_actions = [
            lesson["improvement"]
            for lesson in self.feedback_state["lessons_learned"]
            if lesson["type"] == "success"
        ]
        
        # Generate similar improvements
        # (In real implementation, this would use ML or heuristics)
        
        return new_improvements

    def _save_feedback_state(self):
        """Save feedback state"""
        with open(self.feedback_state_file, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_state, f, ensure_ascii=False, indent=2)

    def _save_report(self, report: Dict):
        """Save report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"feedback_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    agent = FeedbackLoopAgent()
    report = agent.run()
    
    verified = report.get("verified", [])
    improved = len([v for v in verified if v["result"] == "improved"])
    rolled_back = len([v for v in verified if v["result"] == "rolled_back"])
    
    if improved > 0:
        print(f"\nFEEDBACK_IMPROVED:{improved}")
    if rolled_back > 0:
        print(f"FEEDBACK_ROLLED_BACK:{rolled_back}")
    if improved == 0 and rolled_back == 0:
        print("\nFEEDBACK_OK")


if __name__ == "__main__":
    main()
