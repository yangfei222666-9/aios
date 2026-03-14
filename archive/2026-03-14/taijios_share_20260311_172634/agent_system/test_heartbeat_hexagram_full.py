#!/usr/bin/env python3
"""
Heartbeat Hexagram Integration - Full Test
==========================================

完整测试：模拟卦象引擎可用时的输出
"""

import json
from pathlib import Path
from datetime import datetime


class MockHexagramEngine:
    """模拟卦象引擎（用于测试）"""
    
    def consult(self, context: dict, question: str) -> dict:
        """模拟卦象咨询"""
        
        if question == "system_health_check":
            # 根据指标返回不同卦象
            success_rate = context.get("success_rate", 0.0)
            api_health = context.get("api_health", 0.0)
            
            if success_rate > 0.9 and api_health > 0.9:
                return {
                    "hexagram_name": "坤卦",
                    "hexagram_bits": "000000",
                    "risk_level": "low",
                    "recommended_actions": [
                        "保持当前策略",
                        "继续积累经验",
                        "稳步推进改进"
                    ],
                    "guardrails": {
                        "triggered": False,
                        "reasons": []
                    }
                }
            elif success_rate > 0.7:
                return {
                    "hexagram_name": "既济卦",
                    "hexagram_bits": "101010",
                    "risk_level": "medium",
                    "recommended_actions": [
                        "监控关键指标",
                        "准备应急预案"
                    ],
                    "guardrails": {
                        "triggered": False,
                        "reasons": []
                    }
                }
            else:
                return {
                    "hexagram_name": "大过卦",
                    "hexagram_bits": "011110",
                    "risk_level": "high",
                    "recommended_actions": [
                        "立即降低风险",
                        "启用保守策略",
                        "人工介入评估"
                    ],
                    "guardrails": {
                        "triggered": True,
                        "reasons": [
                            "成功率低于 70%",
                            "系统健康度下降"
                        ]
                    }
                }
        
        elif question == "agent_lifecycle":
            # Agent 生命周期卦象
            tasks_completed = context.get("tasks_completed", 0)
            tasks_failed = context.get("tasks_failed", 0)
            
            if tasks_completed > 50 and tasks_failed < 5:
                return {
                    "hexagram_name": "乾卦",
                    "lifecycle_stage": "mature",
                    "keep_active": True
                }
            elif tasks_completed > 20:
                return {
                    "hexagram_name": "坤卦",
                    "lifecycle_stage": "stable",
                    "keep_active": True
                }
            else:
                return {
                    "hexagram_name": "未济卦",
                    "lifecycle_stage": "growing",
                    "keep_active": True
                }
        
        return {}


def test_full_integration():
    """完整集成测试"""
    
    print("="*60)
    print("Heartbeat Hexagram Integration - Full Test")
    print("="*60)
    
    # 场景 1: 健康系统（坤卦）
    print("\n[SCENARIO 1] Healthy System (坤卦)")
    print("-"*60)
    
    engine = MockHexagramEngine()
    result = engine.consult(
        context={
            "api_health": 0.95,
            "success_rate": 0.925,
            "queue_depth": 3,
            "evolution_score": 99.5
        },
        question="system_health_check"
    )
    
    print(f"Hexagram: {result['hexagram_name']} ({result['hexagram_bits']})")
    print(f"Risk Level: {result['risk_level']}")
    print("Recommended Actions:")
    for action in result['recommended_actions']:
        print(f"  • {action}")
    print(f"Guardrail Triggered: {result['guardrails']['triggered']}")
    
    # 场景 2: 中等风险（既济卦）
    print("\n[SCENARIO 2] Medium Risk (既济卦)")
    print("-"*60)
    
    result = engine.consult(
        context={
            "api_health": 0.80,
            "success_rate": 0.75,
            "queue_depth": 8,
            "evolution_score": 85.0
        },
        question="system_health_check"
    )
    
    print(f"Hexagram: {result['hexagram_name']} ({result['hexagram_bits']})")
    print(f"Risk Level: {result['risk_level']}")
    print("Recommended Actions:")
    for action in result['recommended_actions']:
        print(f"  • {action}")
    print(f"Guardrail Triggered: {result['guardrails']['triggered']}")
    
    # 场景 3: 高风险（大过卦）
    print("\n[SCENARIO 3] High Risk (大过卦)")
    print("-"*60)
    
    result = engine.consult(
        context={
            "api_health": 0.60,
            "success_rate": 0.55,
            "queue_depth": 15,
            "evolution_score": 70.0
        },
        question="system_health_check"
    )
    
    print(f"Hexagram: {result['hexagram_name']} ({result['hexagram_bits']})")
    print(f"Risk Level: {result['risk_level']}")
    print("Recommended Actions:")
    for action in result['recommended_actions']:
        print(f"  • {action}")
    print(f"Guardrail Triggered: {result['guardrails']['triggered']}")
    if result['guardrails']['triggered']:
        print("Guardrail Reasons:")
        for reason in result['guardrails']['reasons']:
            print(f"  • {reason}")
    
    # 场景 4: Agent 生命周期
    print("\n[SCENARIO 4] Agent Lifecycle")
    print("-"*60)
    
    agents = [
        {"name": "coder-dispatcher", "completed": 60, "failed": 3},
        {"name": "analyst-dispatcher", "completed": 30, "failed": 2},
        {"name": "monitor-dispatcher", "completed": 10, "failed": 0}
    ]
    
    for agent in agents:
        result = engine.consult(
            context={
                "tasks_completed": agent["completed"],
                "tasks_failed": agent["failed"]
            },
            question="agent_lifecycle"
        )
        
        status = "✓" if result['keep_active'] else "⚠"
        print(f"{status} {agent['name']}")
        print(f"    Hexagram: {result['hexagram_name']}")
        print(f"    Stage: {result['lifecycle_stage']}")
    
    print("\n" + "="*60)
    print("✅ Full integration test completed")
    print("="*60)


if __name__ == "__main__":
    test_full_integration()
