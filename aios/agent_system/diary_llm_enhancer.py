#!/usr/bin/env python3
"""
diary_llm_enhancer.py - LLM 增强日记提取

功能：
1. 使用 LLM 自动总结事件
2. 提取关键观点
3. 识别情绪和意图（比关键词更准确）
4. 生成结构化日记

依赖：
- OpenAI API（或本地 LLM）
- 需要配置 OPENAI_API_KEY
"""

import json
import os
from pathlib import Path
from datetime import datetime

# LLM 提示词模板
DIARY_EXTRACTION_PROMPT = """你是一个日记助手，负责从对话中提取结构化信息。

对话内容：
{conversation}

请提取以下信息（JSON格式）：
{{
  "event_summary": "事件简要总结（50字内）",
  "event_cause": "事件原因",
  "event_process": "事件过程",
  "event_result": "事件结果",
  "emotion": "核心情绪（高兴/难过/委屈/生气/倾诉/疲惫/坚定/常态）",
  "intent": "意图（求共情/陪伴 | 求建议/表决心 | 记事项/纯聊天）",
  "key_points": [
    "关键观点1",
    "关键观点2"
  ],
  "self_feeling": "自我感受",
  "others_view": "他人视角",
  "attitude_plan": "态度/规划",
  "core_opinion": "核心观点（一句话）"
}}

只返回JSON，不要其他内容。
"""

def extract_with_llm(conversation: str, model: str = "gpt-4") -> dict:
    """
    使用 LLM 提取日记信息
    
    Args:
        conversation: 完整对话文本
        model: LLM 模型名称
    
    Returns:
        结构化日记数据
    """
    try:
        # 检查 API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[WARN] OPENAI_API_KEY not set, using keyword-based extraction")
            return None
        
        # 调用 OpenAI API
        import openai
        openai.api_key = api_key
        
        prompt = DIARY_EXTRACTION_PROMPT.format(conversation=conversation)
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的日记助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # 解析响应
        result_text = response.choices[0].message.content.strip()
        
        # 提取 JSON（可能被包裹在 ```json ``` 中）
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        print(f"[ERROR] LLM extraction failed: {e}")
        return None

def enhance_diary_entry(entry: dict, conversation: str) -> dict:
    """
    使用 LLM 增强日记条目
    
    Args:
        entry: 基础日记条目（关键词提取）
        conversation: 完整对话文本
    
    Returns:
        增强后的日记条目
    """
    llm_result = extract_with_llm(conversation)
    
    if llm_result:
        # 合并 LLM 结果和基础提取
        entry.update({
            "event_cause": llm_result.get("event_cause", ""),
            "event_process": llm_result.get("event_process", ""),
            "event_result": llm_result.get("event_result", ""),
            "key_points": llm_result.get("key_points", []),
            "self_feeling": llm_result.get("self_feeling", ""),
            "others_view": llm_result.get("others_view", ""),
            "attitude_plan": llm_result.get("attitude_plan", ""),
            "core_opinion": llm_result.get("core_opinion", ""),
            "llm_enhanced": True
        })
        
        # 如果 LLM 的情绪/意图更准确，覆盖关键词提取
        if llm_result.get("emotion"):
            entry["emotion"] = llm_result["emotion"]
        if llm_result.get("intent"):
            entry["intent"] = llm_result["intent"]
    else:
        entry["llm_enhanced"] = False
    
    return entry

def generate_enhanced_diary_md(entry: dict) -> str:
    """生成增强版日记Markdown"""
    template = f"""# {entry['date']} 日记

## 📅 时间
- **日期：** {entry['date']}
- **时段：** {entry['time_period']}

## 👥 人物
{chr(10).join([f"- {p}" for p in entry['people']])}

## 📖 事件
- **原因：** {entry.get('event_cause', '（未提取）')}
- **过程：** {entry.get('event_process', '（未提取）')}
- **结果：** {entry.get('event_result', '（未提取）')}

## 💭 核心情绪
- {entry['emotion']}

## 🎯 关键观点
1. **自我感受：** {entry.get('self_feeling', '（未提取）')}
2. **他人视角：** {entry.get('others_view', '（未提取）')}
3. **态度/规划：** {entry.get('attitude_plan', '（未提取）')}
4. **核心观点：** {entry.get('core_opinion', '（未提取）')}

## 🔖 意图/结论
- {entry['intent']}

---

## 完整对话
```
{entry['full_text']}
```

---

*LLM 增强：{'✅ 已启用' if entry.get('llm_enhanced') else '❌ 未启用'}*
"""
    return template

if __name__ == "__main__":
    # 测试
    test_conversation = """
    珊瑚海: 1. 帮你优化这个模板？（调整分类、简化结构）
    小九: 好！三件事一起做，我们分步完成
    珊瑚海: 1. 集成到Heartbeat（每天自动提取对话）
    小九: 好！三个集成一起做，我们按优先级完成
    """
    
    result = extract_with_llm(test_conversation)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("LLM extraction not available (API key not set)")
