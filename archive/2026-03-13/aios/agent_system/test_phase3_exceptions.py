"""
Phase 3 异常场景回归测试
验证降级路径 100% 覆盖
"""

import json
from debate_policy_engine import execute_debate_round, POLICY_VERSION


# ============================================================
# Mock LLM Functions
# ============================================================

def mock_llm_timeout(prompt: str) -> str:
    """模拟模型超时/拒绝连接"""
    raise TimeoutError("Connection timeout")


def mock_llm_empty(prompt: str) -> str:
    """模拟模型返回空响应"""
    return ""


def mock_llm_corrupted(prompt: str) -> str:
    """模拟模型输出幻觉/非 JSON 格式"""
    return "我是一段无法解析的废话，根本不是 JSON！"


def mock_llm_approve(prompt: str) -> str:
    """模拟模型擅自给出 approve（用于大过卦拦截测试）"""
    return json.dumps({
        "verdict": "approve",
        "confidence": 0.95,
        "reason": "模型认为可以通过"
    })


# ============================================================
# Test Cases
# ============================================================

def test_case_1_model_timeout():
    """用例 1: 模型彻底超时/拒绝连接（断网模拟）"""
    print("\n" + "=" * 60)
    print("Test Case 1: 模型超时")
    print("=" * 60)
    
    state = {"flags": {}}
    result = execute_debate_round(
        state=state,
        prompt="测试 prompt",
        llm_generate_func=mock_llm_timeout,
        role="bull"
    )
    
    # 断言：保守化降级
    assert result["verdict"] == "reject", f"Expected reject, got {result['verdict']}"
    assert result["requires_human_gate"] is True, "Expected requires_human_gate=True"
    assert result["fast_track"] is False, "Expected fast_track=False"
    assert "LLM Exception" in result["reason"], f"Expected LLM Exception in reason, got {result['reason']}"
    assert result["_audit_meta"]["policy_version"] == POLICY_VERSION
    
    print(f"✅ verdict: {result['verdict']}")
    print(f"✅ requires_human_gate: {result['requires_human_gate']}")
    print(f"✅ fast_track: {result['fast_track']}")
    print(f"✅ reason: {result['reason']}")
    print(f"✅ policy_version: {result['_audit_meta']['policy_version']}")


def test_case_2_model_corrupted():
    """用例 2: 模型输出幻觉/非 JSON 格式冲突"""
    print("\n" + "=" * 60)
    print("Test Case 2: 模型输出格式崩溃")
    print("=" * 60)
    
    state = {"flags": {}}
    result = execute_debate_round(
        state=state,
        prompt="测试 prompt",
        llm_generate_func=mock_llm_corrupted,
        role="bear"
    )
    
    # 断言：解析失败进入 except 块，安全降级为 reject + human_gate
    assert result["verdict"] == "reject", f"Expected reject, got {result['verdict']}"
    assert result["requires_human_gate"] is True, "Expected requires_human_gate=True"
    assert result["fast_track"] is False, "Expected fast_track=False"
    assert "Format Corrupted" in result["reason"], f"Expected Format Corrupted in reason, got {result['reason']}"
    
    print(f"✅ verdict: {result['verdict']}")
    print(f"✅ requires_human_gate: {result['requires_human_gate']}")
    print(f"✅ reason: {result['reason']}")


def test_case_3_daguo_override():
    """用例 3: 危机拦截优先级测试（大过卦下模型擅自给出 approve）"""
    print("\n" + "=" * 60)
    print("Test Case 3: 大过卦硬拦截（模型擅自 approve）")
    print("=" * 60)
    
    # 大过卦状态
    state_crisis = {"flags": {"expert_review": True}}
    
    result = execute_debate_round(
        state=state_crisis,
        prompt="测试 prompt",
        llm_generate_func=mock_llm_approve,
        role="expert"
    )
    
    # 断言：核心执行器强行覆写为 reject + requires_human_gate=True
    assert result["verdict"] == "reject", f"Expected reject (overridden), got {result['verdict']}"
    assert result["requires_human_gate"] is True, "Expected requires_human_gate=True (overridden)"
    assert result["fast_track"] is False, "Expected fast_track=False"
    assert "大过卦硬拦截" in result["reason"], f"Expected 大过卦硬拦截 in reason, got {result['reason']}"
    
    print(f"✅ verdict: {result['verdict']} (强制覆写)")
    print(f"✅ requires_human_gate: {result['requires_human_gate']} (强制覆写)")
    print(f"✅ fast_track: {result['fast_track']}")
    print(f"✅ reason: {result['reason']}")


def test_case_4_empty_response():
    """用例 4: 模型返回空响应"""
    print("\n" + "=" * 60)
    print("Test Case 4: 模型返回空响应")
    print("=" * 60)
    
    state = {"flags": {}}
    result = execute_debate_round(
        state=state,
        prompt="测试 prompt",
        llm_generate_func=mock_llm_empty,
        role="bull"
    )
    
    # 断言：保守化降级
    assert result["verdict"] == "reject", f"Expected reject, got {result['verdict']}"
    assert result["requires_human_gate"] is True, "Expected requires_human_gate=True"
    assert "Empty Response" in result["reason"], f"Expected Empty Response in reason, got {result['reason']}"
    
    print(f"✅ verdict: {result['verdict']}")
    print(f"✅ requires_human_gate: {result['requires_human_gate']}")
    print(f"✅ reason: {result['reason']}")


# ============================================================
# Run All Tests
# ============================================================

def run_all_tests():
    """运行所有测试用例"""
    print("\n" + "=" * 60)
    print("Phase 3 异常场景回归测试")
    print("=" * 60)
    
    try:
        test_case_1_model_timeout()
        test_case_2_model_corrupted()
        test_case_3_daguo_override()
        test_case_4_empty_response()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！降级路径 100% 覆盖")
        print("=" * 60)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    run_all_tests()
