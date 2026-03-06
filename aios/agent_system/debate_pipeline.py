"""
Debate Pipeline - Phase 3 完整实现
Bull vs Bear 辩论 + 64卦调解 + 异常处理

核心流程：
1. 检查大过卦硬门控（高风险任务强制人工审批）
2. Bull 辩手生成支持论据
3. Bear 辩手识别风险点
4. 64卦调解融合双方观点
5. 生成最终决策（approve/reject/defer）
"""

import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from phase3_types import GenerateRequest, GenerateResponse, DecisionResult
from debate_policy_engine import get_system_state, build_debate_policy, record_decision_audit
from debate_vote_selector import select_mode as _select_debate_vote_mode


def run_debate_pipeline(
    task_text: str,
    risk_level: str = "medium",
    provider = None,
    force_hexagram: Optional[str] = None,
    force_evolution_score: Optional[float] = None,
    task_id: Optional[str] = None,
    mode_hint: str = "auto",
) -> DecisionResult:
    """
    执行完整的 Bull vs Bear 辩论流程
    
    Args:
        task_text: 任务描述
        risk_level: 风险等级（low/medium/high）
        provider: LLM Provider（需实现 generate(GenerateRequest) -> GenerateResponse）
        force_hexagram: 强制卦象（测试用）
        force_evolution_score: 强制 Evolution Score（测试用）
        task_id: 任务 ID（可选）
    
    Returns:
        DecisionResult: 决策结果
    """
    
    # 1. 获取系统状态
    state = get_system_state()
    if force_hexagram:
        state["hexagram"] = force_hexagram
        state["hexagram_id"] = _parse_hexagram_id(force_hexagram)
    if force_evolution_score is not None:
        state["evolution_score"] = force_evolution_score
    
    # 2. 生成辩论策略
    policy = build_debate_policy(state)
    policy["task_risk_level"] = risk_level
    
    # 3. 大过卦硬门控（高风险任务强制人工审批）
    if "大过卦" in state["hexagram"] and risk_level == "high":
        audit_id = record_decision_audit(
            task_id=task_id or "unknown",
            system_state=state,
            debate_policy=policy,
            debate_result={"crisis_gate": True},
            final_decision="defer"
        )
        
        return DecisionResult(
            verdict="defer",
            reason="大过卦 + 高风险任务 → 强制人工审批",
            rounds_used=0,
            early_exit=True,
            confidence=0.0,
            requires_human_gate=True,
            audit_id=audit_id,
            selected_mode="",
            mode_reason="大过卦硬门控，未执行模式选择",
            uncertainty_score=0.0,
            convergence_score=0.0,
        )
    
    # 4. 检查 Provider
    if provider is None:
        return DecisionResult(
            verdict="defer",
            reason="No LLM provider configured",
            rounds_used=0,
            early_exit=True,
            confidence=0.0,
            requires_human_gate=True,
            audit_id=""
        )
    
    # 5. Debate vs Vote 动态模式选择
    signals = []  # 从 task_text 提取关键词作为信号
    _selector_result = _select_debate_vote_mode(
        signals=signals,
        market_state=risk_level,
        mode_hint=mode_hint,
    )
    selected_mode = _selector_result.mode
    mode_reason = _selector_result.reason
    uncertainty_score = _selector_result.uncertainty_score
    convergence_score = _selector_result.convergence_score
    
    # 5. 执行辩论
    max_rounds = policy["max_rounds"]
    bull_weight = policy["bull_weight"]
    bear_weight = policy["bear_weight"]
    
    bull_args = []
    bear_args = []
    
    for round_num in range(1, max_rounds + 1):
        # Bull 辩手
        bull_req = GenerateRequest(
            role="bull",
            prompt=f"任务：{task_text}\n风险等级：{risk_level}\n请生成支持论据（简短，1-2句）",
            context={"round": round_num, "task": task_text},
            temperature=0.3,
            max_tokens=256,
            trace_id=f"bull-r{round_num}"
        )
        
        try:
            bull_resp = provider.generate(bull_req)
        except Exception as e:
            # Bull 异常 → defer
            return _fallback_defer(f"Bull 辩手异常: {type(e).__name__}", round_num)
        
        if not bull_resp.ok or not bull_resp.text.strip():
            # Bull 失败 → defer
            return _fallback_defer("Bull 辩手响应失败", round_num)
        
        bull_args.append(bull_resp.text.strip())
        
        # Bear 辩手
        bear_req = GenerateRequest(
            role="bear",
            prompt=f"任务：{task_text}\n风险等级：{risk_level}\nBull 论据：{bull_resp.text}\n请识别风险点（简短，1-2句）",
            context={"round": round_num, "task": task_text, "bull_arg": bull_resp.text},
            temperature=0.3,
            max_tokens=256,
            trace_id=f"bear-r{round_num}"
        )
        
        try:
            bear_resp = provider.generate(bear_req)
        except Exception as e:
            # Bear 异常 → defer
            return _fallback_defer(f"Bear 辩手异常: {type(e).__name__}", round_num)
        
        if not bear_resp.ok or not bear_resp.text.strip():
            # Bear 失败 → defer
            return _fallback_defer("Bear 辩手响应失败", round_num)
        
        bear_args.append(bear_resp.text.strip())
        
        # 检查冲突（Bull approve vs Bear reject）
        if _is_conflicting(bull_resp.text, bear_resp.text):
            # 冲突 → 升级到人工
            return DecisionResult(
                verdict="defer",
                reason=f"Bull vs Bear 冲突（轮次 {round_num}）→ 升级人工",
                rounds_used=round_num,
                early_exit=True,
                confidence=0.0,
                requires_human_gate=True,
                audit_id=_generate_audit_id(task_text)
            )
    
    # 6. 64卦调解
    judge_req = GenerateRequest(
        role="judge",
        prompt=f"任务：{task_text}\n卦象：{state['hexagram']}\nBull 论据：{'; '.join(bull_args)}\nBear 风险：{'; '.join(bear_args)}\n请融合双方观点，给出最终决策（approve/reject/defer）",
        context={"hexagram": state["hexagram"], "bull": bull_args, "bear": bear_args},
        temperature=0.2,
        max_tokens=512,
        trace_id="judge-final"
    )
    judge_resp = provider.generate(judge_req)
    
    if not judge_resp.ok or not judge_resp.text.strip():
        return _fallback_defer("Judge 调解失败", max_rounds)
    
    # 7. 解析决策
    verdict = _parse_verdict(judge_resp.text)
    confidence = bull_weight if verdict == "approve" else bear_weight
    
    audit_id = record_decision_audit(
        task_id=task_id or "unknown",
        system_state=state,
        debate_policy=policy,
        debate_result={
            "bull_args": bull_args,
            "bear_args": bear_args,
            "judge_decision": judge_resp.text
        },
        final_decision=verdict
    )
    
    return DecisionResult(
        verdict=verdict,
        reason=judge_resp.text[:200],
        rounds_used=max_rounds,
        early_exit=False,
        confidence=confidence,
        requires_human_gate=(verdict == "defer"),
        audit_id=audit_id,
        selected_mode=selected_mode,
        mode_reason=mode_reason,
        uncertainty_score=uncertainty_score,
        convergence_score=convergence_score,
    )


