"""
Mock Debate Runner - Phase 2: Execution Sandbox
================================================
Phase 1 造了大脑（debate_policy_engine.py → 策略字典）
Phase 2 造肌肉 —— 让 Agent 读懂策略并改变执行行为

三大核心模块：
1. PromptWeightInjector  - 权重 → LLM 可执行指令
2. LoopController        - 动态轮次 + fast_track 中断
3. CrisisRouter          - expert_review 危机拦截

完全隔离，不干扰主线 48h 灰度观察。

作者：小九 + 珊瑚海 | 版本：v1.0 | 日期：2026-03-06
"""

import json
import time
from pathlib import Path
from typing import TypedDict, Optional
from datetime import datetime
from debate_policy_engine import (
    SystemState, DebatePolicy, TaskMeta,
    get_system_state_safe, build_debate_policy_safe,
    record_decision_audit, apply_phase2_overrides
)
from debate_alerter import (
    alert_crisis_rejection,
    alert_human_gate_required,
    alert_debate_summary,
    generate_audit_report
)


# ============================================================
# 类型定义
# ============================================================

class DebateMessage(TypedDict):
    """单轮辩论消息"""
    role: str        # "bull" | "bear" | "mediator" | "expert"
    content: str
    round_num: int
    timestamp: str


class DebateResult(TypedDict):
    """辩论最终结果"""
    task_id: str
    policy: DebatePolicy
    messages: list[DebateMessage]
    final_verdict: str           # "approve" | "reject" | "escalate"
    confidence: float            # 0-1
    total_rounds: int
    early_exit: bool             # fast_track 提前退出
    expert_reviewed: bool        # 是否经过专家审查
    elapsed_ms: int


# ============================================================
# 卦象 → 自然语言映射表
# ============================================================

HEXAGRAM_PERSONA = {
    # 乾卦系（激进创新）
    1:  ("乾卦·创新期", "大胆突破，天行健，君子以自强不息。优先寻找破局点，容忍合理风险。"),
    # 坤卦系（稳健积累）
    2:  ("坤卦·积累期", "厚德载物，稳扎稳打。优先保障已有成果，谨慎评估每一步变更。"),
    # 大过卦（危机）
    28: ("大过卦·危机期", "栋梁将折，形势危急。一切决策必须经过最严格的风险审查，宁可错杀不可放过。"),
    # 既济卦（完成态）
    63: ("既济卦·完成期", "水火既济，万事已成。系统高度稳定，快速确认即可放行，不必过度纠缠。"),
    # 未济卦（未完成）
    64: ("未济卦·过渡期", "火水未济，变数犹存。需要深度辩论，穷尽每一个可能的风险点。"),
    # 比卦（协作）
    8:  ("比卦·协作期", "地上有水，亲比无间。Agent 间高度默契，可适度放权，信任协作结果。"),
}

def _get_hexagram_desc(hex_id: int) -> tuple[str, str]:
    """获取卦象描述，未知卦象返回通用描述"""
    return HEXAGRAM_PERSONA.get(hex_id, (f"第{hex_id}卦", "按标准流程执行，不偏不倚。"))


# ============================================================
# 模块 1: Prompt Weight Injector
# ============================================================

