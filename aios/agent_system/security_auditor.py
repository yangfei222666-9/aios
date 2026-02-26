#!/usr/bin/env python3
"""
AIOS Security Auditor Agent

Responsibilities:
1. Permission checks (file access, tool usage)
2. Sensitive operation review (delete, modify, external calls)
3. Data access logging
4. Security risk scoring
5. Compliance verification

Triggers:
- Daily audit (4:00 AM)
- Before high-risk operations
- On-demand audit

Output:
- SECURITY_AUDIT_OK - No issues found
- SECURITY_AUDIT_WARNINGS:N - Found N warnings
- SECURITY_AUDIT_CRITICAL:N - Found N critical issues
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict, Counter

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class SecurityAuditor:
    """Security Auditor Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "security"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"
        
        # Sensitive paths
        self.sensitive_paths = [
            "C:\\Windows\\System32",
            "C:\\Program Files",
            str(Path.home() / ".ssh"),
            str(Path.home() / ".aws"),
            str(Path.home() / ".config")
        ]
        
        # High-risk operations
        self.high_risk_ops = [
            "delete", "remove", "rm", "rmdir",
            "format", "wipe", "destroy",
            "exec", "eval", "system"
        ]

    def run(self) -> Dict:
        """Run security audit"""
        print("=" * 80)
        print(f"  Security Auditor Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "security_auditor",
            "checks": {},
            "findings": []
        }

        # 1. Permission checks
        print("[1/5] Checking permissions...")
        perm_check = self._check_permissions()
        report["checks"]["permissions"] = perm_check
        print(f"  Found {len(perm_check['violations'])} violations")

        # 2. Sensitive operations review
        print("[2/5] Reviewing sensitive operations...")
        ops_check = self._review_sensitive_operations()
        report["checks"]["sensitive_operations"] = ops_check
        print(f"  Found {len(ops_check['suspicious'])} suspicious operations")

        # 3. Data access logging
        print("[3/5] Analyzing data access patterns...")
        access_check = self._analyze_data_access()
        report["checks"]["data_access"] = access_check
        print(f"  Found {len(access_check['anomalies'])} anomalies")

        # 4. Security risk scoring
        print("[4/5] Calculating security risk score...")
        risk_score = self._calculate_risk_score(report["checks"])
        report["risk_score"] = risk_score
        print(f"  Risk score: {risk_score['score']:.2f}/10 ({risk_score['level']})")

        # 5. Generate findings
        print("[5/5] Generating findings...")
        findings = self._generate_findings(report["checks"])
        report["findings"] = findings
        print(f"  Generated {len(findings)} findings")

        # Save report
        self._save_report(report)

        print()
        print("=" * 80)
        critical = len([f for f in findings if f["severity"] == "critical"])
        warnings = len([f for f in findings if f["severity"] == "warning"])
        
        if critical > 0:
            print(f"  CRITICAL: {critical} critical issues found!")
        elif warnings > 0:
            print(f"  WARNING: {warnings} warnings found")
        else:
            print("  OK: No security issues found")
        print("=" * 80)

        return report

    def _check_permissions(self) -> Dict:
        """Check permission violations"""
        violations = []
        
        if not self.events_file.exists():
            return {"violations": [], "total_checks": 0}
        
        cutoff = datetime.now() - timedelta(days=1)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Check timestamp
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    # Check file access
                    if event.get("type") == "file_access":
                        path = event.get("path", "")
                        operation = event.get("operation", "")
                        agent_id = event.get("agent_id", "")
                        
                        # Check sensitive paths
                        for sensitive_path in self.sensitive_paths:
                            if path.startswith(sensitive_path):
                                violations.append({
                                    "type": "sensitive_path_access",
                                    "path": path,
                                    "operation": operation,
                                    "agent_id": agent_id,
                                    "timestamp": timestamp_str
                                })
                
                except Exception:
                    continue
        
        return {
            "violations": violations,
            "total_checks": len(violations)
        }

    def _review_sensitive_operations(self) -> Dict:
        """Review sensitive operations"""
        suspicious = []
        
        if not self.events_file.exists():
            return {"suspicious": [], "total_operations": 0}
        
        cutoff = datetime.now() - timedelta(days=1)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Check timestamp
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    # Check operations
                    if event.get("type") == "operation":
                        operation = event.get("operation", "").lower()
                        target = event.get("target", "")
                        agent_id = event.get("agent_id", "")
                        
                        # Check high-risk operations
                        for risk_op in self.high_risk_ops:
                            if risk_op in operation:
                                suspicious.append({
                                    "type": "high_risk_operation",
                                    "operation": operation,
                                    "target": target,
                                    "agent_id": agent_id,
                                    "timestamp": timestamp_str
                                })
                
                except Exception:
                    continue
        
        return {
            "suspicious": suspicious,
            "total_operations": len(suspicious)
        }

    def _analyze_data_access(self) -> Dict:
        """Analyze data access patterns"""
        anomalies = []
        access_patterns = defaultdict(lambda: {"count": 0, "timestamps": []})
        
        if not self.events_file.exists():
            return {"anomalies": [], "total_accesses": 0}
        
        cutoff = datetime.now() - timedelta(days=1)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Check timestamp
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    # Track data access
                    if event.get("type") in ["file_access", "data_read", "data_write"]:
                        agent_id = event.get("agent_id", "unknown")
                        access_patterns[agent_id]["count"] += 1
                        access_patterns[agent_id]["timestamps"].append(timestamp_str)
                
                except Exception:
                    continue
        
        # Detect anomalies (>100 accesses in 24h)
        for agent_id, pattern in access_patterns.items():
            if pattern["count"] > 100:
                anomalies.append({
                    "type": "excessive_data_access",
                    "agent_id": agent_id,
                    "count": pattern["count"],
                    "timespan": "24h"
                })
        
        return {
            "anomalies": anomalies,
            "total_accesses": sum(p["count"] for p in access_patterns.values())
        }

    def _calculate_risk_score(self, checks: Dict) -> Dict:
        """Calculate overall security risk score (0-10)"""
        score = 0.0
        
        # Permission violations (0-3 points)
        violations = len(checks.get("permissions", {}).get("violations", []))
        score += min(violations * 0.5, 3.0)
        
        # Sensitive operations (0-4 points)
        suspicious = len(checks.get("sensitive_operations", {}).get("suspicious", []))
        score += min(suspicious * 0.8, 4.0)
        
        # Data access anomalies (0-3 points)
        anomalies = len(checks.get("data_access", {}).get("anomalies", []))
        score += min(anomalies * 1.0, 3.0)
        
        # Determine level
        if score >= 7.0:
            level = "critical"
        elif score >= 4.0:
            level = "high"
        elif score >= 2.0:
            level = "medium"
        else:
            level = "low"
        
        return {
            "score": score,
            "level": level,
            "max_score": 10.0
        }

    def _generate_findings(self, checks: Dict) -> List[Dict]:
        """Generate security findings"""
        findings = []
        
        # Permission violations
        for violation in checks.get("permissions", {}).get("violations", []):
            findings.append({
                "severity": "warning",
                "category": "permission",
                "description": f"Sensitive path access: {violation['path']}",
                "agent_id": violation["agent_id"],
                "recommendation": "Review agent permissions and restrict access to sensitive paths"
            })
        
        # Sensitive operations
        for suspicious in checks.get("sensitive_operations", {}).get("suspicious", []):
            findings.append({
                "severity": "critical",
                "category": "operation",
                "description": f"High-risk operation: {suspicious['operation']} on {suspicious['target']}",
                "agent_id": suspicious["agent_id"],
                "recommendation": "Require manual approval for high-risk operations"
            })
        
        # Data access anomalies
        for anomaly in checks.get("data_access", {}).get("anomalies", []):
            findings.append({
                "severity": "warning",
                "category": "data_access",
                "description": f"Excessive data access: {anomaly['count']} accesses in {anomaly['timespan']}",
                "agent_id": anomaly["agent_id"],
                "recommendation": "Investigate agent behavior and implement rate limiting"
            })
        
        return findings

    def _save_report(self, report: Dict):
        """Save audit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"audit_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    auditor = SecurityAuditor()
    report = auditor.run()
    
    findings = report.get("findings", [])
    critical = len([f for f in findings if f["severity"] == "critical"])
    warnings = len([f for f in findings if f["severity"] == "warning"])
    
    if critical > 0:
        print(f"\nSECURITY_AUDIT_CRITICAL:{critical}")
    elif warnings > 0:
        print(f"\nSECURITY_AUDIT_WARNINGS:{warnings}")
    else:
        print("\nSECURITY_AUDIT_OK")


if __name__ == "__main__":
    main()
