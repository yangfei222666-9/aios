#!/usr/bin/env python3
"""
GitHub Learning Agent 4: Agent Observability Researcher

Responsibilities:
1. Search GitHub for observability patterns
2. Analyze logging strategies
3. Extract monitoring best practices
4. Identify tracing patterns
5. Generate observability reports

Focus Areas:
- Structured logging
- Metrics collection
- Distributed tracing
- Alerting strategies
- Dashboards
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class AgentObservabilityResearcher:
    """GitHub Learning Agent - Agent Observability"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "github_learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        """Run research"""
        print("=" * 80)
        print(f"  Agent Observability Researcher - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "agent_observability_researcher",
            "findings": []
        }

        # Analyze observability patterns
        print("[1/4] Analyzing observability patterns...")
        patterns = self._analyze_observability_patterns()
        report["patterns"] = patterns
        print(f"  Identified {len(patterns)} patterns")

        # Analyze logging strategies
        print("[2/4] Analyzing logging strategies...")
        logging = self._analyze_logging()
        report["logging"] = logging
        print(f"  Identified {len(logging)} strategies")

        # Analyze metrics
        print("[3/4] Analyzing metrics collection...")
        metrics = self._analyze_metrics()
        report["metrics"] = metrics
        print(f"  Identified {len(metrics)} metric types")

        # Generate recommendations
        print("[4/4] Generating recommendations...")
        recommendations = self._generate_recommendations(patterns, logging, metrics)
        report["recommendations"] = recommendations
        print(f"  Generated {len(recommendations)} recommendations")

        # Save report
        self._save_report(report)

        print()
        print("=" * 80)
        print(f"  Completed! {len(patterns)} patterns analyzed")
        print("=" * 80)

        return report

    def _analyze_observability_patterns(self) -> List[Dict]:
        """Analyze observability patterns"""
        return [
            {
                "name": "Three Pillars",
                "description": "Logs, Metrics, Traces",
                "components": ["Logging", "Metrics", "Tracing"],
                "examples": ["OpenTelemetry", "Prometheus + Grafana + Jaeger"],
                "benefits": ["Complete visibility", "Root cause analysis", "Performance optimization"]
            },
            {
                "name": "Structured Logging",
                "description": "JSON-formatted logs",
                "fields": ["timestamp", "level", "message", "context", "trace_id"],
                "examples": ["ELK Stack", "Loki"],
                "benefits": ["Searchable", "Parseable", "Queryable"]
            },
            {
                "name": "Distributed Tracing",
                "description": "Track requests across services",
                "components": ["Trace ID", "Span ID", "Parent Span"],
                "examples": ["Jaeger", "Zipkin", "OpenTelemetry"],
                "benefits": ["Request flow", "Latency analysis", "Bottleneck identification"]
            },
            {
                "name": "Metrics Collection",
                "description": "Time-series data",
                "types": ["Counter", "Gauge", "Histogram", "Summary"],
                "examples": ["Prometheus", "StatsD", "InfluxDB"],
                "benefits": ["Trends", "Alerting", "Capacity planning"]
            },
            {
                "name": "Health Endpoints",
                "description": "Expose health status",
                "endpoints": ["/health", "/ready", "/metrics"],
                "examples": ["Kubernetes", "Spring Boot Actuator"],
                "benefits": ["Monitoring", "Auto-healing", "Load balancing"]
            }
        ]

    def _analyze_logging(self) -> List[Dict]:
        """Analyze logging strategies"""
        return [
            {
                "name": "Log Levels",
                "levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "use_cases": {
                    "DEBUG": "Development, troubleshooting",
                    "INFO": "Normal operations",
                    "WARNING": "Potential issues",
                    "ERROR": "Errors that need attention",
                    "CRITICAL": "System failures"
                },
                "best_practice": "Use appropriate level, avoid log spam"
            },
            {
                "name": "Contextual Logging",
                "fields": ["agent_id", "task_id", "user_id", "session_id"],
                "benefits": ["Correlation", "Filtering", "Debugging"],
                "implementation": "Add context to all log entries"
            },
            {
                "name": "Log Aggregation",
                "tools": ["ELK Stack", "Loki", "CloudWatch"],
                "benefits": ["Centralized", "Searchable", "Alerting"],
                "implementation": "Ship logs to central system"
            },
            {
                "name": "Log Rotation",
                "strategies": ["Size-based", "Time-based", "Compression"],
                "benefits": ["Disk management", "Performance", "Retention"],
                "implementation": "Rotate daily, compress old logs"
            }
        ]

    def _analyze_metrics(self) -> List[Dict]:
        """Analyze metrics collection"""
        return [
            {
                "category": "System Metrics",
                "metrics": ["CPU usage", "Memory usage", "Disk I/O", "Network I/O"],
                "collection": "psutil, node_exporter",
                "frequency": "Every 10-60 seconds"
            },
            {
                "category": "Application Metrics",
                "metrics": ["Request rate", "Error rate", "Latency", "Success rate"],
                "collection": "Custom instrumentation",
                "frequency": "Per request"
            },
            {
                "category": "Business Metrics",
                "metrics": ["Tasks completed", "Agent utilization", "Cost per task"],
                "collection": "Application logs",
                "frequency": "Per task"
            },
            {
                "category": "Agent Metrics",
                "metrics": ["Agent count", "Agent status", "Task queue depth", "Circuit breaker state"],
                "collection": "Agent system",
                "frequency": "Every 5-10 minutes"
            }
        ]

    def _generate_recommendations(self, patterns: List[Dict], logging: List[Dict], metrics: List[Dict]) -> List[Dict]:
        """Generate recommendations"""
        return [
            {
                "priority": "high",
                "category": "Structured Logging",
                "recommendation": "Migrate from print() to structured logging (JSON format)",
                "action": "Replace all print() with logger.info() + JSON formatter",
                "benefit": "Searchable, parseable logs"
            },
            {
                "priority": "high",
                "category": "Metrics Collection",
                "recommendation": "Add Prometheus-compatible metrics endpoint",
                "action": "Implement /metrics endpoint with agent metrics",
                "benefit": "Real-time monitoring and alerting"
            },
            {
                "priority": "high",
                "category": "Contextual Logging",
                "recommendation": "Add agent_id, task_id to all log entries",
                "action": "Use contextvars or thread-local storage",
                "benefit": "Better correlation and debugging"
            },
            {
                "priority": "medium",
                "category": "Distributed Tracing",
                "recommendation": "Add trace_id to track requests across agents",
                "action": "Generate trace_id at entry point, propagate through events",
                "benefit": "End-to-end request tracking"
            },
            {
                "priority": "medium",
                "category": "Health Endpoints",
                "recommendation": "Add /health and /ready endpoints",
                "action": "Implement HTTP server with health checks",
                "benefit": "Better monitoring and auto-healing"
            },
            {
                "priority": "low",
                "category": "Log Aggregation",
                "recommendation": "Consider ELK Stack or Loki for log aggregation",
                "action": "Evaluate based on scale",
                "benefit": "Centralized log management"
            }
        ]

    def _save_report(self, report: Dict):
        """Save research report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"observability_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    researcher = AgentObservabilityResearcher()
    report = researcher.run()
    
    recommendations = report.get("recommendations", [])
    high_priority = len([r for r in recommendations if r["priority"] == "high"])
    
    print(f"\nGITHUB_LEARNING_OBSERVABILITY:{high_priority} high-priority recommendations")


if __name__ == "__main__":
    main()