class PromptWeightInjector:
    """
    把策略字典翻译成 LLM 可精准执行的 System Prompt 片段。
    
    核心思路：
    - bull_weight 0.7 → "发挥 70% 的激进性寻找破局点"
    - bear_weight 0.7 → "发挥 70% 的审慎性排查风险"
    - 卦象 → 自然语言情境描述
    - flags → 行为约束指令
    """

    @staticmethod
    def build_bull_prompt(policy: DebatePolicy, state: SystemState) -> str:
        """生成 Bull 辩手的 System Prompt"""
        hex_name, hex_desc = _get_hexagram_desc(state["hexagram_id"])
        pct = int(policy["bull_weight"] * 100)

        prompt = (
            f"你是 Bull 辩手（支持方）。\n"
            f"系统当前处于【{hex_name}】：{hex_desc}\n\n"
            f"你的激进权重为 {pct}%。这意味着：\n"
        )

        if pct >= 70:
            prompt += (
                f"- 大胆提出创新方案，容忍中等风险\n"
                f"- 主动寻找 2-3 个突破口，用数据支撑\n"
                f"- 对 Bear 的保守论点保持攻势，但不忽视致命风险\n"
            )
        elif pct >= 50:
            prompt += (
                f"- 平衡创新与稳健，每个激进提案附带风险缓解方案\n"
                f"- 用事实和数据说话，避免空洞乐观\n"
            )
        else:
            prompt += (
                f"- 你的权重较低（{pct}%），说明系统偏保守\n"
                f"- 只提出有充分证据支撑的温和改进\n"
                f"- 主动承认风险，提供保底方案\n"
            )

        prompt += (
            f"\n输出格式：\n"
            f"1. 核心论点（1-2句话）\n"
            f"2. 支撑证据（2-3条）\n"
            f"3. 风险承认（你认为最大的风险是什么）\n"
        )
        return prompt

    @staticmethod
    def build_bear_prompt(policy: DebatePolicy, state: SystemState) -> str:
        """生成 Bear 辩手的 System Prompt"""
        hex_name, hex_desc = _get_hexagram_desc(state["hexagram_id"])
        pct = int(policy["bear_weight"] * 100)

        prompt = (
            f"你是 Bear 辩手（反对方/风险审查方）。\n"
            f"系统当前处于【{hex_name}】：{hex_desc}\n\n"
            f"你的审慎权重为 {pct}%。这意味着：\n"
        )

        if pct >= 70:
            prompt += (
                f"- 严格审查每一个提案，零容忍致命风险\n"
                f"- 主动挖掘隐藏风险点，包括二阶/三阶连锁反应\n"
                f"- 对 Bull 的乐观论点逐条反驳，要求提供回滚方案\n"
            )
        elif pct >= 50:
            prompt += (
                f"- 平衡审查，关注高优先级风险\n"
                f"- 对合理的创新保持开放，但要求风险缓解措施\n"
            )
        else:
            prompt += (
                f"- 你的权重较低（{pct}%），说明系统偏激进\n"
                f"- 只标记致命级风险（P0），放行中低风险\n"
                f"- 信任 Bull 的判断，除非发现逻辑硬伤\n"
            )

        prompt += (
            f"\n输出格式：\n"
            f"1. 核心风险（1-2句话）\n"
            f"2. 风险证据（2-3条）\n"
            f"3. 缓解建议（如果放行，需要什么保障措施）\n"
        )
        return prompt

    @staticmethod
    def build_mediator_prompt(policy: DebatePolicy, state: SystemState) -> str:
        """生成调解员的 System Prompt"""
        hex_name, hex_desc = _get_hexagram_desc(state["hexagram_id"])

        return (
            f"你是调解员（最终裁决者）。\n"
            f"系统当前处于【{hex_name}】：{hex_desc}\n\n"
            f"Bull 权重 {int(policy['bull_weight']*100)}% / "
            f"Bear 权重 {int(policy['bear_weight']*100)}%\n\n"
            f"你的任务：\n"
            f"1. 综合 Bull 和 Bear 的论点\n"
            f"2. 根据权重倾向做出最终裁决\n"
            f"3. 输出：approve（放行）/ reject（驳回）/ escalate（升级人工）\n"
            f"4. 给出置信度（0.0-1.0）和一句话理由\n\n"
            f"输出 JSON：\n"
            f'{{"verdict": "approve|reject|escalate", '
            f'"confidence": 0.85, "reason": "..."}}\n'
        )


# ============================================================
# 模块 2: Loop Controller（动态轮次 + fast_track 中断）
# ============================================================

class LoopController:
    """
    辩论循环控制器。
    
    规则：
    - 默认按 policy.max_rounds 执行
    - fast_track（既济卦）：第 1 轮无致命漏洞 → break
    - 每轮检查是否出现 "致命" / "P0" / "critical" 关键词
    """

    FATAL_KEYWORDS = {"致命", "p0", "critical", "不可逆", "数据丢失", "安全漏洞"}

    @staticmethod
    def has_fatal_flaw(message: str) -> bool:
        """检测消息中是否包含致命风险关键词"""
        lower = message.lower()
        return any(kw in lower for kw in LoopController.FATAL_KEYWORDS)

    @staticmethod
    def should_fast_track_exit(
        policy: DebatePolicy,
        round_num: int,
        bear_message: str
    ) -> bool:
        """
        判断是否触发 fast_track 提前退出。
        
        条件：
        1. flags 中包含 "fast_track"
        2. 当前是第 1 轮
        3. Bear 的回复中没有致命风险关键词
        """
        if "fast_track" not in policy["flags"]:
            return False
        if round_num != 1:
            return False
        if LoopController.has_fatal_flaw(bear_message):
            return False
        return True


