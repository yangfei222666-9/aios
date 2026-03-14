"""
execution_guard.py - 执行前门控
职责：根据 confidence + risk_level 决定 allow / pending / blocked
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class Action:
    """操作对象（复用 ui_vision_agent 的定义）"""
    type: str
    params: Dict[str, Any]


class ExecutionGuard:
    """执行门控"""
    
    def __init__(self):
        pass
    
    def check(self, confidence: float, action: Action, task_desc: str = "") -> Dict[str, str]:
        """
        检查是否允许执行
        
        Args:
            confidence: 置信度（0.0-1.0）
            action: 操作对象
            task_desc: 任务描述（用于风险判断）
        
        Returns:
            {"decision": "allow" | "pending" | "blocked", "reason": str}
            
        注：v0.1 中 pending 专指"待人工确认"状态
        """
        # 1. 推导风险等级
        risk_level = self._infer_risk_level(action, task_desc)
        
        # 2. 决策规则
        if confidence >= 0.8 and risk_level == "low":
            return {"decision": "allow", "reason": "高置信度 + 低风险"}
        
        elif confidence >= 0.7 and risk_level in ["low", "medium"]:
            return {"decision": "pending", "reason": "中等置信度，需人工确认"}
        
        elif risk_level == "high":
            return {"decision": "blocked", "reason": "高风险操作，拒绝执行"}
        
        else:  # confidence < 0.7
            return {"decision": "blocked", "reason": f"置信度过低 ({confidence:.2f})"}
    
    def _infer_risk_level(self, action: Action, task_desc: str) -> str:
        """
        推导风险等级（v0.1 简化规则）
        
        注：第一版按 action.type + 关键词粗判
        后续会接入更细粒度风险判断（目标语义、页面上下文）
        """
        # 高风险关键词
        high_risk_keywords = ["删除", "关闭", "确认", "提交", "发送", "支付", "购买"]
        if any(kw in task_desc for kw in high_risk_keywords):
            return "high"
        
        # 按操作类型
        if action.type == "click":
            return "low"  # 普通点击
        
        elif action.type == "type":
            return "medium"  # 文本输入
        
        elif action.type == "press":
            key = action.params.get("key", "")
            if key in ["enter", "delete", "backspace"]:
                return "high"  # 回车/删除键
            return "medium"
        
        elif action.type == "scroll":
            return "low"  # 滚动
        
        else:
            return "medium"  # 未知操作类型，保守处理


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    guard = ExecutionGuard()
    
    # 测试用例
    test_cases = [
        # (confidence, action, task_desc, expected_decision)
        (0.9, Action("click", {"x": 100, "y": 200}), "点击登录按钮", "allow"),
        (0.75, Action("type", {"text": "username"}), "输入用户名", "pending"),
        (0.6, Action("click", {"x": 100, "y": 200}), "点击按钮", "blocked"),
        (0.95, Action("click", {"x": 100, "y": 200}), "点击删除按钮", "blocked"),
    ]
    
    print("=" * 60)
    print("ExecutionGuard 测试")
    print("=" * 60)
    
    for confidence, action, task_desc, expected in test_cases:
        result = guard.check(confidence, action, task_desc)
        status = "✅" if result["decision"] == expected else "❌"
        print(f"\n{status} Task: {task_desc}")
        print(f"   Confidence: {confidence}, Action: {action.type}")
        print(f"   Decision: {result['decision']} (expected: {expected})")
        print(f"   Reason: {result['reason']}")