# ============================================================
# 辅助函数
# ============================================================

def _parse_hexagram_id(hexagram_str: str) -> int:
    """从卦象字符串解析卦序号（如 "大过卦 (#28)" → 28）"""
    import re
    match = re.search(r"#(\d+)", hexagram_str)
    if match:
        return int(match.group(1))
    
    # 默认映射
    hexagram_map = {
        "坤卦": 2,
        "乾卦": 1,
        "大过卦": 28,
        "既济卦": 63,
        "未济卦": 64
    }
    for name, id in hexagram_map.items():
        if name in hexagram_str:
            return id
    return 2  # 默认坤卦


def _generate_audit_id(task_text: str) -> str:
    """生成审计 ID（时间戳 + 任务哈希）"""
    import hashlib
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    task_hash = hashlib.md5(task_text.encode()).hexdigest()[:8]
    return f"audit-{timestamp}-{task_hash}"


def _fallback_defer(reason: str, rounds_used: int) -> DecisionResult:
    """异常降级 → defer"""
    return DecisionResult(
        verdict="defer",
        reason=reason,
        rounds_used=rounds_used,
        early_exit=True,
        confidence=0.0,
        requires_human_gate=True,
        audit_id=""
    )


def _is_conflicting(bull_text: str, bear_text: str) -> bool:
    """检查 Bull vs Bear 是否冲突"""
    bull_lower = bull_text.lower()
    bear_lower = bear_text.lower()
    
    # Bull approve + Bear reject → 冲突
    bull_approve = any(kw in bull_lower for kw in ["approve", "safe", "低风险", "可以"])
    bear_reject = any(kw in bear_lower for kw in ["reject", "high risk", "高风险", "不建议"])
    
    return bull_approve and bear_reject


def _parse_verdict(judge_text: str) -> str:
    """从 Judge 文本解析决策（approve/reject/defer）"""
    text_lower = judge_text.lower()
    
    if "approve" in text_lower or "批准" in text_lower:
        return "approve"
    elif "reject" in text_lower or "拒绝" in text_lower:
        return "reject"
    else:
        return "defer"
