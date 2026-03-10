#!/usr/bin/env python3
"""
Hexagram Engine - 卦象引擎核心

完整流程：
1. 收集指标
2. 计算六爻
3. 判断卦象
4. 检测变爻
5. 应用兜底规则
6. 输出解释对象

Author: 珊瑚海 + 小九
Date: 2026-03-07
Version: 2.0
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import json

from hexagram_lines import calculate_six_lines, LineScore
from hexagram_mapping import map_binary_to_hexagram, HexagramInfo, RiskLevel
from hexagram_guardrails import apply_guardrails

@dataclass
class HexagramResult:
    """卦象结果（完整解释对象）"""
    # 全局卦象
    global_hexagram_name: str  # 全局卦名
    global_hexagram_bits: str  # 6-bit 二进制（自下而上）
    global_risk_level: str  # 全局风险等级
    global_recommended_actions: List[str]  # 全局推荐动作
    
    # 六爻详情
    line_scores: Dict[str, float]  # 六爻评分
    changing_lines: List[int]  # 变爻（1-6）
    dominant_factors: List[str]  # 主导因素
    
    # 兜底规则
    guardrail_triggered: bool  # 是否触发兜底
    guardrail_reasons: List[str]  # 触发原因
    
    # 其他
    explanation: str  # 详细解释
    confidence: float  # 整体置信度
    timestamp: float  # 时间戳

# ============================================================
# 兜底规则层（已迁移到 hexagram_guardrails.py）
# ============================================================
# 保留此注释以标记历史位置

# ============================================================
# 主引擎
# ============================================================

def calculate_hexagram(metrics: Dict[str, float], 
                      previous_binary: str = None) -> HexagramResult:
    """
    计算卦象（完整流程）
    
    Args:
        metrics: 系统指标
        previous_binary: 上一次的卦象（用于检测变爻）
    
    Returns:
        HexagramResult 对象
    """
    import time
    
    # Step 1: 计算六爻
    lines = calculate_six_lines(metrics)
    
    # Step 2: 构造 6-bit 二进制（自下而上）
    binary = "".join([
        str(lines["line_1_infra"].state),
        str(lines["line_2_execution"].state),
        str(lines["line_3_learning"].state),
        str(lines["line_4_routing"].state),
        str(lines["line_5_collaboration"].state),
        str(lines["line_6_governance"].state),
    ])
    
    # Step 3: 映射到卦象
    hexagram = map_binary_to_hexagram(binary)
    
    # Step 4: 应用强兜底规则（guardrails）
    hexagram, triggered_rules = apply_guardrails(lines, hexagram)
    
    # Step 5: 检测变爻
    changing_lines = []
    if previous_binary and len(previous_binary) == 6:
        for i in range(6):
            if binary[i] != previous_binary[i]:
                changing_lines.append(i + 1)  # 爻的编号从 1 开始
    
    # Step 6: 识别主导因素
    dominant_factors = []
    for name, line in lines.items():
        if line.score < 0.3:
            dominant_factors.append(f"{line.description}（低分: {line.score:.2f}）")
        elif line.is_changing:
            dominant_factors.append(f"{line.description}（临界: {line.score:.2f}）")
    
    if not dominant_factors:
        dominant_factors.append("系统整体稳定")
    
    # Step 7: 计算整体置信度
    confidence = sum(line.confidence for line in lines.values()) / 6.0
    
    # Step 8: 生成详细解释
    explanation = f"""
【全局卦象】
卦象: {hexagram.name}
卦义: {hexagram.meaning}
风险等级: {hexagram.risk.value}

六爻状态（自下而上）:
  初爻（基础设施层）: {lines['line_1_infra'].score:.2f} ({'阳' if lines['line_1_infra'].state == 1 else '阴'}) {'[临界]' if lines['line_1_infra'].is_changing else ''}
  二爻（执行层）: {lines['line_2_execution'].score:.2f} ({'阳' if lines['line_2_execution'].state == 1 else '阴'}) {'[临界]' if lines['line_2_execution'].is_changing else ''}
  三爻（学习层）: {lines['line_3_learning'].score:.2f} ({'阳' if lines['line_3_learning'].state == 1 else '阴'}) {'[临界]' if lines['line_3_learning'].is_changing else ''}
  四爻（调度层）: {lines['line_4_routing'].score:.2f} ({'阳' if lines['line_4_routing'].state == 1 else '阴'}) {'[临界]' if lines['line_4_routing'].is_changing else ''}
  五爻（协作层）: {lines['line_5_collaboration'].score:.2f} ({'阳' if lines['line_5_collaboration'].state == 1 else '阴'}) {'[临界]' if lines['line_5_collaboration'].is_changing else ''}
  上爻（治理层）: {lines['line_6_governance'].score:.2f} ({'阳' if lines['line_6_governance'].state == 1 else '阴'}) {'[临界]' if lines['line_6_governance'].is_changing else ''}

