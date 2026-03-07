#!/usr/bin/env python3
"""
diary_extractor.py - 从对话中自动提取日记结构

功能：
1. 从 Telegram 消息中提取关键信息
2. 自动填充日记模板
3. 保存到 memory/YYYY-MM-DD.md
4. 集成到 Heartbeat（每天23:00自动提取）
"""

import json
import re
from datetime import datetime
from pathlib import Path

# 情绪关键词映射
EMOTION_KEYWORDS = {
    "高兴": ["开心", "高兴", "哈哈", "😊", "🎉", "太好了", "完美", "成功"],
    "难过": ["难过", "伤心", "😢", "失望", "遗憾"],
    "委屈": ["委屈", "不公平", "😔"],
    "生气": ["生气", "愤怒", "😠", "烦", "讨厌"],
    "倾诉": ["想说", "倾诉", "💬", "聊聊", "听我说"],
    "疲惫": ["累", "疲惫", "😴", "困", "休息"],
    "坚定": ["坚定", "决心", "💪", "一定", "必须", "立刻"],
    "常态": []  # 默认
}

# 意图关键词映射
INTENT_KEYWORDS = {
    "求共情/陪伴": ["理解我", "陪我", "听我说", "感觉", "心情"],
    "求建议/表决心": ["怎么办", "建议", "我要", "我决定", "帮我", "优化"],
    "记事项/纯聊天": ["记一下", "提醒", "聊天", "讨论", "看看"]
}

def extract_diary_from_session() -> dict:
    """
    从当前会话历史中提取今天的对话
    
    Returns:
        {
            "date": "2026-03-06",
            "time_period": "晚上",
            "people": ["我", "小九"],
            "event": {...},
            "emotion": "坚定",
            "intent": "求建议",
            "conversations": [...]
        }
    """
    # 读取会话日志（假设在 workspace/.openclaw/sessions/main/）
    # 实际实现时需要调用 OpenClaw 的 sessions_history API
    
    # 临时实现：从 memory/YYYY-MM-DD.md 读取（如果已存在）
    today = datetime.now().strftime("%Y-%m-%d")
    memory_dir = Path(__file__).parent.parent / "memory"
    today_file = memory_dir / f"{today}.md"
    
    if today_file.exists():
        # 文件已存在，不重复提取
        return None
    
    # TODO: 实际实现时调用 sessions_history 获取今天的消息
    # 这里返回一个示例结构
    return {
        "date": today,
        "time_period": "晚上",
        "people": ["我", "小九"],
        "event_summary": "今天的对话（自动提取）",
        "emotion": "常态",
        "intent": "纯聊天",
        "full_text": "（今天的完整对话内容）"
    }

def detect_emotion(text: str) -> str:
    """检测文本中的情绪"""
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return emotion
    return "常态"

def detect_intent(text: str) -> str:
    """检测文本中的意图"""
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return intent
    return "纯聊天"

def extract_diary_entry(messages: list) -> dict:
    """
    从消息列表中提取日记条目
    
    Args:
        messages: [{"time": "22:55", "user": "珊瑚海", "text": "..."}]
    
    Returns:
        {
            "date": "2026-03-06",
            "time_period": "晚上",
            "people": ["我", "小九"],
            "event": {...},
            "emotion": "坚定",
            "intent": "求建议"
        }
    """
    if not messages:
        return None
    
    # 提取时间
    first_msg = messages[0]
    time_str = first_msg.get("time", "")
    hour = int(time_str.split(":")[0]) if ":" in time_str else 12
    
    time_period = "深夜"
    if 6 <= hour < 12:
        time_period = "早晨"
    elif 12 <= hour < 14:
        time_period = "中午"
    elif 14 <= hour < 18:
        time_period = "下午"
    elif 18 <= hour < 23:
        time_period = "晚上"
    
    # 提取人物
    people = set()
    for msg in messages:
        user = msg.get("user", "")
        if "珊瑚海" in user:
            people.add("我")
        elif "小九" in user or "Kiro" in user:
            people.add("小九")
    
    # 合并所有文本
    full_text = " ".join([msg.get("text", "") for msg in messages])
    
    # 检测情绪和意图
    emotion = detect_emotion(full_text)
    intent = detect_intent(full_text)
    
    # 提取事件（简化版，实际可以用LLM）
    event_summary = full_text[:100] + "..." if len(full_text) > 100 else full_text
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time_period": time_period,
        "people": list(people),
        "event_summary": event_summary,
        "emotion": emotion,
        "intent": intent,
        "full_text": full_text
    }

def generate_diary_md(entry: dict) -> str:
    """生成日记Markdown"""
    template = f"""# {entry['date']} 日记

## 📅 时间
- **日期：** {entry['date']}
- **时段：** {entry['time_period']}

## 👥 人物
{chr(10).join([f"- {p}" for p in entry['people']])}

## 📖 事件
{entry['event_summary']}

## 💭 核心情绪
- {entry['emotion']}

## 🔖 意图/结论
- {entry['intent']}

---

## 完整对话
```
{entry['full_text']}
```
"""
    return template

def save_diary(entry: dict, output_dir: Path = None):
    """保存日记到文件（支持 LLM 增强）"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "memory"
    
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{entry['date']}.md"
    
    # 尝试 LLM 增强
    try:
        from diary_llm_enhancer import enhance_diary_entry, generate_enhanced_diary_md
        entry = enhance_diary_entry(entry, entry.get('full_text', ''))
        content = generate_enhanced_diary_md(entry)
    except Exception as e:
        print(f"[WARN] LLM enhancement failed: {e}, using basic template")
        content = generate_diary_md(entry)
    
    # 如果文件已存在，追加而不是覆盖
    mode = "a" if output_file.exists() else "w"
    
    with open(output_file, mode, encoding="utf-8") as f:
        if mode == "a":
            f.write("\n\n---\n\n")
        f.write(content)
    
    print(f"[OK] Diary saved: {output_file}")
    return output_file

if __name__ == "__main__":
    # 测试
    test_messages = [
        {
            "time": "22:55",
            "user": "珊瑚海",
            "text": "1. 帮你优化这个模板？（调整分类、简化结构）"
        },
        {
            "time": "22:56",
            "user": "小九",
            "text": "好！三件事一起做，我们分步完成"
        }
    ]
    
    entry = extract_diary_entry(test_messages)
    if entry:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        save_diary(entry)
