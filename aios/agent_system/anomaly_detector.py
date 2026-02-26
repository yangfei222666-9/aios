#!/usr/bin/env python3
"""
AIOS Anomaly Detector Agent

Responsibilities:
1. Abnormal time activity detection (non-working hours)
2. Abnormal resource usage (CPU/memory spikes)
3. Suspicious call patterns (rapid repeated calls)
4. Behavioral anomalies (deviation from normal patterns)
5. Automatic circuit breaker

Triggers:
- Real-time monitoring (every 5 minutes)
- On resource spike
- On suspicious pattern

Output:
- ANOMALY_OK - No anomalies detected
- ANOMALY_DETECTED:N - Detected N anomalies
- ANOMALY_CRITICAL:N - Detected N critical anomalies (auto circuit break)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict, Counter

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class AnomalyDetector:
    """Anomaly Detector Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "anomaly"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"
        self.circuit_breaker_file = AIOS_ROOT / "agent_system" / "circuit_breaker_state.json"
        
        # Thresholds
        self.working_hours = (8, 23)  # 8:00 - 23:00
        self.max_calls_per_minute = 20
        self.max_cpu_percent = 90
        self.max_memory_percent = 90

    def run(self) -> Dict:
        """Run anomaly detection"""
        print("=" * 80)
        print(f"  Anomaly Detector Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "anomaly_detector",
            "detections": {},
            "anomalies": []
        }

        # 1. Time-based anomalies
        print("[1/5] Detecting time-based anomalies...")
        time_anomalies = self._detect_time_anomalies()
        report["detections"]["time"] = time_anomalies
        print(f"  Found {len(time_anomalies['anomalies'])} time anomalies")

        # 2. Resource anomalies
        print("[2/5] Detecting resource anomalies...")
        resource_anomalies = self._detect_resource_anomalies()
        report["detections"]["resource"] = resource_anomalies
        print(f"  Found {len(resource_anomalies['anomalies'])} resource anomalies")

        # 3. Call pattern anomalies
        print("[3/5] Detecting call pattern anomalies...")
        pattern_anomalies = self._detect_pattern_anomalies()
        report["detections"]["pattern"] = pattern_anomalies
        print(f"  Found {len(pattern_anomalies['anomalies'])} pattern anomalies")

        # 4. Behavioral anomalies
        print("[4/5] Detecting behavioral anomalies...")
        behavior_anomalies = self._detect_behavioral_anomalies()
        report["detections"]["behavior"] = behavior_anomalies
        print(f"  Found {len(behavior_anomalies['anomalies'])} behavioral anomalies")

        # 5. Circuit breaker check
        print("[5/5] Checking circuit breaker...")
        circuit_breaker = self._check_circuit_breaker(report["detections"])
        report["circuit_breaker"] = circuit_breaker
        print(f"  Circuit breaker: {circuit_breaker['status']}")

        # Collect all anomalies
        all_anomalies = []
        for detection in report["detections"].values():
            all_anomalies.extend(detection.get("anomalies", []))
        report["anomalies"] = all_anomalies

        # Save report
        self._save_report(report)

        print()
        print("=" * 80)
        critical = len([a for a in all_anomalies if a["severity"] == "critical"])
        warnings = len([a for a in all_anomalies if a["severity"] == "warning"])
        
        if critical > 0:
            print(f"  CRITICAL: {critical} critical anomalies detected!")
            if circuit_breaker["triggered"]:
                print(f"  Circuit breaker TRIGGERED for: {', '.join(circuit_breaker['agents'])}")
        elif warnings > 0:
            print(f"  WARNING: {warnings} anomalies detected")
        else:
            print("  OK: No anomalies detected")
        print("=" * 80)

        return report

    def _detect_time_anomalies(self) -> Dict:
        """Detect abnormal time activity"""
        anomalies = []
        
        if not self.events_file.exists():
            return {"anomalies": [], "total_events": 0}
        
        cutoff = datetime.now() - timedelta(minutes=30)
        non_working_hours_events = []
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    # Check if outside working hours
                    hour = event_time.hour
                    if hour < self.working_hours[0] or hour >= self.working_hours[1]:
                        non_working_hours_events.append({
                            "timestamp": timestamp_str,
                            "hour": hour,
                            "type": event.get("type", ""),
                            "agent_id": event.get("agent_id", "")
                        })
                
                except Exception:
                    continue
        
        # Group by agent
        by_agent = defaultdict(list)
        for event in non_working_hours_events:
            by_agent[event["agent_id"]].append(event)
        
        # Detect anomalies (>10 events in non-working hours)
        for agent_id, events in by_agent.items():
            if len(events) > 10:
                anomalies.append({
                    "type": "non_working_hours_activity",
                    "severity": "warning",
                    "agent_id": agent_id,
                    "event_count": len(events),
                    "timespan": "30min",
                    "description": f"Agent {agent_id} had {len(events)} events outside working hours"
                })
        
        return {
            "anomalies": anomalies,
            "total_events": len(non_working_hours_events)
        }

    def _detect_resource_anomalies(self) -> Dict:
        """Detect abnormal resource usage"""
        anomalies = []
        
        if not self.events_file.exists():
            return {"anomalies": [], "total_checks": 0}
        
        cutoff = datetime.now() - timedelta(minutes=10)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    if event.get("type") != "resource_usage":
                        continue
                    
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    cpu = event.get("cpu_percent", 0)
                    memory = event.get("memory_percent", 0)
                    agent_id = event.get("agent_id", "")
                    
                    # Check CPU spike
                    if cpu > self.max_cpu_percent:
                        anomalies.append({
                            "type": "cpu_spike",
                            "severity": "critical",
                            "agent_id": agent_id,
                            "value": cpu,
                            "threshold": self.max_cpu_percent,
                            "timestamp": timestamp_str,
                            "description": f"CPU usage {cpu}% exceeds threshold {self.max_cpu_percent}%"
                        })
                    
                    # Check memory spike
                    if memory > self.max_memory_percent:
                        anomalies.append({
                            "type": "memory_spike",
                            "severity": "critical",
                            "agent_id": agent_id,
                            "value": memory,
                            "threshold": self.max_memory_percent,
                            "timestamp": timestamp_str,
                            "description": f"Memory usage {memory}% exceeds threshold {self.max_memory_percent}%"
                        })
                
                except Exception:
                    continue
        
        return {
            "anomalies": anomalies,
            "total_checks": len(anomalies)
        }

    def _detect_pattern_anomalies(self) -> Dict:
        """Detect suspicious call patterns"""
        anomalies = []
        
        if not self.events_file.exists():
            return {"anomalies": [], "total_patterns": 0}
        
        cutoff = datetime.now() - timedelta(minutes=5)
        call_patterns = defaultdict(list)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    # Track calls
                    if event.get("type") in ["router_call", "tool_call", "api_call"]:
                        agent_id = event.get("agent_id", "unknown")
                        call_patterns[agent_id].append(timestamp_str)
                
                except Exception:
                    continue
        
        # Detect rapid repeated calls (>20 calls/min)
        for agent_id, timestamps in call_patterns.items():
            if len(timestamps) > self.max_calls_per_minute:
                anomalies.append({
                    "type": "rapid_repeated_calls",
                    "severity": "warning",
                    "agent_id": agent_id,
                    "call_count": len(timestamps),
                    "timespan": "5min",
                    "threshold": self.max_calls_per_minute,
                    "description": f"Agent {agent_id} made {len(timestamps)} calls in 5 minutes"
                })
        
        return {
            "anomalies": anomalies,
            "total_patterns": len(call_patterns)
        }

    def _detect_behavioral_anomalies(self) -> Dict:
        """Detect behavioral anomalies (deviation from normal)"""
        anomalies = []
        
        # TODO: Implement ML-based behavioral anomaly detection
        # For now, use simple heuristics
        
        if not self.events_file.exists():
            return {"anomalies": [], "total_checks": 0}
        
        cutoff = datetime.now() - timedelta(hours=1)
        agent_behaviors = defaultdict(lambda: {"actions": [], "errors": 0})
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    agent_id = event.get("agent_id", "")
                    if not agent_id:
                        continue
                    
                    agent_behaviors[agent_id]["actions"].append(event.get("type", ""))
                    
                    if event.get("type") in ["error", "failure"]:
                        agent_behaviors[agent_id]["errors"] += 1
                
                except Exception:
                    continue
        
        # Detect high error rate (>50%)
        for agent_id, behavior in agent_behaviors.items():
            total_actions = len(behavior["actions"])
            if total_actions >= 10:
                error_rate = behavior["errors"] / total_actions
                if error_rate > 0.5:
                    anomalies.append({
                        "type": "high_error_rate",
                        "severity": "critical",
                        "agent_id": agent_id,
                        "error_rate": error_rate,
                        "errors": behavior["errors"],
                        "total_actions": total_actions,
                        "description": f"Agent {agent_id} has {error_rate:.1%} error rate"
                    })
        
        return {
            "anomalies": anomalies,
            "total_checks": len(agent_behaviors)
        }

    def _check_circuit_breaker(self, detections: Dict) -> Dict:
        """Check if circuit breaker should be triggered"""
        triggered_agents = set()
        
        # Collect critical anomalies
        for detection in detections.values():
            for anomaly in detection.get("anomalies", []):
                if anomaly["severity"] == "critical":
                    agent_id = anomaly.get("agent_id", "")
                    if agent_id:
                        triggered_agents.add(agent_id)
        
        # Update circuit breaker state
        if triggered_agents:
            circuit_state = {
                "triggered": True,
                "agents": list(triggered_agents),
                "timestamp": datetime.now().isoformat(),
                "reason": "Critical anomalies detected"
            }
            
            with open(self.circuit_breaker_file, 'w', encoding='utf-8') as f:
                json.dump(circuit_state, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "triggered",
                "triggered": True,
                "agents": list(triggered_agents)
            }
        
        return {
            "status": "normal",
            "triggered": False,
            "agents": []
        }

    def _save_report(self, report: Dict):
        """Save anomaly report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"anomaly_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    detector = AnomalyDetector()
    report = detector.run()
    
    anomalies = report.get("anomalies", [])
    critical = len([a for a in anomalies if a["severity"] == "critical"])
    
    if critical > 0:
        print(f"\nANOMALY_CRITICAL:{critical}")
    elif anomalies:
        print(f"\nANOMALY_DETECTED:{len(anomalies)}")
    else:
        print("\nANOMALY_OK")


if __name__ == "__main__":
    main()
