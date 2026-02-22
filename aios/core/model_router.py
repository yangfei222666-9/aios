"""
AIOS Model Router - 自动选择最优模型
根据任务复杂度自动在 sonnet/opus 之间切换
"""
import re
from typing import Literal

ModelTier = Literal["sonnet", "opus"]

# 触发 opus 的关键词（复杂任务）
OPUS_TRIGGERS = {
    # 代码相关
    "重构", "架构", "设计模式", "优化算法", "性能调优", "并发", "多线程",
    "refactor", "architecture", "design pattern", "optimize", "concurrent",
    
    # 多步骤任务
    "分析并", "先...再", "然后", "接着", "最后",
    "step by step", "multi-step",
    
    # 复杂问题
    "为什么", "原理", "深入", "详细分析", "根本原因",
    "why", "principle", "deep dive", "root cause",
    
    # 创造性任务
    "创建项目", "从零开始", "完整实现", "端到端", "完整", "项目",
    "create project", "from scratch", "full implementation", "end-to-end", "complete", "project",
    
    # 调试
    "调试", "排查", "定位问题", "找bug",
    "debug", "troubleshoot", "diagnose",
}

# 明确要求 sonnet 的关键词（简单任务）
SONNET_TRIGGERS = {
    "列出", "查看", "显示", "读取", "检查状态",
    "list", "show", "display", "read", "check status",
    "简单", "快速", "直接",
    "simple", "quick", "straightforward",
}

def route_model(message: str, context: dict = None) -> ModelTier:
    """
    根据消息内容和上下文自动选择模型
    
    Args:
        message: 用户消息
        context: 可选上下文（如最近的错误、任务历史等）
    
    Returns:
        "sonnet" 或 "opus"
    """
    msg_lower = message.lower()
    
    # 1. 明确指定模型
    if "用opus" in msg_lower or "use opus" in msg_lower:
        return "opus"
    if "用sonnet" in msg_lower or "use sonnet" in msg_lower:
        return "sonnet"
    
    # 2. 检查 sonnet 触发词（优先级高，因为用户明确要简单快速）
    if any(trigger in msg_lower for trigger in SONNET_TRIGGERS):
        return "sonnet"
    
    # 3. 检查 opus 触发词
    opus_score = sum(1 for trigger in OPUS_TRIGGERS if trigger in msg_lower)
    if opus_score >= 1:  # 只要有1个复杂任务关键词就用 opus
        return "opus"
    
    # 4. 长度判断（超长消息通常是复杂任务）
    if len(message) > 500:
        return "opus"
    
    # 5. 代码块判断（包含代码通常需要更强推理）
    if "```" in message or message.count("\n") > 10:
        return "opus"
    
    # 6. 上下文判断
    if context:
        # 如果最近有失败，用 opus 重试
        if context.get("recent_failures", 0) > 0:
            return "opus"
        
        # 如果是子任务的一部分，继承父任务的模型选择
        if context.get("parent_model"):
            return context["parent_model"]
    
    # 7. 默认 sonnet（省钱）
    return "sonnet"

def get_model_id(tier: ModelTier) -> str:
    """返回完整的模型 ID"""
    if tier == "opus":
        return "chat/claude-opus-4-6"
    else:
        return "chat/claude-sonnet-4-5-20250929"

def explain_choice(message: str, tier: ModelTier) -> str:
    """解释为什么选择这个模型（调试用）"""
    reasons = []
    msg_lower = message.lower()
    
    if tier == "opus":
        if any(t in msg_lower for t in OPUS_TRIGGERS):
            matched = [t for t in OPUS_TRIGGERS if t in msg_lower]
            reasons.append(f"复杂任务关键词: {matched[:3]}")
        if len(message) > 500:
            reasons.append(f"消息长度: {len(message)} 字符")
        if "```" in message:
            reasons.append("包含代码块")
    else:
        if any(t in msg_lower for t in SONNET_TRIGGERS):
            matched = [t for t in SONNET_TRIGGERS if t in msg_lower]
            reasons.append(f"简单任务关键词: {matched[:3]}")
        if not reasons:
            reasons.append("默认选择（省钱）")
    
    return f"{tier.upper()}: {', '.join(reasons)}"

# CLI 测试
if __name__ == "__main__":
    test_cases = [
        "列出所有文件",
        "帮我重构这段代码，优化性能",
        "为什么这个算法这么慢？深入分析一下",
        "创建一个完整的 Web 项目，包括前后端",
        "检查 AIOS 状态",
        "调试这个 bug，找出根本原因",
        "简单看一下日志",
    ]
    
    print("Model Router 测试:\n")
    for msg in test_cases:
        tier = route_model(msg)
        print(f"[{tier.upper()}] {msg}")
        print(f"  → {explain_choice(msg, tier)}\n")
