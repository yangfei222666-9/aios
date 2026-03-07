"""
Debate Alerter - Phase 3 Step 1: 审计与告警闭环
================================================
大过卦拦截 → 立刻推送 Telegram（带完整上下文）
生成审计报告（Mermaid 流程图 + 决策链）

作者：小九 + 珊瑚海 | 版本：v1.0 | 日期：2026-03-06
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from notifier import write_alert


# ============================================================
# 告警触发器
# ============================================================

def alert_crisis_rejection(
    task_id: str,
    task_desc: str,
    state: dict,
    policy: dict,
    expert_result: dict,
    audit_id: str
):
    """
    大过卦 Expert 一票否决 → 立刻推送 Telegram
    
    Args:
        task_id: 任务 ID
        task_desc: 任务描述
        state: 系统状态
        policy: 辩论策略
        expert_result: Expert 审查结果
        audit_id: 审计记录 ID
    """
    hex_name = state.get("hexagram", "未知卦象")
    score = state.get("evolution_score", 0)
    risks = expert_result.get("risks_found", [])
    reason = expert_result.get("expert_reason", "")
    
    title = f"🚨 大过卦危机拦截 - {task_id}"
    body = (
        f"【高危任务被拦截】\n\n"
        f"任务: {task_desc}\n"
        f"卦象: {hex_name} (#{state.get('hexagram_id', 0)})\n"
        f"Evolution Score: {score:.1f}\n"
        f"风险等级: {policy.get('task_risk_level', 'unknown')}\n\n"
        f"检测到高危操作: {', '.join(risks)}\n\n"
        f"Expert 裁决: {reason}\n\n"
        f"审计 ID: {audit_id}\n"
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    write_alert("critical", title, body)
    print(f"[ALERT] 已推送 Telegram: {title}")


def alert_human_gate_required(
    task_id: str,
    task_desc: str,
    state: dict,
    policy: dict,
    audit_id: str
):
    """
    requires_human_gate=True → 推送人工审批请求
    
    Args:
        task_id: 任务 ID
        task_desc: 任务描述
        state: 系统状态
        policy: 辩论策略
        audit_id: 审计记录 ID
    """
    hex_name = state.get("hexagram", "未知卦象")
    score = state.get("evolution_score", 0)
    
    title = f"⚠️ 人工审批请求 - {task_id}"
    body = (
        f"【需要人工确认】\n\n"
        f"任务: {task_desc}\n"
        f"卦象: {hex_name} (#{state.get('hexagram_id', 0)})\n"
        f"Evolution Score: {score:.1f}\n"
        f"风险等级: {policy.get('task_risk_level', 'unknown')}\n\n"
        f"原因: {policy.get('reason', '')}\n\n"
        f"审计 ID: {audit_id}\n"
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"请回复: approve / reject"
    )
    
    write_alert("warning", title, body)
    print(f"[ALERT] 已推送 Telegram: {title}")


def alert_debate_summary(
    task_id: str,
    result: dict,
    audit_id: str
):
    """
    辩论完成 → 推送摘要（仅 critical 或 escalate）
    
    Args:
        task_id: 任务 ID
        result: 辩论结果
        audit_id: 审计记录 ID
    """
    verdict = result.get("final_verdict", "unknown")
    
    # 只推送 reject 或 escalate
    if verdict not in ["reject", "escalate"]:
        return
    
    confidence = result.get("confidence", 0)
    rounds = result.get("total_rounds", 0)
    early_exit = result.get("early_exit", False)
    expert_reviewed = result.get("expert_reviewed", False)
    
    emoji = {"reject": "🚫", "escalate": "⬆️"}.get(verdict, "❓")
    level = "critical" if verdict == "reject" else "warning"
    
    title = f"{emoji} 辩论结果: {verdict.upper()} - {task_id}"
    body = (
        f"【辩论完成】\n\n"
        f"最终裁决: {verdict}\n"
        f"置信度: {confidence:.2f}\n"
        f"辩论轮次: {rounds}\n"
        f"提前退出: {early_exit}\n"
        f"专家审查: {expert_reviewed}\n\n"
        f"审计 ID: {audit_id}\n"
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    write_alert(level, title, body)
    print(f"[ALERT] 已推送 Telegram: {title}")


# ============================================================
# 审计报告生成器（Mermaid 流程图）
# ============================================================

def generate_audit_report(audit_id: str, output_path: Optional[Path] = None) -> str:
    """
    从 decision_audit.jsonl 读取审计记录，生成 Mermaid 流程图
    
    Args:
        audit_id: 审计记录 ID
        output_path: 输出路径（默认 reports/audit_{audit_id}.md）
    
    Returns:
        report_path: 报告文件路径
    """
    workspace = Path(__file__).parent
    audit_file = workspace / "decision_audit.jsonl"
    
    if not audit_file.exists():
        print(f"[WARN] 审计文件不存在: {audit_file}")
        return ""
    
    # 查找审计记录
    audit = None
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                if record.get("audit_id") == audit_id:
                    audit = record
                    break
            except json.JSONDecodeError:
                continue
    
    if not audit:
        print(f"[WARN] 未找到审计记录: {audit_id}")
        return ""
    
    # 提取数据
    task_id = audit.get("task_id", "unknown")
    state = audit.get("system_state", {})
    policy = audit.get("debate_policy", {})
    result = audit.get("debate_result", {})
    final_decision = audit.get("final_decision", "unknown")
    
    hex_name = state.get("hexagram", "未知")
    hex_id = state.get("hexagram_id", 0)
    score = state.get("evolution_score", 0)
    confidence = state.get("confidence", 0)
    
    bull_weight = policy.get("bull_weight", 0.5)
    bear_weight = policy.get("bear_weight", 0.5)
    max_rounds = policy.get("max_rounds", 3)
    flags = policy.get("flags", [])
    policy_version = policy.get("policy_version", "v1.0")
    risk_level = policy.get("task_risk_level", "medium")
    human_gate = policy.get("requires_human_gate", False)
    
    # 生成 Mermaid 流程图
    mermaid = f"""# 审计报告 - {audit_id}