变爻: {changing_lines if changing_lines else '无'}
主导因素: {', '.join(dominant_factors)}
整体置信度: {confidence:.2f}

推荐动作:
{chr(10).join(f'  • {action}' for action in hexagram.actions[:4])}
"""
    
    if triggered_rules:
        explanation += f"\n⚠️ 兜底规则触发: {', '.join(triggered_rules)}"
    
    # Step 9: 构造结果对象
    return HexagramResult(
        global_hexagram_name=hexagram.name,
        global_hexagram_bits=binary,
        global_risk_level=hexagram.risk.value,
        global_recommended_actions=hexagram.actions[:4],
        line_scores={
            "line_1_infra": lines["line_1_infra"].score,
            "line_2_execution": lines["line_2_execution"].score,
            "line_3_learning": lines["line_3_learning"].score,
            "line_4_routing": lines["line_4_routing"].score,
            "line_5_collaboration": lines["line_5_collaboration"].score,
            "line_6_governance": lines["line_6_governance"].score,
        },
        changing_lines=changing_lines,
        dominant_factors=dominant_factors,
        guardrail_triggered=len(triggered_rules) > 0,
        guardrail_reasons=triggered_rules,
        explanation=explanation.strip(),
        confidence=confidence,
        timestamp=time.time()
    )

# ============================================================
# 测试用例
# ============================================================

if __name__ == "__main__":
    print("=== Hexagram Engine 测试 ===\n")
    
    # 测试场景 1：新 Agent 启动
    print("=" * 60)
    print("场景 1：新 Agent 启动")
    print("=" * 60)
    metrics_new = {
        "api_health": 0.3,
        "network_latency": 0.8,
        "dependency_available": 0.2,
        "task_success_rate": 0.0,
        "timeout_rate": 0.0,
        "retry_rate": 0.0,
        "recommendation_hit_rate": 0.0,
        "learning_gain": 0.0,
        "experience_validity": 0.0,
        "router_accuracy": 0.5,
        "queue_length": 0.0,
        "dispatch_stability": 0.5,
        "agent_cooperation": 0.5,
        "resource_sharing": 0.5,
        "conflict_rate": 0.0,
        "evolution_score": 0.0,
        "canary_health": 0.5,
        "global_stability": 0.5,
    }
    result = calculate_hexagram(metrics_new)
    print(result.explanation)
    print()
    
    # 测试场景 2：成熟 Agent
    print("=" * 60)
    print("场景 2：成熟 Agent")
    print("=" * 60)
    metrics_mature = {
        "api_health": 0.98,
        "network_latency": 0.1,
        "dependency_available": 0.95,
        "task_success_rate": 0.96,
        "timeout_rate": 0.05,
        "retry_rate": 0.03,
        "recommendation_hit_rate": 0.85,
        "learning_gain": 0.80,
        "experience_validity": 0.90,
        "router_accuracy": 0.92,
        "queue_length": 0.15,
        "dispatch_stability": 0.95,
        "agent_cooperation": 0.90,
        "resource_sharing": 0.88,
        "conflict_rate": 0.05,
        "evolution_score": 99.5,
        "canary_health": 0.95,
        "global_stability": 0.98,
    }
    result = calculate_hexagram(metrics_mature)
    print(result.explanation)
    print()
    
    # 测试场景 3：基础设施异常（触发兜底规则）
    print("=" * 60)
    print("场景 3：基础设施异常（触发兜底规则）")
    print("=" * 60)
    metrics_infra_fail = {
        "api_health": 0.15,  # 严重异常
        "network_latency": 0.9,
        "dependency_available": 0.3,
        "task_success_rate": 0.45,
        "timeout_rate": 0.6,
        "retry_rate": 0.5,
        "recommendation_hit_rate": 0.70,
        "learning_gain": 0.65,
        "experience_validity": 0.75,
        "router_accuracy": 0.80,
        "queue_length": 0.7,
        "dispatch_stability": 0.60,
        "agent_cooperation": 0.75,
        "resource_sharing": 0.70,
        "conflict_rate": 0.2,
        "evolution_score": 85.0,
        "canary_health": 0.70,
        "global_stability": 0.65,
    }
    result = calculate_hexagram(metrics_infra_fail)
    print(result.explanation)
    print()
    
    # 测试场景 4：爻变检测（既济 → 蹇）
    print("=" * 60)
    print("场景 4：爻变检测（API 突然超时）")
    print("=" * 60)
    previous_binary = "111111"  # 既济卦
    metrics_api_timeout = metrics_mature.copy()
    metrics_api_timeout["api_health"] = 0.18  # API 突然大量失败
    result = calculate_hexagram(metrics_api_timeout, previous_binary)
    print(result.explanation)
    print()
    
    # 输出 JSON 格式（用于集成）
    print("=" * 60)
    print("JSON 输出示例")
    print("=" * 60)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