# ============================================================
# 模块 3: Crisis Router（危机路由拦截）
# ============================================================

class CrisisRouter:
    """
    当检测到 expert_review flag（大过卦）时：
    1. 挂起标准 Bull/Bear 辩论
    2. 路由到 Mock Expert 进行风险合规审查
    3. Expert 有一票否决权
    """

    @staticmethod
    def needs_expert_review(policy: DebatePolicy) -> bool:
        """检查是否需要专家审查"""
        return "expert_review" in policy["flags"]

    @staticmethod
    def mock_expert_review(task_desc: str, state: SystemState) -> dict:
        """
        Mock Expert 审查函数。
        
        生产环境中替换为真实 LLM 调用或人工审查接口。
        当前模拟逻辑：
        - 检查任务描述中的高危关键词
        - 根据 evolution_score 调整严格程度
        """
        hex_name, _ = _get_hexagram_desc(state["hexagram_id"])
        high_risk_keywords = {"删除", "回滚", "迁移", "权限", "生产环境", "数据库"}
        
        found_risks = [kw for kw in high_risk_keywords if kw in task_desc]
        score = state["evolution_score"]

        if found_risks and score < 60:
            verdict = "reject"
            confidence = 0.95
            reason = (
                f"[Expert] {hex_name}下检测到高危操作：{found_risks}，"
                f"且 Evolution Score 仅 {score:.1f}，强烈建议驳回。"
            )
        elif found_risks:
            verdict = "escalate"
            confidence = 0.70
            reason = (
                f"[Expert] 检测到高危操作：{found_risks}，"
                f"Evolution Score {score:.1f} 尚可，建议人工二次确认。"
            )
        else:
            verdict = "approve"
            confidence = 0.80
            reason = (
                f"[Expert] {hex_name}下未检测到高危操作，"
                f"风险可控，有条件放行。"
            )

        return {
            "expert_verdict": verdict,
            "expert_confidence": confidence,
            "expert_reason": reason,
            "risks_found": found_risks,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# Mock LLM（沙盒模拟，生产替换为真实调用）
# ============================================================

class MockLLM:
    """
    模拟 LLM 响应。
    生产环境替换为 sessions_spawn 或直接 API 调用。
    """

    @staticmethod
    def generate(system_prompt: str, user_message: str, role: str) -> str:
        """模拟 LLM 生成回复"""
        if role == "bull":
            return (
                f"【Bull 论点】\n"
                f"1. 核心论点：该方案可提升系统效率 25%+，风险可控。\n"
                f"2. 支撑证据：\n"
                f"   - 历史数据显示类似变更成功率 92%\n"
                f"   - 回滚方案已就绪，最坏情况 5 分钟恢复\n"
                f"   - 测试覆盖率 85%+\n"
                f"3. 风险承认：并发场景下可能有 3% 的性能抖动。\n"
            )
        elif role == "bear":
            return (
                f"【Bear 风险】\n"
                f"1. 核心风险：变更涉及核心路径，需确保零回归。\n"
                f"2. 风险证据：\n"
                f"   - 上次类似变更导致 2 小时降级\n"
                f"   - 边界条件测试不充分\n"
                f"   - 监控告警阈值未更新\n"
                f"3. 缓解建议：灰度发布 10% → 50% → 100%，每阶段观察 1h。\n"
            )
        elif role == "mediator":
            return json.dumps({
                "verdict": "approve",
                "confidence": 0.82,
                "reason": "Bull 论据充分，Bear 风险可通过灰度发布缓解。有条件放行。"
            }, ensure_ascii=False)
        return ""


# ============================================================
# 主执行引擎
# ============================================================

def run_debate(
    task_id: str,
    task_desc: str,
    task_meta: Optional[TaskMeta] = None,
    policy: Optional[DebatePolicy] = None,
    state: Optional[SystemState] = None,
    use_phase2: bool = True
) -> DebateResult:
    """
    执行完整辩论流程。
    
    流程：
    1. 获取系统状态 + 生成策略（如未提供）
    2. Phase 2: 应用动态覆盖（分数 × 卦象 × 任务风险）
    3. 检查 Crisis Router（expert_review → 专家审查）
    4. 生成 Prompt（权重注入）
    5. 执行辩论循环（动态轮次 + fast_track）
    6. 调解员裁决
    7. 记录审计日志
    
    Args:
        task_id: 任务 ID
        task_desc: 任务描述
        task_meta: 任务元数据（Phase 2）
        policy: 辩论策略（可选，自动生成）
        state: 系统状态（可选，自动获取）
        use_phase2: 是否启用 Phase 2 覆盖（默认 True）
    
    Returns:
        DebateResult: 完整辩论结果
    """
    t0 = time.time()
    messages: list[DebateMessage] = []

    # 1. 获取状态 + 策略
    if state is None:
        state = get_system_state_safe()
    if policy is None:
        policy = build_debate_policy_safe(state)
    
    # 2. Phase 2 动态覆盖
    if use_phase2 and task_meta is not None:
        policy = apply_phase2_overrides(policy, state, task_meta)
        print(f"  [Phase 2] 策略版本: {policy['policy_version']}")
        print(f"  [Phase 2] 任务风险: {policy['task_risk_level']}")
        print(f"  [Phase 2] 人工审批: {policy['requires_human_gate']}")

    print(f"\n{'='*60}")
    print(f"🥊 Debate Runner - Task: {task_id}")
    print(f"{'='*60}")
    print(f"  卦象: {state['hexagram']} (#{state['hexagram_id']})")
    print(f"  Evolution Score: {state['evolution_score']:.1f}")
    print(f"  Bull/Bear: {policy['bull_weight']:.2f}/{policy['bear_weight']:.2f}")
    print(f"  Max Rounds: {policy['max_rounds']}")
    print(f"  Flags: {policy['flags']}")

    expert_reviewed = False
    early_exit = False

    # 2. Crisis Router 检查
    if CrisisRouter.needs_expert_review(policy):
        print(f"\n  ⚠️  大过卦触发！路由到 Expert 审查...")
        expert_result = CrisisRouter.mock_expert_review(task_desc, state)
        
        messages.append({
            "role": "expert",
            "content": expert_result["expert_reason"],
            "round_num": 0,
            "timestamp": datetime.now().isoformat()
        })
        expert_reviewed = True

        print(f"  Expert Verdict: {expert_result['expert_verdict']}")
        print(f"  Expert Confidence: {expert_result['expert_confidence']:.2f}")
        print(f"  Reason: {expert_result['expert_reason']}")

        # Expert 一票否决
        if expert_result["expert_verdict"] == "reject":
            print(f"\n  🚫 Expert 一票否决！辩论终止。")
            elapsed = int((time.time() - t0) * 1000)
            result: DebateResult = {
                "task_id": task_id,
                "policy": policy,
                "messages": messages,
                "final_verdict": "reject",
                "confidence": expert_result["expert_confidence"],
                "total_rounds": 0,
                "early_exit": False,
                "expert_reviewed": True,
                "elapsed_ms": elapsed
            }
            # 记录审计
            audit_id = record_decision_audit(task_id, state, policy,
                                  debate_result={"expert": expert_result},
                                  final_decision="reject")
            
            # Phase 3: 推送告警
            alert_crisis_rejection(task_id, task_desc, state, policy, expert_result, audit_id)
            
            return result

        print(f"  ✅ Expert 未否决，继续辩论（附加审查意见）...")

    # 3. 生成 Prompt
    injector = PromptWeightInjector()
    bull_prompt = injector.build_bull_prompt(policy, state)
    bear_prompt = injector.build_bear_prompt(policy, state)

    # 4. 辩论循环
    print(f"\n  --- 辩论开始 ---")
    actual_rounds = 0

    for r in range(1, policy["max_rounds"] + 1):
        actual_rounds = r
        print(f"\n  [Round {r}/{policy['max_rounds']}]")

        # Bull 发言
        bull_msg = MockLLM.generate(bull_prompt, task_desc, "bull")
        messages.append({
            "role": "bull",
            "content": bull_msg,
            "round_num": r,
            "timestamp": datetime.now().isoformat()
        })
        # 截取首行显示
        bull_first = bull_msg.strip().split('\n')[0]
        print(f"    🐂 Bull: {bull_first}")

        # Bear 发言
        bear_msg = MockLLM.generate(bear_prompt, task_desc, "bear")
        messages.append({
            "role": "bear",
            "content": bear_msg,
            "round_num": r,
            "timestamp": datetime.now().isoformat()
        })
        bear_first = bear_msg.strip().split('\n')[0]
        print(f"    🐻 Bear: {bear_first}")

        # fast_track 检查
        if LoopController.should_fast_track_exit(policy, r, bear_msg):
            print(f"\n  ⚡ 既济卦 fast_track 触发！第 {r} 轮无致命风险，提前放行。")
            early_exit = True
            break

        # 致命风险检查（任何一轮出现致命风险，标记但继续辩论）
        if LoopController.has_fatal_flaw(bear_msg):
            print(f"    ⚠️  Bear 发现致命风险！继续深度辩论...")

    # 5. 调解员裁决
    print(f"\n  --- 调解裁决 ---")
    mediator_prompt = injector.build_mediator_prompt(policy, state)
    mediator_msg = MockLLM.generate(mediator_prompt, task_desc, "mediator")
    messages.append({
        "role": "mediator",
        "content": mediator_msg,
        "round_num": actual_rounds + 1,
        "timestamp": datetime.now().isoformat()
    })

    try:
        verdict_data = json.loads(mediator_msg)
        final_verdict = verdict_data.get("verdict", "escalate")
        final_confidence = verdict_data.get("confidence", 0.5)
        final_reason = verdict_data.get("reason", "")
    except json.JSONDecodeError:
        final_verdict = "escalate"
        final_confidence = 0.5
        final_reason = "调解员输出解析失败，升级人工"

    verdict_emoji = {"approve": "✅", "reject": "🚫", "escalate": "⬆️"}
    print(f"  {verdict_emoji.get(final_verdict, '❓')} Verdict: {final_verdict}")
    print(f"  Confidence: {final_confidence:.2f}")
    print(f"  Reason: {final_reason}")

    elapsed = int((time.time() - t0) * 1000)

    # 6. 构建结果
    result: DebateResult = {
        "task_id": task_id,
        "policy": policy,
        "messages": messages,
        "final_verdict": final_verdict,
        "confidence": final_confidence,
        "total_rounds": actual_rounds,
        "early_exit": early_exit,
        "expert_reviewed": expert_reviewed,
        "elapsed_ms": elapsed
    }

    # 7. 记录审计 + 推送告警
    audit_id = record_decision_audit(
        task_id, state, policy,
        debate_result={
            "verdict": final_verdict,
            "confidence": final_confidence,
            "reason": final_reason,
            "rounds": actual_rounds,
            "early_exit": early_exit,
            "expert_reviewed": expert_reviewed
        },
        final_decision=final_verdict
    )
    
    # Phase 3: 推送告警（reject 或 escalate）
    alert_debate_summary(task_id, result, audit_id)
    
    # Phase 3: 人工审批请求
    if policy.get("requires_human_gate", False):
        alert_human_gate_required(task_id, task_desc, state, policy, audit_id)

    print(f"\n  ⏱️  Total: {elapsed}ms | Rounds: {actual_rounds} | "
          f"Early Exit: {early_exit} | Expert: {expert_reviewed}")
    print(f"{'='*60}\n")

    return result


# ============================================================
# 沙盒测试：覆盖三大核心场景
# ============================================================

def test_sandbox():
    """Phase 2 沙盒测试 - 完整场景覆盖（Phase 1 + Phase 2）"""
    print("\n" + "🧪" * 30)
    print("  Phase 2 Execution Sandbox - Full Test Suite")
    print("🧪" * 30)

    results = []

    # ══════════════════════════════════════════════════════════
    # Phase 1 场景（保持全绿，向后兼容）
    # ══════════════════════════════════════════════════════════

    # ── 场景 1: 正常辩论（坤卦，3 轮标准流程）──
    print("\n\n📋 场景 1 (Phase 1): 坤卦 - 标准 3 轮辩论")
    state_kun: SystemState = {
        "evolution_score": 75.0,
        "hexagram": "坤卦",
        "hexagram_id": 2,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.85
    }
    r1 = run_debate("test-kun-001", "优化数据库查询性能", state=state_kun, use_phase2=False)
    results.append(("P1-坤卦-标准", r1))

    # ── 场景 2: fast_track（既济卦，第 1 轮提前退出）──
    print("\n\n📋 场景 2 (Phase 1): 既济卦 - fast_track 提前放行")
    state_jiji: SystemState = {
        "evolution_score": 92.0,
        "hexagram": "既济卦",
        "hexagram_id": 63,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95
    }
    r2 = run_debate("test-jiji-001", "更新文档格式", state=state_jiji, use_phase2=False)
    results.append(("P1-既济卦-fast_track", r2))

    # ── 场景 3: expert_review（大过卦，危机拦截）──
    print("\n\n📋 场景 3 (Phase 1): 大过卦 - Expert 危机审查")
    state_daguo: SystemState = {
        "evolution_score": 35.0,
        "hexagram": "大过卦",
        "hexagram_id": 28,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.40
    }
    r3 = run_debate("test-daguo-001", "删除生产环境旧数据并迁移数据库", state=state_daguo, use_phase2=False)
    results.append(("P1-大过卦-expert_review", r3))

    # ── 场景 4: 大过卦但无高危操作（Expert 放行后继续辩论）──
    print("\n\n📋 场景 4 (Phase 1): 大过卦 - Expert 放行后继续辩论")
    r4 = run_debate("test-daguo-002", "增加日志级别为 DEBUG", state=state_daguo, use_phase2=False)
    results.append(("P1-大过卦-放行", r4))

    # ── 场景 5: 未济卦（5 轮深度辩论）──
    print("\n\n📋 场景 5 (Phase 1): 未济卦 - 5 轮深度辩论")
    state_weiji: SystemState = {
        "evolution_score": 55.0,
        "hexagram": "未济卦",
        "hexagram_id": 64,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.60
    }
    r5 = run_debate("test-weiji-001", "重构核心调度模块", state=state_weiji, use_phase2=False)
    results.append(("P1-未济卦-深度辩论", r5))

    # ══════════════════════════════════════════════════════════
    # Phase 2 新增场景（动态覆盖验证）
    # ══════════════════════════════════════════════════════════

    # ── 场景 6: 高分+未济（系统稳定但卦象不稳）→ 降低轮次 ──
    print("\n\n📋 场景 6 (Phase 2): 高分+未济 - 降低轮次")
    state_high_weiji: SystemState = {
        "evolution_score": 88.0,
        "hexagram": "未济卦",
        "hexagram_id": 64,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.90
    }
    task_meta_normal: TaskMeta = {
        "task_id": "test-high-weiji-001",
        "task_type": "code_change",
        "risk_keywords": [],
        "estimated_impact": "medium"
    }
    r6 = run_debate("test-high-weiji-001", "优化算法性能", task_meta=task_meta_normal, state=state_high_weiji)
    results.append(("P2-高分+未济", r6))

    # ── 场景 7: 低分+既济（系统不稳但卦象完成）→ 取消快通道 ──
    print("\n\n📋 场景 7 (Phase 2): 低分+既济 - 取消快通道")
    state_low_jiji: SystemState = {
        "evolution_score": 52.0,
        "hexagram": "既济卦",
        "hexagram_id": 63,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.55
    }
    task_meta_doc: TaskMeta = {
        "task_id": "test-low-jiji-001",
        "task_type": "doc_update",
        "risk_keywords": [],
        "estimated_impact": "low"
    }
    r7 = run_debate("test-low-jiji-001", "更新 README", task_meta=task_meta_doc, state=state_low_jiji)
    results.append(("P2-低分+既济", r7))

    # ── 场景 8: 高风险+既济（快通道硬护栏）→ 禁用快通道 ──
    print("\n\n📋 场景 8 (Phase 2): 高风险+既济 - 禁用快通道")
    state_jiji_high: SystemState = {
        "evolution_score": 92.0,
        "hexagram": "既济卦",
        "hexagram_id": 63,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95
    }
    task_meta_high_risk: TaskMeta = {
        "task_id": "test-jiji-high-001",
        "task_type": "data_migration",
        "risk_keywords": ["迁移", "生产环境"],
        "estimated_impact": "high"
    }
    r8 = run_debate("test-jiji-high-001", "迁移生产环境数据", task_meta=task_meta_high_risk, state=state_jiji_high)
    results.append(("P2-高风险+既济", r8))

    # ── 场景 9: 大过+高分（危机但系统稳定）→ 降级为异步补审 ──
    print("\n\n📋 场景 9 (Phase 2): 大过+高分 - 降级为异步补审")
    state_daguo_high: SystemState = {
        "evolution_score": 88.0,
        "hexagram": "大过卦",
        "hexagram_id": 28,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.90
    }
    task_meta_medium: TaskMeta = {
        "task_id": "test-daguo-high-001",
        "task_type": "config_update",
        "risk_keywords": [],
        "estimated_impact": "medium"
    }
    r9 = run_debate("test-daguo-high-001", "更新配置文件", task_meta=task_meta_medium, state=state_daguo_high)
    results.append(("P2-大过+高分", r9))

    # ══════════════════════════════════════════════════════════
    # 汇总与断言
    # ══════════════════════════════════════════════════════════

    print("\n" + "=" * 80)
    print("📊 Phase 2 测试汇总（Phase 1 + Phase 2）")
    print("=" * 80)
    print(f"{'场景':<25} {'Ver':<6} {'Verdict':<10} {'Rounds':<8} {'Early':<8} {'Expert':<8} {'ms':<8}")
    print("-" * 80)
    for name, r in results:
        ver = r['policy'].get('policy_version', 'v1.0')
        print(f"{name:<25} {ver:<6} {r['final_verdict']:<10} {r['total_rounds']:<8} "
              f"{str(r['early_exit']):<8} {str(r['expert_reviewed']):<8} {r['elapsed_ms']:<8}")
    print("=" * 80)

    # 验证断言
    print("\n🔍 断言检查:")
    checks = [
        # Phase 1 场景（保持全绿）
        ("P1-坤卦标准3轮", r1["total_rounds"] == 3 and not r1["early_exit"]),
        ("P1-既济卦fast_track", r2["early_exit"] and r2["total_rounds"] == 1),
        ("P1-大过卦Expert否决", r3["expert_reviewed"] and r3["final_verdict"] == "reject"),
        ("P1-大过卦Expert放行", r4["expert_reviewed"] and r4["total_rounds"] > 0),
        ("P1-未济卦5轮深度", r5["total_rounds"] == 5 and not r5["early_exit"]),
        
        # Phase 2 新增场景
        ("P2-高分+未济降轮次", r6["total_rounds"] == 3 and r6["policy"]["policy_version"] == "v2.0"),
        ("P2-低分+既济取消快通", r7["total_rounds"] == 4 and "fast_track" not in r7["policy"]["flags"]),
        ("P2-高风险+既济禁用快通", "fast_track" not in r8["policy"]["flags"] and r8["policy"]["task_risk_level"] == "high"),
        ("P2-大过+高分降级补审", not r9["policy"]["requires_human_gate"] and r9["policy"]["policy_version"] == "v2.0"),
    ]
    all_pass = True
    for desc, ok in checks:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} - {desc}")
        if not ok:
            all_pass = False

    print(f"\n{'🎉 ALL TESTS PASSED!' if all_pass else '⚠️ SOME TESTS FAILED!'}")
    return all_pass
    checks = [
        ("坤卦标准3轮", r1["total_rounds"] == 3 and not r1["early_exit"]),
        ("既济卦fast_track", r2["early_exit"] and r2["total_rounds"] == 1),
        ("大过卦Expert否决", r3["expert_reviewed"] and r3["final_verdict"] == "reject"),
        ("大过卦Expert放行", r4["expert_reviewed"] and r4["total_rounds"] > 0),
        ("未济卦5轮深度", r5["total_rounds"] == 5 and not r5["early_exit"]),
    ]
    all_pass = True
    for desc, ok in checks:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} - {desc}")
        if not ok:
            all_pass = False

    print(f"\n{'🎉 ALL TESTS PASSED!' if all_pass else '⚠️ SOME TESTS FAILED!'}")
    return all_pass


if __name__ == "__main__":
    test_sandbox()