**任务 ID:** {task_id}  
**时间:** {audit.get('timestamp', '')}  
**最终决策:** {final_decision}

---

## 系统状态

- **卦象:** {hex_name} (#{hex_id})
- **Evolution Score:** {score:.1f}
- **置信度:** {confidence:.2f}

---

## 辩论策略 ({policy_version})

- **Bull 权重:** {bull_weight:.2f}
- **Bear 权重:** {bear_weight:.2f}
- **最大轮次:** {max_rounds}
- **特殊标记:** {', '.join(flags) if flags else '无'}
- **风险等级:** {risk_level}
- **人工审批:** {'是' if human_gate else '否'}

---

## 决策流程

```mermaid
graph TD
    A[系统状态] -->|Evolution Score: {score:.1f}| B[生成策略]
    B -->|{policy_version}| C{{卦象: {hex_name}}}
    C -->|Bull: {bull_weight:.2f} / Bear: {bear_weight:.2f}| D[辩论循环]
"""

    # 添加特殊节点
    if "expert_review" in flags:
        mermaid += f"    C -->|大过卦| E[Expert 审查]\n"
        mermaid += f"    E -->|风险等级: {risk_level}| D\n"
    
    if "fast_track" in flags:
        mermaid += f"    D -->|既济卦快通道| F[第1轮检查]\n"
        mermaid += f"    F -->|无致命风险| G[提前放行]\n"
        mermaid += f"    F -->|有风险| D\n"
    
    # 最终裁决
    verdict_emoji = {"approve": "✅", "reject": "🚫", "escalate": "⬆️"}.get(final_decision, "❓")
    mermaid += f"    D --> H[调解裁决]\n"
    mermaid += f"    H --> I[{verdict_emoji} {final_decision}]\n"
    
    if human_gate:
        mermaid += f"    I --> J[人工审批]\n"
    
    mermaid += "```\n\n"
    
    # 添加辩论结果
    if result:
        mermaid += f"## 辩论结果\n\n"
        mermaid += f"- **裁决:** {result.get('verdict', 'unknown')}\n"
        mermaid += f"- **置信度:** {result.get('confidence', 0):.2f}\n"
        mermaid += f"- **轮次:** {result.get('rounds', 0)}\n"
        mermaid += f"- **提前退出:** {'是' if result.get('early_exit', False) else '否'}\n"
        mermaid += f"- **专家审查:** {'是' if result.get('expert_reviewed', False) else '否'}\n"
        mermaid += f"\n**理由:** {result.get('reason', '')}\n"
    
    # 写入文件
    if output_path is None:
        reports_dir = workspace / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"audit_{audit_id}.md"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mermaid)
    
    print(f"[OK] 审计报告已生成: {output_path}")
    return str(output_path)


