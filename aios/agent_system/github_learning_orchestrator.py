#!/usr/bin/env python3
"""
GitHub Learning Orchestrator

Runs 5 GitHub learning agents and generates a comprehensive report.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent.parent
python_exe = r"C:\Program Files\Python312\python.exe"

class GitHubLearningOrchestrator:
    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "github_learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.learners = [
            {
                "name": "Architecture",
                "script": AIOS_ROOT / "agent_system" / "github_learner_architecture.py"
            },
            {
                "name": "Communication",
                "script": AIOS_ROOT / "agent_system" / "github_learner_communication.py"
            },
            {
                "name": "Lifecycle",
                "script": AIOS_ROOT / "agent_system" / "github_learner_lifecycle.py"
            },
            {
                "name": "Observability",
                "script": AIOS_ROOT / "agent_system" / "github_learner_observability.py"
            },
            {
                "name": "Testing",
                "script": AIOS_ROOT / "agent_system" / "github_learner_testing.py"
            }
        ]

    def run(self):
        print("=" * 80)
        print(f"  GitHub Learning Orchestrator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "learners": [],
            "all_recommendations": []
        }

        for i, learner in enumerate(self.learners, 1):
            print(f"[{i}/{len(self.learners)}] Running {learner['name']} Learner...")
            result = self._run_learner(learner)
            report["learners"].append(result)
            
            if result.get("recommendations"):
                report["all_recommendations"].extend(result["recommendations"])
            
            print()

        # Generate summary
        summary = self._generate_summary(report)
        report["summary"] = summary
        
        print("=" * 80)
        print(f"Total recommendations: {summary['total']}")
        print(f"High priority: {summary['high']}, Medium: {summary['medium']}, Low: {summary['low']}")
        print("=" * 80)
        
        self._save_report(report)
        return report

    def _run_learner(self, learner):
        result = {
            "name": learner["name"],
            "success": False,
            "recommendations": []
        }

        try:
            process = subprocess.run(
                [python_exe, str(learner["script"])],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            result["success"] = process.returncode == 0
            
            if result["success"]:
                # Parse latest report
                report_pattern = learner["script"].stem + "_*.json"
                report_files = sorted(self.data_dir.glob(report_pattern.replace("github_learner_", "")))
                
                if report_files:
                    with open(report_files[-1], 'r', encoding='utf-8') as f:
                        learner_report = json.load(f)
                    result["recommendations"] = learner_report.get("recommendations", [])
            
            print(f"  {'OK' if result['success'] else 'FAILED'} - {len(result['recommendations'])} recommendations")
        
        except Exception as e:
            print(f"  ERROR: {str(e)}")
        
        return result

    def _generate_summary(self, report):
        all_recommendations = report.get("all_recommendations", [])
        
        return {
            "total": len(all_recommendations),
            "high": len([r for r in all_recommendations if r["priority"] == "high"]),
            "medium": len([r for r in all_recommendations if r["priority"] == "medium"]),
            "low": len([r for r in all_recommendations if r["priority"] == "low"])
        }

    def _save_report(self, report):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"github_learning_summary_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nSummary report saved: {report_file}")


def main():
    orchestrator = GitHubLearningOrchestrator()
    report = orchestrator.run()
    
    total = report.get("summary", {}).get("total", 0)
    print(f"\nGITHUB_LEARNING_COMPLETE:{total} recommendations")


if __name__ == "__main__":
    main()
