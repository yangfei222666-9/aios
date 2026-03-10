"""
Skill Failure Alert - 连续失败预警

核心功能：
1. 检测连续失败（warn: 2次 / crit: 3次）
2. 提取最近失败原因
3. 推荐恢复策略
4. 集成到 Heartbeat（每小时检查）

输出格式：
{
  "alert_level": "warn" | "crit",
  "skill_id": "pdf-skill",
  "consecutive_failures": 2,
  "last_failure_reason": "timeout",
  "suggested_recovery": "increase_timeout_and_retry",
  "failure_window": "最近 5 次执行"
}
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict

from paths import DATA_DIR
from skill_memory import SkillMemory

SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"
ALERT_LOG_FILE = DATA_DIR / "skill_failure_alerts.jsonl"


def check_consecutive_failures(window_size: int = 5) -> List[Dict]:
    """
    检查所有 Skill 的连续失败情况
    
    Args:
        window_size: 检查最近 N 次执行（默认 5）
    
    Returns:
        告警列表（按严重程度排序）
    """
    if not SKILL_EXECUTIONS_FILE.exists():
        return []
    
    # 按 skill_id 分组，收集最近执行记录
    skill_executions = defaultdict(list)
    
    with open(SKILL_EXECUTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    skill_id = SkillMemory.normalize_skill_id(record.get("skill_id", ""))
                    skill_executions[skill_id].append(record)
                except (json.JSONDecodeError, KeyError):
                    continue
    
    # 检查每个 Skill 的连续失败
    alerts = []
    
    for skill_id, executions in skill_executions.items():
        # 按时间排序，取最近 N 次
        executions.sort(key=lambda x: x.get("started_at", ""))
        recent = executions[-window_size:]
        
        if len(recent) < 2:
            continue
        
        # 从最新往前数，计算连续失败次数
        consecutive_failures = 0
        last_failure_reason = None
        
        for record in reversed(recent):
            if record["status"] == "failed":
                consecutive_failures += 1
                if last_failure_reason is None:
                    last_failure_reason = record.get("error", "unknown")
            else:
                break
        
        # 判断告警级别
        alert_level = None
        if consecutive_failures >= 3:
            alert_level = "crit"
        elif consecutive_failures >= 2:
            alert_level = "warn"
        
        if alert_level:
            # 分类错误类型
            error_type = _classify_error(last_failure_reason or "")
            recovery_strategy = _suggest_recovery(error_type)
            
            alert = {
                "alert_level": alert_level,
                "skill_id": skill_id,
                "skill_name": recent[-1].get("skill_name", skill_id),
                "skill_version": recent[-1].get("skill_version", "1.0.0"),
                "consecutive_failures": consecutive_failures,
                "last_failure_reason": error_type,
                "last_failure_detail": last_failure_reason,
                "suggested_recovery": recovery_strategy,
                "failure_window": f"最近 {len(recent)} 次执行",
                "detected_at": datetime.now().isoformat(),
                "recent_executions": [
                    {
                        "execution_id": r.get("execution_id", ""),
                        "status": r["status"],
                        "started_at": r.get("started_at", ""),
                        "duration_ms": r.get("duration_ms", 0),
                        "error": r.get("error", "") if r["status"] == "failed" else None
                    }
                    for r in recent
                ]
            }
            
            alerts.append(alert)
    
    # 按严重程度排序（crit > warn），再按连续失败次数排序
    alerts.sort(key=lambda x: (
        0 if x["alert_level"] == "crit" else 1,
        -x["consecutive_failures"]
    ))
    
    # 记录告警日志
    if alerts:
        _log_alerts(alerts)
    
    return alerts


def _classify_error(error_msg: str) -> str:
    """分类错误类型（与 skill_memory.py 保持一致）"""
    error_lower = error_msg.lower()
    
    if "timeout" in error_lower or "timed out" in error_lower:
        return "timeout"
    elif "encoding" in error_lower or "decode" in error_lower:
        return "encoding_error"
    elif "not found" in error_lower or "no such file" in error_lower:
        return "file_not_found"
    elif "permission" in error_lower:
        return "permission_denied"
    elif any(kw in error_lower for kw in [
        "memory", "out of memory", "oom",
        "resource", "resources exhausted", "insufficient resources",
        "quota exceeded", "disk space", "cpu"
    ]):
        return "resource_exhausted"
    elif any(kw in error_lower for kw in [
        "network", "connection", "dns", "unreachable",
        "502", "503", "504", "gateway"
    ]):
        return "network_error"
    elif any(kw in error_lower for kw in [
        "dependency", "module not found", "import error",
        "package", "version conflict"
    ]):
        return "dependency_error"
    elif "syntax" in error_lower or "parse" in error_lower:
        return "syntax_error"
    else:
        return "unknown"


def _suggest_recovery(error_type: str) -> str:
    """根据错误类型建议恢复策略（与 skill_memory.py 保持一致）"""
    strategies = {
        "timeout": "increase_timeout_and_retry",
        "encoding_error": "try_multiple_encodings",
        "file_not_found": "check_file_path_and_retry",
        "permission_denied": "check_permissions_and_retry",
        "resource_exhausted": "reduce_batch_size_and_retry",
        "network_error": "switch_to_backup_endpoint",
        "dependency_error": "check_dependencies_and_reinstall",
        "syntax_error": "validate_input_and_retry",
        "unknown": "default_recovery"
    }
    return strategies.get(error_type, "default_recovery")


def _log_alerts(alerts: List[Dict]):
    """记录告警到日志文件"""
    ALERT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ALERT_LOG_FILE, "a", encoding="utf-8") as f:
        for alert in alerts:
            # 简化版（不包含 recent_executions）
            log_entry = {
                "detected_at": alert["detected_at"],
                "alert_level": alert["alert_level"],
                "skill_id": alert["skill_id"],
                "consecutive_failures": alert["consecutive_failures"],
                "last_failure_reason": alert["last_failure_reason"],
                "suggested_recovery": alert["suggested_recovery"]
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def format_alert_message(alert: Dict) -> str:
    """格式化告警消息（用于 Heartbeat 输出）"""
    emoji = "🔴" if alert["alert_level"] == "crit" else "⚠️"
    
    msg = (
        f"{emoji} {alert['alert_level'].upper()}: {alert['skill_id']} v{alert['skill_version']}\n"
        f"   连续失败: {alert['consecutive_failures']} 次\n"
        f"   最近原因: {alert['last_failure_reason']}\n"
        f"   建议动作: {alert['suggested_recovery']}\n"
        f"   检测窗口: {alert['failure_window']}"
    )
    
    return msg


def get_recent_alerts(hours: int = 24) -> List[Dict]:
    """获取最近 N 小时的告警记录"""
    if not ALERT_LOG_FILE.exists():
        return []
    
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    alerts = []
    with open(ALERT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    alert = json.loads(line)
                    if alert.get("detected_at", "") >= cutoff:
                        alerts.append(alert)
                except (json.JSONDecodeError, KeyError):
                    continue
    
    return alerts


if __name__ == "__main__":
    print("Skill Failure Alert 测试")
    print("=" * 60)
    
    # 检查连续失败
    alerts = check_consecutive_failures(window_size=5)
    
    if not alerts:
        print("✅ 所有 Skill 运行正常，无连续失败")
    else:
        print(f"⚠️ 检测到 {len(alerts)} 个告警：\n")
        for alert in alerts:
            print(format_alert_message(alert))
            print()
    
    # 获取最近 24h 告警
    recent = get_recent_alerts(hours=24)
    print(f"\n📊 最近 24h 告警统计: {len(recent)} 条")
    
    print("\n测试完成！")
