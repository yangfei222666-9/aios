#!/usr/bin/env python3
"""
API 监控通知处理器
读取 api_monitor_notify.json 并发送 Telegram 消息
"""
import json
from pathlib import Path

NOTIFY_FILE = Path(__file__).parent / "api_monitor_notify.json"

def process_notification():
    """处理待发送的通知"""
    if not NOTIFY_FILE.exists():
        return None
    
    try:
        with open(NOTIFY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 删除通知文件（避免重复发送）
        NOTIFY_FILE.unlink()
        
        return data
    except Exception as e:
        print(f"[ERROR] Failed to read notification file: {e}")
        return None

if __name__ == "__main__":
    notify = process_notification()
    if notify:
        print(f"[NOTIFY] Pending notification:")
        print(f"   Chat ID: {notify['chat_id']}")
        print(f"   Message: {notify['message']}")
        print(f"   Level: {notify['level']}")
    else:
        print("[OK] No pending notifications")
