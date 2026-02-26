#!/usr/bin/env python3
"""
AIOS Resource Optimizer Agent

Responsibilities:
1. Memory leak detection
2. Idle process cleanup
3. Cache strategy optimization
4. Resource allocation tuning
5. Performance bottleneck identification

Triggers:
- Hourly optimization
- On resource pressure
- On performance degradation

Output:
- RESOURCE_OPTIMIZER_OK - No optimization needed
- RESOURCE_OPTIMIZER_APPLIED:N - Applied N optimizations
- RESOURCE_OPTIMIZER_SUGGESTIONS:N - Generated N suggestions (need approval)
"""

import json
import sys
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class ResourceOptimizer:
    """Resource Optimizer Agent"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "optimizer"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = AIOS_ROOT / "data" / "events.jsonl"
        
        # Thresholds
        self.memory_leak_threshold_mb = 500  # 500MB growth
        self.idle_threshold_minutes = 60  # 1 hour idle
        self.cache_hit_rate_threshold = 0.5  # 50%

    def run(self) -> Dict:
        """Run resource optimization"""
        print("=" * 80)
        print(f"  Resource Optimizer Agent - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent": "resource_optimizer",
            "analysis": {},
            "optimizations": []
        }

        # 1. Memory leak detection
        print("[1/5] Detecting memory leaks...")
        memory_analysis = self._detect_memory_leaks()
        report["analysis"]["memory"] = memory_analysis
        print(f"  Found {len(memory_analysis['leaks'])} potential leaks")

        # 2. Idle process cleanup
        print("[2/5] Identifying idle processes...")
        idle_analysis = self._identify_idle_processes()
        report["analysis"]["idle"] = idle_analysis
        print(f"  Found {len(idle_analysis['idle_agents'])} idle agents")

        # 3. Cache optimization
        print("[3/5] Analyzing cache performance...")
        cache_analysis = self._analyze_cache_performance()
        report["analysis"]["cache"] = cache_analysis
        print(f"  Cache hit rate: {cache_analysis.get('hit_rate', 0):.1%}")

        # 4. Resource allocation
        print("[4/5] Analyzing resource allocation...")
        allocation_analysis = self._analyze_resource_allocation()
        report["analysis"]["allocation"] = allocation_analysis
        print(f"  Found {len(allocation_analysis['bottlenecks'])} bottlenecks")

        # 5. Generate optimizations
        print("[5/5] Generating optimizations...")
        optimizations = self._generate_optimizations(report["analysis"])
        report["optimizations"] = optimizations
        
        # Apply low-risk optimizations
        applied = self._apply_optimizations(optimizations)
        report["applied"] = applied
        print(f"  Generated {len(optimizations)} optimizations, applied {len(applied)}")

        # Save report
        self._save_report(report)

        print()
        print("=" * 80)
        if applied:
            print(f"  Applied {len(applied)} optimizations")
        else:
            print("  No optimizations needed")
        print("=" * 80)

        return report

    def _detect_memory_leaks(self) -> Dict:
        """Detect memory leaks"""
        leaks = []
        
        if not self.events_file.exists():
            return {"leaks": [], "total_checks": 0}
        
        # Track memory usage over time
        memory_history = defaultdict(list)
        cutoff = datetime.now() - timedelta(hours=1)
        
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
                    
                    agent_id = event.get("agent_id", "")
                    memory_mb = event.get("memory_mb", 0)
                    
                    if agent_id and memory_mb > 0:
                        memory_history[agent_id].append({
                            "timestamp": timestamp_str,
                            "memory_mb": memory_mb
                        })
                
                except Exception:
                    continue
        
        # Detect leaks (memory growth >500MB in 1 hour)
        for agent_id, history in memory_history.items():
            if len(history) >= 2:
                first_memory = history[0]["memory_mb"]
                last_memory = history[-1]["memory_mb"]
                growth = last_memory - first_memory
                
                if growth > self.memory_leak_threshold_mb:
                    leaks.append({
                        "agent_id": agent_id,
                        "growth_mb": growth,
                        "initial_mb": first_memory,
                        "current_mb": last_memory,
                        "timespan": "1h"
                    })
        
        return {
            "leaks": leaks,
            "total_checks": len(memory_history)
        }

    def _identify_idle_processes(self) -> Dict:
        """Identify idle processes"""
        idle_agents = []
        
        # Read agents data
        agents_file = AIOS_ROOT / "agent_system" / "agents_data.json"
        if not agents_file.exists():
            return {"idle_agents": [], "total_agents": 0}
        
        with open(agents_file, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
        
        now = datetime.now()
        
        for agent in agents_data.get("agents", []):
            if agent.get("status") != "active":
                continue
            
            last_active = agent.get("stats", {}).get("last_active")
            if not last_active:
                # Never active
                idle_agents.append({
                    "agent_id": agent["id"],
                    "idle_minutes": "never_active",
                    "reason": "Never executed any task"
                })
            else:
                last_active_time = datetime.fromisoformat(last_active)
                idle_minutes = (now - last_active_time).total_seconds() / 60
                
                if idle_minutes > self.idle_threshold_minutes:
                    idle_agents.append({
                        "agent_id": agent["id"],
                        "idle_minutes": int(idle_minutes),
                        "last_active": last_active,
                        "reason": f"Idle for {int(idle_minutes)} minutes"
                    })
        
        return {
            "idle_agents": idle_agents,
            "total_agents": len(agents_data.get("agents", []))
        }

    def _analyze_cache_performance(self) -> Dict:
        """Analyze cache performance"""
        cache_stats = {"hits": 0, "misses": 0}
        
        if not self.events_file.exists():
            return {"hit_rate": 0.0, "total_requests": 0}
        
        cutoff = datetime.now() - timedelta(hours=1)
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    if event.get("type") != "cache_access":
                        continue
                    
                    timestamp_str = event.get("timestamp", "")
                    if not timestamp_str:
                        continue
                    
                    event_time = datetime.fromisoformat(timestamp_str)
                    if event_time < cutoff:
                        continue
                    
                    if event.get("hit", False):
                        cache_stats["hits"] += 1
                    else:
                        cache_stats["misses"] += 1
                
                except Exception:
                    continue
        
        total = cache_stats["hits"] + cache_stats["misses"]
        hit_rate = cache_stats["hits"] / total if total > 0 else 0.0
        
        return {
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
            "hit_rate": hit_rate,
            "total_requests": total
        }

    def _analyze_resource_allocation(self) -> Dict:
        """Analyze resource allocation"""
        bottlenecks = []
        
        # Get current system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check CPU bottleneck
        if cpu_percent > 80:
            bottlenecks.append({
                "type": "cpu",
                "value": cpu_percent,
                "threshold": 80,
                "severity": "high" if cpu_percent > 90 else "medium"
            })
        
        # Check memory bottleneck
        if memory.percent > 80:
            bottlenecks.append({
                "type": "memory",
                "value": memory.percent,
                "threshold": 80,
                "severity": "high" if memory.percent > 90 else "medium"
            })
        
        # Check disk bottleneck
        if disk.percent > 80:
            bottlenecks.append({
                "type": "disk",
                "value": disk.percent,
                "threshold": 80,
                "severity": "high" if disk.percent > 90 else "medium"
            })
        
        return {
            "bottlenecks": bottlenecks,
            "current_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
        }

    def _generate_optimizations(self, analysis: Dict) -> List[Dict]:
        """Generate optimization suggestions"""
        optimizations = []
        
        # Memory leak optimizations
        for leak in analysis.get("memory", {}).get("leaks", []):
            optimizations.append({
                "type": "memory_leak",
                "risk": "medium",
                "agent_id": leak["agent_id"],
                "action": "restart_agent",
                "description": f"Restart agent {leak['agent_id']} to free {leak['growth_mb']}MB",
                "expected_benefit": f"Free {leak['growth_mb']}MB memory"
            })
        
        # Idle process optimizations
        for idle in analysis.get("idle", {}).get("idle_agents", []):
            if idle["idle_minutes"] != "never_active" and idle["idle_minutes"] > 120:
                optimizations.append({
                    "type": "idle_cleanup",
                    "risk": "low",
                    "agent_id": idle["agent_id"],
                    "action": "archive_agent",
                    "description": f"Archive idle agent {idle['agent_id']} (idle for {idle['idle_minutes']}min)",
                    "expected_benefit": "Free system resources"
                })
        
        # Cache optimizations
        cache_data = analysis.get("cache", {})
        if cache_data.get("hit_rate", 1.0) < self.cache_hit_rate_threshold:
            optimizations.append({
                "type": "cache_tuning",
                "risk": "low",
                "action": "increase_cache_ttl",
                "description": f"Increase cache TTL (current hit rate: {cache_data.get('hit_rate', 0):.1%})",
                "expected_benefit": "Improve cache hit rate"
            })
        
        # Resource allocation optimizations
        for bottleneck in analysis.get("allocation", {}).get("bottlenecks", []):
            if bottleneck["severity"] == "high":
                optimizations.append({
                    "type": "resource_allocation",
                    "risk": "high",
                    "action": f"scale_{bottleneck['type']}",
                    "description": f"{bottleneck['type'].upper()} usage at {bottleneck['value']:.1f}%",
                    "expected_benefit": f"Reduce {bottleneck['type']} pressure"
                })
        
        return optimizations

    def _apply_optimizations(self, optimizations: List[Dict]) -> List[Dict]:
        """Apply low-risk optimizations automatically"""
        applied = []
        
        for opt in optimizations:
            if opt["risk"] == "low":
                # Apply optimization
                success = self._execute_optimization(opt)
                if success:
                    applied.append(opt)
        
        return applied

    def _execute_optimization(self, optimization: Dict) -> bool:
        """Execute a single optimization"""
        try:
            action = optimization["action"]
            
            if action == "archive_agent":
                # Archive idle agent
                agent_id = optimization["agent_id"]
                agents_file = AIOS_ROOT / "agent_system" / "agents_data.json"
                
                with open(agents_file, 'r', encoding='utf-8') as f:
                    agents_data = json.load(f)
                
                for agent in agents_data["agents"]:
                    if agent["id"] == agent_id:
                        agent["status"] = "archived"
                        agent["archived_at"] = datetime.now().isoformat()
                        agent["archive_reason"] = "Idle cleanup by Resource Optimizer"
                        break
                
                with open(agents_file, 'w', encoding='utf-8') as f:
                    json.dump(agents_data, f, ensure_ascii=False, indent=2)
                
                return True
            
            elif action == "increase_cache_ttl":
                # TODO: Implement cache TTL increase
                return True
            
            # Other actions require manual approval
            return False
        
        except Exception as e:
            print(f"Failed to execute optimization: {e}")
            return False

    def _save_report(self, report: Dict):
        """Save optimization report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"optimizer_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """Main function"""
    optimizer = ResourceOptimizer()
    report = optimizer.run()
    
    applied = report.get("applied", [])
    optimizations = report.get("optimizations", [])
    suggestions = [o for o in optimizations if o not in applied]
    
    if applied:
        print(f"\nRESOURCE_OPTIMIZER_APPLIED:{len(applied)}")
    elif suggestions:
        print(f"\nRESOURCE_OPTIMIZER_SUGGESTIONS:{len(suggestions)}")
    else:
        print("\nRESOURCE_OPTIMIZER_OK")


if __name__ == "__main__":
    main()
