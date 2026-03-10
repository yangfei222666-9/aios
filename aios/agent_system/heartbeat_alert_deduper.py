# -*- coding: utf-8 -*-
"""
Heartbeat Alert Deduper - Shadow Mode MVP

核心职责：
  判断一个告警是否应该通知用户（去重 + severity 变化感知）。
  Shadow mode 下只记录判断结果，不控制实际通知。

去重规则（珊瑚海 2026-03-08 确认）：
  - 已发过的告警不重复通知
  - 恶化（WARN→CRIT / 连续失败次数增加）→ 通知
  - 首次出现 → 通知
  - 好转（CRIT→WARN / ERROR→WARN）→ 只记录，不强提醒
  - 错误类型变化 → 通知
  - 修复后再次复发 → 通知

Severity 设计（方案 A：保持状态演化）：
  - ERROR → WARN 是好转
  - WARN → ERROR 是恶化

Shadow Mode 接入：
  - deduper_shadow_enabled = true  → 并行运行，只记录
  - deduper_notify_enabled = false → 不控制通知
  - 观察期通过后再切 deduper_notify_enabled = true
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from paths import DATA_DIR

# ── 文件路径 ──────────────────────────────────────────────────────────────────
DEDUP_STATE_FILE = DATA_DIR / "deduper_state.json"
SHADOW_LOG_FILE = DATA_DIR / "deduper_shadow_log.jsonl"
DEDUP_FEEDBACK_FILE = DATA_DIR / "deduper_feedback.jsonl"

# ── severity 等级映射（数值越大越严重）──────────────────────────────────────
SEVERITY_RANK = {
    "info": 0,
    "warn": 1,
    "crit": 2,
    "error": 2,  # error 和 crit 同级
}


def _load_state() -> Dict:
    """加载去重状态"""
    if DEDUP_STATE_FILE.exists():
        try:
            with open(DEDUP_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"alerts": {}, "version": "1.0.0", "created_at": datetime.now().isoformat()}


def _save_state(state: Dict):
    """保存去重状态"""
    DEDUP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now().isoformat()
    with open(DEDUP_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _append_shadow_log(entry: Dict):
    """追加 shadow 对比日志"""
    SHADOW_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry["logged_at"] = datetime.now().isoformat()
    with open(SHADOW_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _append_feedback(entry: Dict):
    """追加反馈记录"""
    DEDUP_FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry["logged_at"] = datetime.now().isoformat()
    with open(DEDUP_FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def evaluate_alert(alert: Dict) -> Dict:
    """
    评估一个告警是否应该通知。

    Args:
        alert: skill_failure_alert 产生的告警对象
            必须包含: skill_id, alert_level, consecutive_failures, last_failure_reason

    Returns:
        {
            "should_notify": bool,
            "reason": str,           # 判断原因
            "change_type": str,      # "new" | "escalation" | "degradation" | "improvement" | "duplicate" | "recurrence"
            "severity_delta": int,   # 正=恶化, 负=好转, 0=不变
            "skill_id": str,
            "current_level": str,
            "previous_level": str | None,
        }
    """
    state = _load_state()
    alerts_state = state.setdefault("alerts", {})

    skill_id = alert.get("skill_id", "unknown")
    current_level = alert.get("alert_level", "warn")
    current_failures = alert.get("consecutive_failures", 0)
    current_error_type = alert.get("last_failure_reason", "unknown")

    previous = alerts_state.get(skill_id)

    result = {
        "skill_id": skill_id,
        "current_level": current_level,
        "previous_level": None,
        "should_notify": False,
        "reason": "",
        "change_type": "duplicate",
        "severity_delta": 0,
    }

    if previous is None:
        # 首次出现 → 通知
        result["should_notify"] = True
        result["reason"] = "首次出现"
        result["change_type"] = "new"
    else:
        prev_level = previous.get("alert_level", "warn")
        prev_failures = previous.get("consecutive_failures", 0)
        prev_error_type = previous.get("last_failure_reason", "unknown")
        prev_resolved = previous.get("resolved", False)

        result["previous_level"] = prev_level

        current_rank = SEVERITY_RANK.get(current_level, 1)
        prev_rank = SEVERITY_RANK.get(prev_level, 1)
        result["severity_delta"] = current_rank - prev_rank

        if prev_resolved:
            # 修复后再次复发 → 通知
            result["should_notify"] = True
            result["reason"] = f"修复后复发（之前已 resolved）"
            result["change_type"] = "recurrence"

        elif current_rank > prev_rank:
            # 恶化 → 通知
            result["should_notify"] = True
            result["reason"] = f"恶化: {prev_level} → {current_level}"
            result["change_type"] = "escalation"

        elif current_rank < prev_rank:
            # 好转 → 只记录，不强提醒
            result["should_notify"] = False
            result["reason"] = f"好转: {prev_level} → {current_level}（只记录）"
            result["change_type"] = "improvement"

        elif current_failures > prev_failures:
            # 连续失败次数增加 → 通知
            result["should_notify"] = True
            result["reason"] = f"连续失败增加: {prev_failures} → {current_failures}"
            result["change_type"] = "degradation"

        elif current_error_type != prev_error_type:
            # 错误类型变化 → 通知
            result["should_notify"] = True
            result["reason"] = f"错误类型变化: {prev_error_type} → {current_error_type}"
            result["change_type"] = "escalation"

        else:
            # 完全相同 → 去重，不通知
            result["should_notify"] = False
            result["reason"] = f"重复告警（{current_level}, {current_failures}次, {current_error_type}）"
            result["change_type"] = "duplicate"

    # 更新状态（无论是否通知都更新，保持最新快照）
    alerts_state[skill_id] = {
        "alert_level": current_level,
        "consecutive_failures": current_failures,
        "last_failure_reason": current_error_type,
        "last_seen_at": datetime.now().isoformat(),
        "resolved": False,
        "notify_count": (previous or {}).get("notify_count", 0) + (1 if result["should_notify"] else 0),
    }
    _save_state(state)

    return result


def mark_resolved(skill_id: str):
    """标记一个告警为已解决（下次出现算复发）"""
    state = _load_state()
    if skill_id in state.get("alerts", {}):
        state["alerts"][skill_id]["resolved"] = True
        state["alerts"][skill_id]["resolved_at"] = datetime.now().isoformat()
        _save_state(state)


def run_shadow_evaluation(alerts: List[Dict]) -> List[Dict]:
    """
    Shadow mode 入口：对一批告警做去重评估，只记录不控制。

    Args:
        alerts: skill_failure_alert.check_consecutive_failures() 的输出

    Returns:
        评估结果列表
    """
    results = []

    for alert in alerts:
        evaluation = evaluate_alert(alert)
        results.append(evaluation)

        # 写 shadow 对比日志
        shadow_entry = {
            "skill_id": evaluation["skill_id"],
            "current_level": evaluation["current_level"],
            "previous_level": evaluation["previous_level"],
            "deduper_decision": "notify" if evaluation["should_notify"] else "suppress",
            "reason": evaluation["reason"],
            "change_type": evaluation["change_type"],
            "severity_delta": evaluation["severity_delta"],
            "actual_notification": "sent",  # 旧逻辑总是发送，shadow 记录对比
            "match": not evaluation["should_notify"],  # 如果 deduper 说 suppress，而旧逻辑 sent → mismatch
        }
        _append_shadow_log(shadow_entry)

    # 打印 shadow 摘要
    notify_count = sum(1 for r in results if r["should_notify"])
    suppress_count = len(results) - notify_count
    print(f"   [DEDUPER_SHADOW] Evaluated {len(results)} alerts: "
          f"notify={notify_count}, suppress={suppress_count}")

    for r in results:
        icon = "📢" if r["should_notify"] else "🔇"
        print(f"      {icon} {r['skill_id']}: {r['reason']}")

    return results


def get_shadow_stats(hours: int = 24) -> Dict:
    """获取 shadow 模式统计（用于观察期评估）"""
    if not SHADOW_LOG_FILE.exists():
        return {"total": 0, "notify": 0, "suppress": 0, "mismatch": 0}

    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    total = notify = suppress = mismatch = 0
    with open(SHADOW_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get("logged_at", "") >= cutoff:
                        total += 1
                        if entry["deduper_decision"] == "notify":
                            notify += 1
                        else:
                            suppress += 1
                        if not entry.get("match", True):
                            mismatch += 1
                except (json.JSONDecodeError, KeyError):
                    continue

    return {
        "total": total,
        "notify": notify,
        "suppress": suppress,
        "mismatch": mismatch,
        "suppress_rate": suppress / total if total > 0 else 0,
        "hours": hours,
    }


if __name__ == "__main__":
    print("Heartbeat Alert Deduper - Shadow Mode Test")
    print("=" * 60)

    # 模拟告警
    test_alerts = [
        {
            "alert_level": "crit",
            "skill_id": "api-testing-skill",
            "skill_name": "api-testing-skill",
            "skill_version": "1.0.0",
            "consecutive_failures": 5,
            "last_failure_reason": "network_error",
        },
        {
            "alert_level": "warn",
            "skill_id": "pdf-skill",
            "skill_name": "pdf-skill",
            "skill_version": "2.1.0",
            "consecutive_failures": 2,
            "last_failure_reason": "timeout",
        },
    ]

    results = run_shadow_evaluation(test_alerts)

    print(f"\n📊 Shadow Stats (24h):")
    stats = get_shadow_stats(24)
    print(f"   Total: {stats['total']}")
    print(f"   Notify: {stats['notify']}")
    print(f"   Suppress: {stats['suppress']}")
    print(f"   Suppress rate: {stats['suppress_rate']:.1%}")
