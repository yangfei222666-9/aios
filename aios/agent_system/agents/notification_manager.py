"""Notification Manager Agent - 统一通知管理"""
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class NotificationManager:
    def __init__(self):
        self.alerts_file = Path("alerts.jsonl")
        self.sent_log = Path("data/notifications/sent_log.jsonl")
        
    def manage(self):
        print("=" * 80)
        print("Notification Manager - 通知管理")
        print("=" * 80)
        
        # 1. 收集所有告警
        alerts = self._collect_alerts()
        print(f"\n📬 收集到 {len(alerts)} 条告警")
        
        # 2. 去重
        unique = self._deduplicate(alerts)
        print(f"✨ 去重后 {len(unique)} 条")
        
        # 3. 按优先级分组
        grouped = self._group_by_priority(unique)
        
        # 4. 发送
        sent = self._send_notifications(grouped)
        print(f"✓ 已发送 {sent} 条通知")
        
        print(f"\n{'=' * 80}")
    
    def _collect_alerts(self):
        if not self.alerts_file.exists():
            return []
        alerts = []
        with open(self.alerts_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    alert = json.loads(line)
                    if not alert.get("sent"):
                        alerts.append(alert)
        return alerts
    
    def _deduplicate(self, alerts):
        seen = set()
        unique = []
        for alert in alerts:
            key = alert.get("title", "") + alert.get("body", "")
            if key not in seen:
                seen.add(key)
                unique.append(alert)
        return unique
    
    def _group_by_priority(self, alerts):
        grouped = defaultdict(list)
        for alert in alerts:
            level = alert.get("level", "info")
            grouped[level].append(alert)
        return dict(grouped)
    
    def _send_notifications(self, grouped):
        sent = 0
        for level in ["critical", "warning", "info"]:
            if level in grouped:
                for alert in grouped[level]:
                    print(f"  📤 [{level.upper()}] {alert.get('title')}")
                    alert["sent"] = True
                    sent += 1
        
        # 更新 alerts.jsonl
        if self.alerts_file.exists():
            alerts = []
            with open(self.alerts_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        alerts.append(json.loads(line))
            
            with open(self.alerts_file, "w", encoding="utf-8") as f:
                for alert in alerts:
                    f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        
        return sent

if __name__ == "__main__":
    manager = NotificationManager()
    manager.manage()