# ============================================================
# Heartbeat 集成（每小时检查高危拦截）
# ============================================================

def check_recent_crisis_rejections(hours: int = 1) -> list:
    """
    检查最近 N 小时内的大过卦拦截
    
    Args:
        hours: 时间范围（小时）
    
    Returns:
        rejections: 拦截记录列表
    """
    workspace = Path(__file__).parent
    audit_file = workspace / "decision_audit.jsonl"
    
    if not audit_file.exists():
        return []
    
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(hours=hours)
    
    rejections = []
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                
                if timestamp < cutoff:
                    continue
                
                # 检查是否是大过卦拦截
                policy = record.get("debate_policy", {})
                result = record.get("debate_result", {})
                
                if "expert_review" in policy.get("flags", []):
                    if result.get("expert_verdict") == "reject":
                        rejections.append(record)
                
            except (json.JSONDecodeError, ValueError):
                continue
    
    return rejections


def heartbeat_crisis_check():
    """
    Heartbeat 集成：检查最近 1 小时的高危拦截
    
    如果有拦截，生成汇总报告并推送
    """
    rejections = check_recent_crisis_rejections(hours=1)
    
    if not rejections:
        print("[OK] 最近 1 小时无大过卦拦截")
        return
    
    # 生成汇总
    count = len(rejections)
    tasks = [r.get("task_id", "unknown") for r in rejections]
    
    title = f"🚨 大过卦拦截汇总 ({count} 个任务)"
    body = (
        f"【最近 1 小时】\n\n"
        f"拦截任务:\n"
    )
    
    for r in rejections:
        task_id = r.get("task_id", "unknown")
        state = r.get("system_state", {})
        result = r.get("debate_result", {})
        
        body += (
            f"\n- {task_id}\n"
            f"  卦象: {state.get('hexagram', '未知')}\n"
            f"  Evolution Score: {state.get('evolution_score', 0):.1f}\n"
            f"  原因: {result.get('expert_reason', '')}\n"
        )
    
    body += f"\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    write_alert("critical", title, body)
    print(f"[ALERT] 已推送汇总: {count} 个拦截")


# ============================================================
# 测试入口
# ============================================================

def test_alerter():
    """测试告警系统"""
    print("=" * 60)
    print("Debate Alerter - Test")
    print("=" * 60)
    
    # 模拟大过卦拦截
    print("\n[1] 测试大过卦拦截告警...")
    alert_crisis_rejection(
        task_id="test-crisis-001",
        task_desc="删除生产环境旧数据并迁移数据库",
        state={
            "hexagram": "大过卦",
            "hexagram_id": 28,
            "evolution_score": 35.0,
            "confidence": 0.40
        },
        policy={
            "task_risk_level": "high",
            "flags": ["expert_review"]
        },
        expert_result={
            "expert_verdict": "reject",
            "expert_reason": "检测到高危操作：删除、迁移、生产环境、数据库",
            "risks_found": ["删除", "迁移", "生产环境", "数据库"]
        },
        audit_id="audit-test-001"
    )
    
    # 模拟人工审批请求
    print("\n[2] 测试人工审批请求...")
    alert_human_gate_required(
        task_id="test-gate-001",
        task_desc="更新生产环境配置",
        state={
            "hexagram": "大过卦",
            "hexagram_id": 28,
            "evolution_score": 45.0,
            "confidence": 0.50
        },
        policy={
            "task_risk_level": "high",
            "requires_human_gate": True,
            "reason": "大过卦+高风险 → 同步人工审批"
        },
        audit_id="audit-test-002"
    )
    
    # 模拟辩论摘要
    print("\n[3] 测试辩论摘要...")
    alert_debate_summary(
        task_id="test-debate-001",
        result={
            "final_verdict": "reject",
            "confidence": 0.85,
            "total_rounds": 3,
            "early_exit": False,
            "expert_reviewed": True
        },
        audit_id="audit-test-003"
    )
    
    print("\n" + "=" * 60)
    print("[OK] 测试完成！检查 alerts.jsonl")
    print("=" * 60)


if __name__ == "__main__":
    test_alerter()
