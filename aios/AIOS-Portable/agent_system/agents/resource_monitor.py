"""Resource Monitor - 系统资源监控"""
import psutil, json
from pathlib import Path
from datetime import datetime

class ResourceMonitor:
    def monitor(self):
        print("=" * 80)
        print("Resource Monitor - 资源监控")
        print("=" * 80)
        
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"\n💻 CPU: {cpu}%")
        print(f"🧠 内存: {mem.percent}% ({mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB)")
        print(f"💾 磁盘: {disk.percent}% ({disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB)")
        
        # 告警
        if cpu > 80 or mem.percent > 80 or disk.percent > 80:
            print(f"\n⚠️  资源使用率过高！")
            self._send_alert(cpu, mem.percent, disk.percent)
        else:
            print(f"\n✓ 资源使用正常")
        
        print(f"\n{'=' * 80}")
    
    def _send_alert(self, cpu, mem, disk):
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "warning",
            "title": "资源使用率告警",
            "body": f"CPU: {cpu}%, 内存: {mem}%, 磁盘: {disk}%",
            "sent": False
        }
        with open("alerts.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    monitor = ResourceMonitor()
    monitor.monitor()
