#!/usr/bin/env python3
"""
Prometheus Metrics Endpoint for AIOS

Exposes /metrics endpoint with Prometheus-compatible metrics.

Metrics:
- System metrics (CPU, memory, disk)
- Agent metrics (count by state, success rate)
- AIOS metrics (evolution score, circuit breaker)
- Task queue metrics (depth, throughput)

Usage:
    python metrics_endpoint.py
    
    # Access metrics
    curl http://localhost:9090/metrics
"""

import json
import psutil
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict

AIOS_ROOT = Path(__file__).resolve().parent.parent

class MetricsCollector:
    """Collect metrics from AIOS system"""
    
    def __init__(self):
        self.aios_root = AIOS_ROOT
    
    def collect_system_metrics(self) -> Dict:
        """Collect system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids())
        }
    
    def collect_agent_metrics(self) -> Dict:
        """Collect agent metrics"""
        agents_file = self.aios_root / "agent_system" / "agents_data.json"
        
        if not agents_file.exists():
            return {}
        
        with open(agents_file, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
        
        # Count by status
        status_counts = {}
        total_success_rate = 0
        active_agents = 0
        
        for agent in agents_data["agents"]:
            status = agent["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status == "active":
                active_agents += 1
                total_success_rate += agent["stats"].get("success_rate", 0)
        
        avg_success_rate = total_success_rate / active_agents if active_agents > 0 else 0
        
        return {
            "total_agents": agents_data["summary"]["total_agents"],
            "active_agents": agents_data["summary"]["active"],
            "archived_agents": agents_data["summary"].get("archived", 0),
            "avg_success_rate": avg_success_rate,
            "status_counts": status_counts
        }
    
    def collect_aios_metrics(self) -> Dict:
        """Collect AIOS-specific metrics"""
        metrics = {}
        
        # Circuit breaker state
        circuit_file = self.aios_root / "agent_system" / "circuit_breaker_state.json"
        if circuit_file.exists():
            with open(circuit_file, 'r', encoding='utf-8') as f:
                circuit_state = json.load(f)
            metrics["circuit_breaker_triggered"] = 1 if circuit_state.get("triggered") else 0
        
        # Evolution score (from baseline)
        baseline_file = self.aios_root / "learning" / "metrics_history.jsonl"
        if baseline_file.exists():
            # Read last line
            with open(baseline_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_metric = json.loads(lines[-1])
                    metrics["evolution_score"] = last_metric.get("evolution_score", 0)
        
        return metrics
    
    def collect_queue_metrics(self) -> Dict:
        """Collect task queue metrics"""
        queue_file = self.aios_root / "agent_system" / "data" / "queue" / "queue_state.json"
        
        if not queue_file.exists():
            return {}
        
        with open(queue_file, 'r', encoding='utf-8') as f:
            queue_state = json.load(f)
        
        return {
            "queue_depth": len(queue_state.get("queue", [])),
            "dead_letter_count": len(queue_state.get("dead_letter_queue", [])),
            "completed_count": len(queue_state.get("task_history", []))
        }
    
    def collect_all(self) -> Dict:
        """Collect all metrics"""
        return {
            "system": self.collect_system_metrics(),
            "agents": self.collect_agent_metrics(),
            "aios": self.collect_aios_metrics(),
            "queue": self.collect_queue_metrics(),
            "timestamp": datetime.now().isoformat()
        }
    
    def format_prometheus(self, metrics: Dict) -> str:
        """Format metrics in Prometheus format"""
        lines = []
        
        # System metrics
        system = metrics.get("system", {})
        lines.append(f"# HELP aios_cpu_percent CPU usage percentage")
        lines.append(f"# TYPE aios_cpu_percent gauge")
        lines.append(f"aios_cpu_percent {system.get('cpu_percent', 0)}")
        
        lines.append(f"# HELP aios_memory_percent Memory usage percentage")
        lines.append(f"# TYPE aios_memory_percent gauge")
        lines.append(f"aios_memory_percent {system.get('memory_percent', 0)}")
        
        lines.append(f"# HELP aios_disk_percent Disk usage percentage")
        lines.append(f"# TYPE aios_disk_percent gauge")
        lines.append(f"aios_disk_percent {system.get('disk_percent', 0)}")
        
        # Agent metrics
        agents = metrics.get("agents", {})
        lines.append(f"# HELP aios_agents_total Total number of agents")
        lines.append(f"# TYPE aios_agents_total gauge")
        lines.append(f"aios_agents_total {agents.get('total_agents', 0)}")
        
        lines.append(f"# HELP aios_agents_active Active agents")
        lines.append(f"# TYPE aios_agents_active gauge")
        lines.append(f"aios_agents_active {agents.get('active_agents', 0)}")
        
        lines.append(f"# HELP aios_agents_success_rate Average agent success rate")
        lines.append(f"# TYPE aios_agents_success_rate gauge")
        lines.append(f"aios_agents_success_rate {agents.get('avg_success_rate', 0)}")
        
        # AIOS metrics
        aios = metrics.get("aios", {})
        lines.append(f"# HELP aios_circuit_breaker_triggered Circuit breaker state (1=triggered)")
        lines.append(f"# TYPE aios_circuit_breaker_triggered gauge")
        lines.append(f"aios_circuit_breaker_triggered {aios.get('circuit_breaker_triggered', 0)}")
        
        lines.append(f"# HELP aios_evolution_score Evolution score")
        lines.append(f"# TYPE aios_evolution_score gauge")
        lines.append(f"aios_evolution_score {aios.get('evolution_score', 0)}")
        
        # Queue metrics
        queue = metrics.get("queue", {})
        lines.append(f"# HELP aios_queue_depth Task queue depth")
        lines.append(f"# TYPE aios_queue_depth gauge")
        lines.append(f"aios_queue_depth {queue.get('queue_depth', 0)}")
        
        lines.append(f"# HELP aios_dead_letter_count Dead letter queue count")
        lines.append(f"# TYPE aios_dead_letter_count gauge")
        lines.append(f"aios_dead_letter_count {queue.get('dead_letter_count', 0)}")
        
        return "\n".join(lines)

class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint"""
    
    collector = MetricsCollector()
    
    def do_GET(self):
        """Handle GET request"""
        if self.path == "/metrics":
            # Collect and format metrics
            metrics = self.collector.collect_all()
            prometheus_format = self.collector.format_prometheus(metrics)
            
            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(prometheus_format.encode('utf-8'))
        
        elif self.path == "/health":
            # Health check
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_server(port: int = 9090):
    """Start metrics server"""
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    print(f"Metrics server started on http://0.0.0.0:{port}")
    print(f"Access metrics: http://localhost:{port}/metrics")
    print(f"Health check: http://localhost:{port}/health")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    # Demo: collect and print metrics
    print("=" * 80)
    print("  Metrics Endpoint - Demo")
    print("=" * 80)
    print()
    
    collector = MetricsCollector()
    metrics = collector.collect_all()
    
    print("Collected metrics:")
    print(json.dumps(metrics, indent=2))
    print()
    
    print("Prometheus format:")
    print(collector.format_prometheus(metrics))
    print()
    
    print("=" * 80)
    print("To start server: python metrics_endpoint.py --serve")
    print("=" * 80)
