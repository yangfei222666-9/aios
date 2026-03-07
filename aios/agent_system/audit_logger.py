# audit_logger.py - AIOS 审计日志系统
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock

_AUDIT_LOCK = Lock()
_AUDIT_DIR = Path(__file__).parent / "audit_logs"


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _today_path():
    _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _AUDIT_DIR / f"{day}.jsonl"


def _safe_shrink(value, max_len=4000):
    """截断过长内容，防止日志爆炸"""
    if value is None:
        return None
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    if len(s) <= max_len:
        return value
    return {
        "_truncated": True,
        "preview": s[:max_len],
        "original_length": len(s),
    }


def audit_event(
    *,
    agent_id: str,
    session_id: str,
    action_type: str,
    target: str,
    params=None,
    result: str = "unknown",
    exit_code: int | None = None,
    duration_ms: int | None = None,
    risk_level: str = "medium",
    reason: str | None = None,
    source_task_id: str | None = None,
    lesson_id: str | None = None,
    spawn_id: str | None = None,
    extra=None,
) -> str:
    """
    记录审计事件到 audit_logs/YYYY-MM-DD.jsonl
    
    Args:
        agent_id: Agent ID
        session_id: Session ID
        action_type: 事件类型（file.read/write/delete, command.exec, spawn.*, policy.*）
        target: 操作目标（文件路径、命令、spawn_id等）
        params: 参数字典
        result: 结果（success/failed/rejected/killed）
        exit_code: 命令退出码
        duration_ms: 执行耗时（毫秒）
        risk_level: 风险等级（low/medium/high/critical）
        reason: 原因说明
        source_task_id: 源任务ID
        lesson_id: 教训ID
        spawn_id: Spawn ID
        extra: 额外信息
    
    Returns:
        audit_id: 审计事件ID
    """
    record = {
        "timestamp": utc_now_iso(),
        "audit_id": f"aud_{uuid.uuid4().hex}",
        "agent_id": agent_id,
        "session_id": session_id,
        "action_type": action_type,
        "target": _safe_shrink(target, 2000),
        "params": _safe_shrink(params, 4000),
        "result": result,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "risk_level": risk_level,
        "reason": reason,
        "source_task_id": source_task_id,
        "lesson_id": lesson_id,
        "spawn_id": spawn_id,
        "extra": _safe_shrink(extra, 4000),
    }

    path = _today_path()
    line = json.dumps(record, ensure_ascii=False, default=str)

    with _AUDIT_LOCK:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    return record["audit_id"]


# 便捷查询函数
def query_audit_logs(
    *,
    action_type: str | None = None,
    agent_id: str | None = None,
    lesson_id: str | None = None,
    spawn_id: str | None = None,
    risk_level: str | None = None,
    result: str | None = None,
    days: int = 7,
):
    """
    查询审计日志
    
    Args:
        action_type: 过滤事件类型
        agent_id: 过滤 Agent ID
        lesson_id: 过滤教训ID
        spawn_id: 过滤 Spawn ID
        risk_level: 过滤风险等级
        result: 过滤结果
        days: 查询最近N天
    
    Returns:
        匹配的审计记录列表
    """
    results = []
    for i in range(days):
        date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        path = _AUDIT_DIR / f"{date}.jsonl"
        if not path.exists():
            continue
        
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if action_type and record.get("action_type") != action_type:
                        continue
                    if agent_id and record.get("agent_id") != agent_id:
                        continue
                    if lesson_id and record.get("lesson_id") != lesson_id:
                        continue
                    if spawn_id and record.get("spawn_id") != spawn_id:
                        continue
                    if risk_level and record.get("risk_level") != risk_level:
                        continue
                    if result and record.get("result") != result:
                        continue
                    results.append(record)
                except json.JSONDecodeError:
                    continue
    
    return results


if __name__ == "__main__":
    # 测试
    from datetime import timedelta
    
    audit_id = audit_event(
        agent_id="test-agent",
        session_id="test-session",
        action_type="command.exec",
        target="python test.py",
        params={"cwd": "/workspace", "timeout_sec": 60},
        result="success",
        exit_code=0,
        duration_ms=1234,
        risk_level="medium",
        reason="test run",
    )
    print(f"[OK] Audit event recorded: {audit_id}")
    
    # 查询测试
    logs = query_audit_logs(action_type="command.exec", days=1)
    print(f"[OK] Found {len(logs)} command.exec events")
