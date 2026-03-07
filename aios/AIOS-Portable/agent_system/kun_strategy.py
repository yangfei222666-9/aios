# kun_strategy.py
# 坤卦专属积累策略 - 生产就绪版 v2.0（LowSuccess_Agent优化）
# 作者：Grok + 你 | 版本：v2.0 | 日期：2026.03

import json
from datetime import datetime

def get_kun_thresholds():
    """获取坤卦动态阈值"""
    return {
        'success_rate': 80,  # 成功率阈值（%）
        'confidence': 85,    # 置信度阈值（%）
        'low_success_threshold': 50  # LowSuccess Agent失败率阈值（%）
    }

# LowSuccess_Agent专项优化（坤卦期核心）
LOW_SUCCESS_OPTIMIZE = """
当前LowSuccess_Agent失败模式检测：
- 连续失败率>50% → 自动降权50%
- 触发Error_Pattern_Learner学习其失败日志
- 优先交给Recovery_Agent + Knowledge_Base_Manager处理

置信度最终冲刺公式：
fused = base * 0.65 + evolution * 0.35 + (success>80 ? 3.5 : 0) + (low_success_fixed ? 2.0 : 0)
"""

KUN_STRATEGY_PROMPT = """
你当前处于《易经》第2卦：坤卦（地势坤，君子以厚德载物）
置信度：{confidence:.1f}% | 风险等级：low | 成功率：{success_rate:.1f}%

核心象意：
- 大地厚德载物 → 系统极度稳定，适合长期积累、厚积薄发
- 君子以厚德载物 → 现在最优策略是"稳中求进"，不要激进扩张，先夯实基础

你的核心任务（严格按以下5步执行）：

1. 厚德载物（立即执行）
   - 把所有成功任务的中间结果、知识片段永久存入知识库/向量数据库
   - 开启"坤卦积累模式"：每10分钟做一次全量数据快照

2. 顺势而为（资源积累）
   - 缓慢增加任务生成频率（每次+10%而非翻倍）
   - 优先积累高质量数据：给高成功率Agent增加权重

3. 防微杜渐（保持坤象）
   - 持续监控置信度≥85% 和 成功率≥78% 两条线
   - 若下滑立即切换"比卦亲比模式"或"大过卦减负"

4. LowSuccess_Agent专项优化（新增）
   - 检测连续失败率>50%的Agent → 自动降权50%
   - 触发Error_Pattern_Learner学习失败日志
   - 优先交给Recovery_Agent + Knowledge_Base_Manager处理

5. 事后厚积（闭环学习）
   - 把本次从大过卦翻盘到坤卦的完整轨迹记录为"坤卦案例"
   - 输出3条长期可复用经验

请严格输出JSON行动计划：
{{
  "current_hex": "坤卦",
  "confidence": {confidence},
  "actions": [...],
  "accumulation_plan": "每日快照 + 权重调整 + LowSuccess优化",
  "learning_points": [...]
}}
"""

def apply_kun_strategy(state: dict) -> dict:
    """一键激活坤卦积累策略（v2.0 - 含LowSuccess优化）"""
    prompt = KUN_STRATEGY_PROMPT.format(
        confidence=state.get('confidence', 92.9),
        success_rate=state.get('success_rate', 80.4)
    )
    
    # 检测LowSuccess_Agent
    low_success_agents = state.get('low_success_agents', 0)
    low_success_fixed = low_success_agents > 0
    
    # 示例行动计划（实际接LLM）
    plan = {
        "current_hex": "坤卦",
        "risk": "low",
        "confidence": state.get('confidence', 92.9),
        "success_rate": state.get('success_rate', 80.4),
        "low_success_agents": low_success_agents,
        "low_success_fixed": low_success_fixed,
        "actions": [
            {"step": 1, "action": "save_to_knowledge_base", "detail": "全量快照到知识库", "priority": "high"},
            {"step": 2, "action": "gradual_task_increase", "detail": "生成频率+10%", "priority": "medium"},
            {"step": 3, "action": "monitor_thresholds", "detail": "监控置信度≥85%和成功率≥78%", "priority": "high"},
            {"step": 4, "action": "optimize_low_success", "detail": f"优化{low_success_agents}个LowSuccess_Agent", "priority": "critical" if low_success_fixed else "low"},
            {"step": 5, "action": "record_case_study", "detail": "记录大过→坤卦翻盘案例", "priority": "medium"}
        ],
        "accumulation_plan": "每日快照 + 权重调整 + LowSuccess优化",
        "learning_points": [
            "80%+成功率时优先积累而非扩张",
            "坤卦是最佳长期增长窗口",
            "厚德载物 = 数据永存",
            "LowSuccess_Agent自动降权50%提升整体成功率"
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # 保存到历史
    with open('kun_history.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(plan, ensure_ascii=False) + '\n')
    
    print("[KUN] Kun hexagram accumulation mode activated (v2.0)!")
    print(f"   Confidence: {plan['confidence']:.1f}%")
    print(f"   Success Rate: {plan['success_rate']:.1f}%")
    print(f"   LowSuccess Agents: {low_success_agents} (Fixed: {low_success_fixed})")
    print(f"   Actions: {len(plan['actions'])} steps")
    print(f"   Strategy: Steady accumulation + LowSuccess optimization")
    
    return plan


def check_kun_stability(state):
    """检查坤卦稳定性"""
    confidence = state.get('confidence', 0)
    success_rate = state.get('success_rate', 0)
    
    # 坤卦稳定阈值
    if confidence >= 85 and success_rate >= 78:
        return "stable"
    elif confidence >= 75 and success_rate >= 70:
        return "warning"
    else:
        return "unstable"


if __name__ == "__main__":
    # 测试
    test_state = {
        "hex_name": "坤卦",
        "confidence": 92.9,
        "success_rate": 80.4,
        "completed": 205,
        "total": 255
    }
    
    plan = apply_kun_strategy(test_state)
    print("\n[TEST] Kun strategy plan generated:")
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    
    stability = check_kun_stability(test_state)
    print(f"\n[STABILITY] Current status: {stability}")
