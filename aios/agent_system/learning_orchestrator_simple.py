#!/usr/bin/env python3
"""
AIOS Learning Orchestrator - Simplified Version

Runs 5 learning agents and generates a summary report.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class LearningOrchestrator:
    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.learners = [
            {"name": "Provider", "script": AIOS_ROOT / "agent_system" / "learner_provider.py"},
            {"name": "Playbook", "script": AIOS_ROOT / "agent_system" / "learner_playbook.py"},
            {"name": "Agent Behavior", "script": AIOS_ROOT / "agent_system" / "learner_agent_behavior.py"},
            {"name": "Error Pattern", "script": AIOS_ROOT / "agent_system" / "learner_error_pattern.py"},
            {"name": "Optimization", "script": AIOS_ROOT / "agent_system" / "learner_optimization.py"}
        ]

    def run(self):
        print("=" * 80)
        print(f"  AIOS Learning Orchestrator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "learners": [],
            "all_suggestions": []
        }

        for i, learner in enumerate(self.learners, 1):
            print(f"[{i}/{len(self.learners)}] Running {learner['name']} Learner...")
            result = self._run_learner(learner)
            report["learners"].append(result)
            
            if result.get("suggestions"):
                report["all_suggestions"].extend(result["suggestions"])
            
            print()

        summary = self._generate_summary(report)
        report["summary"] = summary
        
        print("=" * 80)
        print(f"Total suggestions: {summary['total']}")
        print(f"High priority: {summary['high']}, Medium: {summary['medium']}, Low: {summary['low']}")
        print("=" * 80)
        
        self._save_report(report)
        return report

    def _run_learner(self, learner):
        result = {
            "name": learner["name"],
            "success": False,
            "suggestions": []
        }

        try:
            process = subprocess.run(
                [sys.executable, str(learner["script"])],
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='replace'
            )
            
            result["success"] = process.returncode == 0
            
            if result["success"]:
                report_pattern = learner["script"].stem + "_*.json"
                report_files = sorted(self.data_dir.glob(report_pattern))
                
                if report_files:
                    with open(report_files[-1], 'r', encoding='utf-8') as f:
                        learner_report = json.load(f)
                    result["suggestions"] = learner_report.get("suggestions", [])
            
            print(f"  {'OK' if result['success'] else 'FAILED'} - {len(result['suggestions'])} suggestions")
        
        except Exception as e:
            print(f"  ERROR: {str(e)}")
        
        return result

    def _generate_summary(self, report):
        all_suggestions = report.get("all_suggestions", [])
        
        return {
            "total": len(all_suggestions),
            "high": len([s for s in all_suggestions if s.get("priority") == "high"]),
            "medium": len([s for s in all_suggestions if s.get("priority") == "medium"]),
            "low": len([s for s in all_suggestions if s.get("priority") == "low"])
        }

    def _save_report(self, report):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"orchestrator_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    orchestrator = LearningOrchestrator()
    report = orchestrator.run()
    
    total = report.get("summary", {}).get("total", 0)
    print(f"\nLEARNING_ORCHESTRATOR_{'SUGGESTIONS:' + str(total) if total > 0 else 'OK'}")


if __name__ == "__main__":
    main()
