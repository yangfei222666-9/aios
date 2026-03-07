#!/usr/bin/env python3
"""
telegram_diary_bot.py - Telegram 实时日记记录

功能：
1. 监听 Telegram 消息
2. 实时提取情绪和意图
3. 自动保存到 memory/YYYY-MM-DD.md
4. 支持手动触发（/diary 命令）

使用方式：
1. 后台运行：python telegram_diary_bot.py &
2. 手动触发：发送 /diary 到 Telegram
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from diary_extractor import extract_diary_entry, save_diary, detect_emotion, detect_intent

# Telegram 消息缓冲区（存储最近的消息）
message_buffer = []
MAX_BUFFER_SIZE = 50

def on_telegram_message(message: dict):
    """
    处理 Telegram 消息
    
    Args:
        message: {
            "message_id": 18356,
            "from": {"id": 7986452220, "username": "shh7799"},
            "text": "...",
            "date": 1709740680
        }
    """
    global message_buffer
    
    # 添加到缓冲区
    message_buffer.append({
        "time": datetime.fromtimestamp(message["date"]).strftime("%H:%M"),
        "user": message["from"].get("username", "Unknown"),
        "text": message.get("text", "")
    })
    
    # 保持缓冲区大小
    if len(message_buffer) > MAX_BUFFER_SIZE:
        message_buffer.pop(0)
    
    # 检测情绪和意图（实时反馈）
    text = message.get("text", "")
    if text:
        emotion = detect_emotion(text)
        intent = detect_intent(text)
        
        # 如果检测到强烈情绪，实时记录
        if emotion != "常态":
            print(f"[EMOTION] {emotion} detected: {text[:50]}...")
            # 可以选择立即保存或等待批量保存

def trigger_diary_save():
    """手动触发日记保存（/diary 命令）"""
    global message_buffer
    
    if not message_buffer:
        return "今天还没有对话记录"
    
    # 提取日记条目
    entry = extract_diary_entry(message_buffer)
    if entry:
        save_diary(entry)
        return f"✅ 日记已保存：{entry['date']}"
    else:
        return "❌ 提取失败"

def auto_save_at_midnight():
    """每天23:59自动保存"""
    global message_buffer
    
    if message_buffer:
        entry = extract_diary_entry(message_buffer)
        if entry:
            save_diary(entry)
            print(f"[AUTO] Diary saved: {entry['date']}")
            message_buffer.clear()

if __name__ == "__main__":
    print("🤖 Telegram Diary Bot started")
    print("   Listening for messages...")
    print("   Send /diary to manually save")
    
    # TODO: 实际实现时需要连接 Telegram Bot API
    # 这里只是框架代码
    
    # 示例：模拟接收消息
    test_message = {
        "message_id": 18356,
        "from": {"id": 7986452220, "username": "shh7799"},
        "text": "1. 集成到Heartbeat（每天自动提取对话）",
        "date": int(datetime.now().timestamp())
    }
    
    on_telegram_message(test_message)
    print(f"[TEST] Message processed: {test_message['text'][:50]}...")
