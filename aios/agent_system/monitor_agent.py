"""
AIOS Monitor Agent
实时监控系统状态，发现异常立即告警
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta


def _read_last_jsonl_line(file_path: Path) -> dict | None:
    """高效读取 JSONL 文件最后一条有效记录，不加载整个文件。"""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return None
    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf = bytearray()
        while pos > 0:
            read_size = min(4096, pos)
            pos -= read_size
            f.seek(pos)
            chunk = f.read(read_size)
            buf[:0] = chunk
            lines = buf.decode('utf-8', errors='replace').splitlines()
            for line in reversed(lines):
                line = line.strip()
                if line:
                    try:
                        return json.loads(line)
                    except Exception:
                        continue
    return None

class MonitorAgent:
    def __init__(self):
        self.workspace = Path(r"C:\Users\A\.openclaw\workspace\aios")
        self.memory_dir = Path(r"C:\Users\A\.openclaw\workspace\memory")
        self.log_file = self.workspace / "monitor.log"
        self.alerts_file = self.workspace / "core" / "alerts.jsonl"
        
        # 确保 alerts 文件目录存在
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        try:
            print(log_entry.strip())
        except UnicodeEncodeError:
            print(log_entry.encode('ascii', 'ignore').decode('ascii').strip())
    
    def emit_alert(self, alert_type, severity, message, data=None):
        """发出告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "severity": severity,  # info, warning, critical
            "message": message,
            "data": data or {}
        }
        
        # 追加到告警文件
        with open(self.alerts_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert, ensure_ascii=False) + '\n')
        
        # 记录日志
        emoji = {"info": "ℹ️", "warning": "[WARN]", "critical": "🚨"}.get(severity, "")
        self.log(f"{emoji} [{severity.upper()}] {message}")
        
        return alert
    
    def check_evolution_score(self):
        """检查 Evolution Score"""
        self.log("检查 Evolution Score...")
        
        metrics_file = self.workspace / "learning" / "metrics_history.jsonl"
        if not metrics_file.exists():
            return None
        
        # 读取最新的 metric（流式：只读最后一行）
        last_metric = _read_last_jsonl_line(metrics_file)
        if not last_metric:
            return None
        
        score = last_metric.get("evolution_score", 1.0)
        grade = last_metric.get("grade", "unknown")
        
        # 检查阈值
        if score < 0.3:
            return self.emit_alert(
                "evolution_score",
                "critical",
                f"Evolution Score 严重偏低: {score:.2f} ({grade})",
                {"score": score, "grade": grade}
            )
        elif score < 0.5:
            return self.emit_alert(
                "evolution_score",
                "warning",
                f"Evolution Score 偏低: {score:.2f} ({grade})",
                {"score": score, "grade": grade}
            )
        else:
            self.log(f"  Evolution Score 正常: {score:.2f} ({grade})")
            return None
    
    def check_resource_usage(self):
        """检查资源使用"""
        self.log("检查资源使用...")
        
        metrics_file = self.workspace / "learning" / "metrics_history.jsonl"
        if not metrics_file.exists():
            return None
        
        # 读取最新的 metric（流式：只读最后一行）
        last_metric = _read_last_jsonl_line(metrics_file)
        if not last_metric:
            return None
        
        resource = last_metric.get("resource", {})
        
        avg_cpu = resource.get("avg_cpu_percent", 0)
        avg_memory = resource.get("avg_memory_percent", 0)
        peak_cpu = resource.get("peak_cpu_percent", 0)
        peak_memory = resource.get("peak_memory_percent", 0)
        
        alerts = []
        
        # 检查 CPU
        if peak_cpu > 90:
            alerts.append(self.emit_alert(
                "resource_usage",
                "critical",
                f"CPU 峰值过高: {peak_cpu:.1f}%",
                {"cpu": peak_cpu}
            ))
        elif peak_cpu > 80:
            alerts.append(self.emit_alert(
                "resource_usage",
                "warning",
                f"CPU 峰值偏高: {peak_cpu:.1f}%",
                {"cpu": peak_cpu}
            ))
        
        # 检查内存
        if peak_memory > 90:
            alerts.append(self.emit_alert(
                "resource_usage",
                "critical",
                f"内存峰值过高: {peak_memory:.1f}%",
                {"memory": peak_memory}
            ))
        elif peak_memory > 80:
            alerts.append(self.emit_alert(
                "resource_usage",
                "warning",
                f"内存峰值偏高: {peak_memory:.1f}%",
                {"memory": peak_memory}
            ))
        
        if not alerts:
            self.log(f"  资源使用正常: CPU {avg_cpu:.1f}%, 内存 {avg_memory:.1f}%")
        
        return alerts if alerts else None
    
    def check_disk_usage(self):
        """检查磁盘使用"""
        self.log("检查磁盘使用...")
        
        import shutil
        disk_usage = shutil.disk_usage(self.workspace)
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        if disk_percent > 90:
            return self.emit_alert(
                "disk_usage",
                "critical",
                f"磁盘使用率过高: {disk_percent:.1f}%",
                {"disk_percent": disk_percent}
            )
        elif disk_percent > 80:
            return self.emit_alert(
                "disk_usage",
                "warning",
                f"磁盘使用率偏高: {disk_percent:.1f}%",
                {"disk_percent": disk_percent}
            )
        else:
            self.log(f"  磁盘使用正常: {disk_percent:.1f}%")
            return None
    
    def check_agent_health(self):
        """检查 Agent 健康状态"""
        self.log("检查 Agent 健康...")
        
        agents_file = self.workspace / "agent_system" / "agents.jsonl"
        if not agents_file.exists():
            self.log("  没有 Agent 数据")
            return None
        
        # 读取 Agent 状态
        agents = []
        with open(agents_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    agent = json.loads(line)
                    agents.append(agent)
                except:
                    pass
        
        if not agents:
            return None
        
        # 统计状态
        degraded = [a for a in agents if a.get("state") == "degraded"]
        blocked = [a for a in agents if a.get("state") == "blocked"]
        
        alerts = []
        
        if degraded:
            alerts.append(self.emit_alert(
                "agent_health",
                "warning",
                f"{len(degraded)} 个 Agent 处于 degraded 状态",
                {"degraded_agents": [a.get("id") for a in degraded]}
            ))
        
        if blocked:
            alerts.append(self.emit_alert(
                "agent_health",
                "warning",
                f"{len(blocked)} 个 Agent 处于 blocked 状态",
                {"blocked_agents": [a.get("id") for a in blocked]}
            ))
        
        if not alerts:
            self.log(f"  Agent 健康正常: {len(agents)} 个 Agent")
        
        return alerts if alerts else None
    
    def check_event_log_size(self):
        """检查事件日志大小"""
        self.log("检查事件日志大小...")
        
        events_file = self.workspace / "data" / "events.jsonl"
        if not events_file.exists():
            return None
        
        size_mb = events_file.stat().st_size / 1024 / 1024
        
        if size_mb > 50:
            return self.emit_alert(
                "disk_usage",
                "critical",
                f"events.jsonl 过大: {size_mb:.1f}MB",
                {"file": "events.jsonl", "size_mb": size_mb}
            )
        elif size_mb > 10:
            return self.emit_alert(
                "disk_usage",
                "warning",
                f"events.jsonl 偏大: {size_mb:.1f}MB",
                {"file": "events.jsonl", "size_mb": size_mb}
            )
        else:
            self.log(f"  事件日志大小正常: {size_mb:.2f}MB")
            return None
    
    def run_monitoring(self):
        """运行监控"""
        self.log("\n" + "="*50)
        self.log("开始监控")
        self.log("="*50)
        
        alerts = []
        
        # 1. 检查 Evolution Score
        alert = self.check_evolution_score()
        if alert:
            alerts.append(alert)
        
        # 2. 检查资源使用
        alert = self.check_resource_usage()
        if alert:
            alerts.extend(alert if isinstance(alert, list) else [alert])
        
        # 3. 检查磁盘使用
        alert = self.check_disk_usage()
        if alert:
            alerts.append(alert)
        
        # 4. 检查 Agent 健康
        alert = self.check_agent_health()
        if alert:
            alerts.extend(alert if isinstance(alert, list) else [alert])
        
        # 5. 检查事件日志大小
        alert = self.check_event_log_size()
        if alert:
            alerts.append(alert)
        
        # 总结
        self.log("\n=== 监控完成 ===")
        
        if alerts:
            critical_count = len([a for a in alerts if a["severity"] == "critical"])
            warning_count = len([a for a in alerts if a["severity"] == "warning"])
            
            self.log(f"发现 {len(alerts)} 个告警:")
            self.log(f"  - Critical: {critical_count}")
            self.log(f"  - Warning: {warning_count}")
            
            return f"MONITOR_ALERT:{len(alerts)}"
        else:
            self.log("系统正常，无告警")
            return "MONITOR_OK"

if __name__ == "__main__":
    monitor = MonitorAgent()
    result = monitor.run_monitoring()
    print(f"\n输出: {result}")
