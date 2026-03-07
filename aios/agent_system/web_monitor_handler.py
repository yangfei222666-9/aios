#!/usr/bin/env python3
"""
Web Monitor Handler - 处理通知队列
读取 web_monitor_notify.json，发送 Telegram 通知
"""
import json
from pathlib import Path

NOTIFY_FILE = Path(__file__).parent / "web_monitor_notify.json"

def main():
    """处理通知队列"""
    if not NOTIFY_FILE.exists():
        print("无待发送通知")
        return
    
    # 读取通知队列
    with open(NOTIFY_FILE, 'r', encoding='utf-8') as f:
        notifications = json.load(f)
    
    if not notifications:
        print("无待发送通知")
        return
    
    print(f"待发送通知: {len(notifications)} 条")
    
    # 输出第一条通知（由 cron 脚本处理）
    first = notifications[0]
    print(f"NOTIFY:{first['message']}")
    
    # 移除已处理的通知
    notifications = notifications[1:]
    
    # 更新队列
    with open(NOTIFY_FILE, 'w', encoding='utf-8') as f:
        json.dump(notifications, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
