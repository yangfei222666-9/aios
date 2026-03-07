#!/usr/bin/env python3
"""
API 端点故障恢复监控
监控 apiport.cc.cd 的健康状态，从 502 恢复到 200 时通知
"""
import json
import time
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

# 配置
API_URL = "http://apiport.cc.cd/v1/models"
STATE_FILE = Path(__file__).parent / "api_monitor_state.json"
TELEGRAM_CHAT_ID = "7986452220"

def load_state():
    """加载监控状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "last_status": None,
        "consecutive_ok": 0,
        "last_check": None,
        "total_checks": 0,
        "recovery_notified": False
    }

def save_state(state):
    """保存监控状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def check_api():
    """检查 API 状态"""
    try:
        req = urllib.request.Request(API_URL, headers={'User-Agent': 'AIOS-Monitor/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None

def send_telegram_notification(message):
    """发送 Telegram 通知（通过 message tool）"""
    # 写入通知请求文件，由主系统处理
    notify_file = Path(__file__).parent / "api_monitor_notify.json"
    notify_data = {
        "timestamp": datetime.now().isoformat(),
        "chat_id": TELEGRAM_CHAT_ID,
        "message": message,
        "level": "critical"
    }
    with open(notify_file, 'w', encoding='utf-8') as f:
        json.dump(notify_data, f, indent=2, ensure_ascii=False)
    print(f"[NOTIFY] Notification request written: {notify_file}")

def main():
    state = load_state()
    state["total_checks"] += 1
    state["last_check"] = datetime.now().isoformat()
    
    print(f"[CHECK] API status check #{state['total_checks']}")
    print(f"   URL: {API_URL}")
    
    status = check_api()
    
    if status is None:
        print("[WARN] Network error, skipping this check")
        save_state(state)
        return
    
    print(f"   Status: {status}")
    
    # 保存之前的状态（在更新之前）
    prev_status = state["last_status"]
    
    # 检测恢复
    # 401 也算服务可用（只是需要认证）
    is_healthy = status in [200, 401]
    
    # 更新状态
    state["last_status"] = status
    
    if is_healthy:
        state["consecutive_ok"] += 1
        print(f"[OK] API healthy (status={status}, consecutive: {state['consecutive_ok']})")
        
        # 连续两次健康 且之前是故障状态
        if state["consecutive_ok"] >= 2 and not state["recovery_notified"]:
            if prev_status and prev_status not in [200, 401]:
                # 从故障恢复
                message = "🟢 报告！apiport 端点已恢复 200 OK，小九的 API 链路重新打通！"
                print(f"[RECOVERY] {message}")
                send_telegram_notification(message)
                state["recovery_notified"] = True
            elif prev_status is None:
                # 首次检查就是正常
                print("[INFO] First check, API is healthy")
                state["recovery_notified"] = True  # 避免误报
    else:
        state["consecutive_ok"] = 0
        state["recovery_notified"] = False
        print(f"[ERROR] API unhealthy: {status}")
        
        # 如果是首次发现故障
        if prev_status in [200, 401]:
            print("[WARN] API changed from healthy to unhealthy")
    
    save_state(state)
    print(f"[SAVE] State saved")

if __name__ == "__main__":
    main()
