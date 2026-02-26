"""
AIOS Health Check Skill
检查 AIOS 系统健康状态
"""

import json
from pathlib import Path

def check_health():
    """检查系统健康"""
    workspace = Path(r"C:\Users\A\.openclaw\workspace\aios")
    
    issues = []
    
    # 1. 检查事件日志大小
    events_file = workspace / "data" / "events.jsonl"
    if events_file.exists():
        size_mb = events_file.stat().st_size / 1024 / 1024
        if size_mb > 10:
            issues.append({
                "type": "disk_usage",
                "severity": "warning",
                "message": f"events.jsonl 过大 ({size_mb:.1f}MB)",
                "action": "cleanup_old_events"
            })
    
    # 2. 检查 Evolution Score
    baseline_file = workspace / "learning" / "metrics_history.jsonl"
    if baseline_file.exists():
        with open(baseline_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                last_metric = json.loads(lines[-1])
                score = last_metric.get("evolution_score", 1.0)
                grade = last_metric.get("grade", "unknown")
                
                if score < 0.4:
                    issues.append({
                        "type": "performance",
                        "severity": "critical",
                        "message": f"Evolution Score 过低 ({score:.2f}, {grade})",
                        "action": "investigate_degradation"
                    })
                elif score < 0.6:
                    issues.append({
                        "type": "performance",
                        "severity": "warning",
                        "message": f"Evolution Score 偏低 ({score:.2f}, {grade})",
                        "action": "monitor_performance"
                    })
    
    # 3. 检查 Agent 状态
    agents_file = workspace / "agent_system" / "agents.jsonl"
    if agents_file.exists():
        with open(agents_file, 'r', encoding='utf-8') as f:
            agents = [json.loads(line) for line in f]
            degraded = [a for a in agents if a.get("state") == "degraded"]
            blocked = [a for a in agents if a.get("state") == "blocked"]
            
            if degraded:
                issues.append({
                    "type": "agent_health",
                    "severity": "warning",
                    "message": f"{len(degraded)} 个 Agent 处于 degraded 状态",
                    "action": "restart_degraded_agents",
                    "agents": [a.get("id") for a in degraded]
                })
            
            if blocked:
                issues.append({
                    "type": "agent_health",
                    "severity": "warning",
                    "message": f"{len(blocked)} 个 Agent 处于 blocked 状态",
                    "action": "unblock_agents",
                    "agents": [a.get("id") for a in blocked]
                })
    
    # 4. 检查磁盘空间
    import shutil
    disk_usage = shutil.disk_usage(workspace)
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    
    if disk_percent > 90:
        issues.append({
            "type": "disk_usage",
            "severity": "critical",
            "message": f"磁盘使用率过高 ({disk_percent:.1f}%)",
            "action": "cleanup_disk"
        })
    elif disk_percent > 80:
        issues.append({
            "type": "disk_usage",
            "severity": "warning",
            "message": f"磁盘使用率偏高 ({disk_percent:.1f}%)",
            "action": "monitor_disk"
        })
    
    # 返回标准格式
    return {
        "ok": len(issues) == 0,
        "result": {
            "total_issues": len(issues),
            "issues": issues,
            "disk_usage_percent": disk_percent
        },
        "evidence": [
            str(events_file) if events_file.exists() else "events.jsonl (not found)",
            str(baseline_file) if baseline_file.exists() else "metrics_history.jsonl (not found)",
            str(agents_file) if agents_file.exists() else "agents.jsonl (not found)"
        ],
        "next": ["fix_issues"] if issues else []
    }

if __name__ == "__main__":
    result = check_health()
    print(json.dumps(result, indent=2, ensure_ascii=False))
