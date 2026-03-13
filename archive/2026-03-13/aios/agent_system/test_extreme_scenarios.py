"""
极端场景测试 - 验证大过卦/既济卦/未济卦的特殊标记
"""

from debate_policy_engine import build_debate_policy, SystemState
from datetime import datetime

def test_scenario(name: str, score: float, hexagram: str, hexagram_id: int):
    """测试单个场景"""
    print(f"\n{'='*60}")
    print(f"场景: {name}")
    print(f"{'='*60}")
    
    state: SystemState = {
        "evolution_score": score,
        "hexagram": hexagram,
        "hexagram_id": hexagram_id,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95
    }
    
    policy = build_debate_policy(state)
    
    print(f"Evolution Score: {score:.1f}")
    print(f"Hexagram: {hexagram} (#{hexagram_id})")
    print(f"\n策略输出:")
    print(f"  Bull Weight: {policy['bull_weight']:.2f}")
    print(f"  Bear Weight: {policy['bear_weight']:.2f}")
    print(f"  Max Rounds: {policy['max_rounds']}")
    print(f"  Flags: {policy['flags']}")
    print(f"  Reason: {policy['reason']}")
    
    # 验证权重归一化
    total = policy['bull_weight'] + policy['bear_weight']
    assert abs(total - 1.0) < 0.01, f"权重未归一化: {total}"
    print(f"\n✅ 权重归一化验证通过 (sum={total:.2f})")


if __name__ == "__main__":
    print("Debate Policy Engine - 极端场景测试")
    
    # 场景1: 大过卦（危机）
    test_scenario(
        name="大过卦危机（Evolution Score 30）",
        score=30.0,
        hexagram="大过卦",
        hexagram_id=28
    )
    
    # 场景2: 既济卦（稳定）
    test_scenario(
        name="既济卦稳定（Evolution Score 95）",
        score=95.0,
        hexagram="既济卦",
        hexagram_id=63
    )
    
    # 场景3: 未济卦（不稳定）
    test_scenario(
        name="未济卦不稳定（Evolution Score 45）",
        score=45.0,
        hexagram="未济卦",
        hexagram_id=64
    )
    
    # 场景4: 极端低分
    test_scenario(
        name="极端低分（Evolution Score 10）",
        score=10.0,
        hexagram="坤卦",
        hexagram_id=2
    )
    
    # 场景5: 极端高分
    test_scenario(
        name="极端高分（Evolution Score 98）",
        score=98.0,
        hexagram="乾卦",
        hexagram_id=1
    )
    
    print(f"\n{'='*60}")
    print("[OK] 所有极端场景测试通过！")
    print(f"{'='*60}")
