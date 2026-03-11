# -*- coding: utf-8 -*-
"""
Heartbeat Dispatcher Bridge v1.0

作用：把 heartbeat 检查结果转换成 TaskContext，丢给 DecideAndDispatch 走完主链。

这是中枢的第一个真实入口。

设计原则：
- 不改现有 heartbeat 生产链路
- 只消费 heartbeat 已有的检查结果
- 转换成标准 TaskContext 后交给中枢
- 所有决策写入 dispatch_log.jsonl
- 失败时留下 fallback 记录
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from decide_and_dispatch import DecideAndDispatch
from decide_and_dispatch_schema import TaskContext


# ── 事件类型定义 ──────────────────────────────────────────────────────────────

class HeartbeatEventType:
    """heartbeat 可产生的事件类型"""
    HEALTH_CHECK = "health_check"           # 系统健康检查结果
    QUEUE_PROCESSED = "queue_processed"     # 队列处理结果
    ZOMBIE_RECLAIMED = "zombie_reclaimed"   # 僵尸任务回收
    SKILL_FAILURE = "skill_failure"         # 技能连续失败
    EVOLUTION_STALE = "evolution_stale"     # 演化分数过期
    TOKEN_ALERT = "token_alert"            # Token 用量告警


# ── 事件转换器 ────────────────────────────────────────────────────────────────

def health_check_to_context(health: Dict[str, Any]) -> Optional[TaskContext]:
    """
    健康检查结果 → TaskContext
    
    只在健康度异常时生成事件（正常时不产生噪音）
    """
    score = health.get("score", 100)
    
    # 健康度 >= 80 不产生事件
    if score >= 80:
        return None
    
    # 确定优先级和风险
    if score < 60:
        priority = "critical"
        risk_level = "high"
    elif score < 70:
        priority = "high"
        risk_level = "medium"
    else:
        priority = "normal"
        risk_level = "low"
    
    return TaskContext(
        source="heartbeat",
        task_type="monitor",
        content=f"系统健康度异常: {score:.0f}/100 | "
                f"completed={health.get('completed', 0)} "
                f"failed={health.get('failed', 0)} "
                f"pending={health.get('pending', 0)}",
        priority=priority,
        risk_level=risk_level,
        system_state={
            "health_status": "critical" if score < 60 else "degraded" if score < 80 else "healthy",
            "health_score": score,
            "evolution_freshness": health.get("evolution_data_freshness", "unknown"),
        },
        recent_history=[],
        available_handlers=["aios-health-monitor", "pattern-detector", "agent-performance-analyzer"],
    )


def zombie_reclaim_to_context(zombie_result: Dict[str, Any]) -> Optional[TaskContext]:
    """
    僵尸任务回收结果 → TaskContext
    
    只在有回收动作时生成事件
    """
    reclaimed = zombie_result.get("reclaimed", 0)
    if reclaimed == 0:
        return None
    
    permanently_failed = zombie_result.get("permanently_failed", 0)
    
    priority = "high" if permanently_failed > 0 else "normal"
    risk_level = "medium" if permanently_failed > 0 else "low"
    
    return TaskContext(
        source="heartbeat",
        task_type="alert",
        content=f"僵尸任务回收: reclaimed={reclaimed} "
                f"retried={zombie_result.get('retried', 0)} "
                f"permanently_failed={permanently_failed}",
        priority=priority,
        risk_level=risk_level,
        system_state={"health_status": "degraded"},
        recent_history=[],
        available_handlers=["aios-health-monitor", "pattern-detector", "lesson-extractor"],
    )


def skill_failure_to_context(alerts: List[Dict[str, Any]]) -> Optional[TaskContext]:
    """
    技能连续失败告警 → TaskContext
    
    只在有告警时生成事件
    """
    if not alerts:
        return None
    
    # 取最严重的告警
    crit_alerts = [a for a in alerts if a.get("level") == "CRIT"]
    warn_alerts = [a for a in alerts if a.get("level") == "WARN"]
    
    if crit_alerts:
        priority = "critical"
        risk_level = "high"
    else:
        priority = "high"
        risk_level = "medium"
    
    alert_summary = "; ".join(
        f"{a.get('skill', '?')} ({a.get('level', '?')}, {a.get('consecutive_failures', 0)} failures)"
        for a in alerts[:5]
    )
    
    return TaskContext(
        source="heartbeat",
        task_type="alert",
        content=f"技能连续失败: {alert_summary}",
        priority=priority,
        risk_level=risk_level,
        system_state={"health_status": "degraded"},
        recent_history=[],
        available_handlers=["pattern-detector", "lesson-extractor", "aios-health-monitor"],
    )


def evolution_stale_to_context(guard_result: Dict[str, Any]) -> Optional[TaskContext]:
    """
    演化分数过期 → TaskContext
    
    只在数据过期且重算失败时生成事件
    """
    if guard_result.get("freshness") != "stale":
        return None
    
    return TaskContext(
        source="heartbeat",
        task_type="monitor",
        content=f"演化分数数据过期: score={guard_result.get('evolution_score', 0):.1f} "
                f"age={guard_result.get('age_hours', 0):.1f}h",
        priority="normal",
        risk_level="low",
        system_state={
            "health_status": "degraded",
            "evolution_freshness": "stale",
        },
        recent_history=[],
        available_handlers=["aios-health-monitor"],
    )


def token_alert_to_context(alert: Dict[str, Any]) -> Optional[TaskContext]:
    """
    Token 用量告警 → TaskContext
    """
    if not alert:
        return None
    
    level = alert.get("level", "warn")
    priority = "critical" if level == "crit" else "high"
    risk_level = "medium"
    
    return TaskContext(
        source="heartbeat",
        task_type="alert",
        content=f"Token 用量告警: {alert.get('title', '')} - {alert.get('body', '')}",
        priority=priority,
        risk_level=risk_level,
        system_state={"health_status": "degraded"},
        recent_history=[],
        available_handlers=["aios-health-monitor"],
    )


# ── 桥接器主类 ────────────────────────────────────────────────────────────────

class HeartbeatDispatcherBridge:
    """
    Heartbeat → DecideAndDispatch 桥接器
    
    收集 heartbeat 各阶段的检查结果，转换成 TaskContext，
    统一丢给中枢走 router → policy → dispatch 主链。
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, dispatcher: Optional[DecideAndDispatch] = None):
        self.dispatcher = dispatcher or DecideAndDispatch()
        self._events: List[Dict[str, Any]] = []
        self._results: List[Dict[str, Any]] = []
    
    def collect_health_check(self, health: Dict[str, Any]):
        """收集健康检查结果"""
        ctx = health_check_to_context(health)
        if ctx:
            self._events.append({
                "type": HeartbeatEventType.HEALTH_CHECK,
                "context": ctx,
                "raw": health,
            })
    
    def collect_zombie_reclaim(self, zombie_result: Dict[str, Any]):
        """收集僵尸回收结果"""
        ctx = zombie_reclaim_to_context(zombie_result)
        if ctx:
            self._events.append({
                "type": HeartbeatEventType.ZOMBIE_RECLAIMED,
                "context": ctx,
                "raw": zombie_result,
            })
    
    def collect_skill_failure(self, alerts: List[Dict[str, Any]]):
        """收集技能失败告警"""
        ctx = skill_failure_to_context(alerts)
        if ctx:
            self._events.append({
                "type": HeartbeatEventType.SKILL_FAILURE,
                "context": ctx,
                "raw": alerts,
            })
    
    def collect_evolution_stale(self, guard_result: Dict[str, Any]):
        """收集演化分数过期"""
        ctx = evolution_stale_to_context(guard_result)
        if ctx:
            self._events.append({
                "type": HeartbeatEventType.EVOLUTION_STALE,
                "context": ctx,
                "raw": guard_result,
            })
    
    def collect_token_alert(self, alert: Dict[str, Any]):
        """收集 Token 告警"""
        ctx = token_alert_to_context(alert)
        if ctx:
            self._events.append({
                "type": HeartbeatEventType.TOKEN_ALERT,
                "context": ctx,
                "raw": alert,
            })
    
    def dispatch_all(self) -> List[Dict[str, Any]]:
        """
        把所有收集到的事件统一派发给中枢
        
        Returns:
            每个事件的派发结果列表
        """
        if not self._events:
            return []
        
        self._results = []
        
        for event in self._events:
            try:
                decision = self.dispatcher.process_and_log(event["context"])
                explanation = self.dispatcher.explain_decision(decision.decision_record)
                
                self._results.append({
                    "event_type": event["type"],
                    "status": decision.decision_record.final_status,
                    "handler": decision.decision_record.chosen_handler,
                    "explanation": explanation,
                    "timestamp": decision.timestamp,
                    "success": True,
                })
            except Exception as e:
                self._results.append({
                    "event_type": event["type"],
                    "status": "error",
                    "handler": None,
                    "explanation": f"中枢处理异常: {e}",
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                })
        
        return self._results
    
    def get_summary(self) -> str:
        """生成本轮派发摘要"""
        if not self._results:
            return "   无事件需要中枢处理"
        
        lines = []
        for r in self._results:
            status_icon = {
                "dispatched": "✅",
                "degraded": "⬇️",
                "blocked": "🚫",
                "failed": "❌",
                "error": "💥",
            }.get(r["status"], "❓")
            
            handler_text = f" → {r['handler']}" if r["handler"] else ""
            lines.append(f"   {status_icon} [{r['event_type']}]{handler_text} ({r['status']})")
        
        return "\n".join(lines)
    
    def get_event_count(self) -> int:
        """返回收集到的事件数"""
        return len(self._events)
    
    def reset(self):
        """重置状态（下一轮心跳前调用）"""
        self._events = []
        self._results = []


# ── 测试入口 ──────────────────────────────────────────────────────────────────

def main():
    """独立测试"""
    bridge = HeartbeatDispatcherBridge()
    
    # 模拟 heartbeat 检查结果
    bridge.collect_health_check({
        "score": 65.0,
        "total_tasks": 20,
        "completed": 12,
        "failed": 5,
        "pending": 3,
        "finished": 17,
        "evolution_data_freshness": "fresh",
    })
    
    bridge.collect_zombie_reclaim({
        "reclaimed": 2,
        "retried": 1,
        "permanently_failed": 1,
    })
    
    bridge.collect_skill_failure([
        {"skill": "api-testing-skill", "level": "CRIT", "consecutive_failures": 5},
        {"skill": "pdf-skill", "level": "WARN", "consecutive_failures": 3},
    ])
    
    # 派发
    results = bridge.dispatch_all()
    
    print("[DISPATCH_BRIDGE] Heartbeat → 中枢 派发结果:")
    print(bridge.get_summary())
    print()
    
    # 打印详细解释
    for r in results:
        print(f"--- {r['event_type']} ---")
        print(r["explanation"])
        print()


if __name__ == "__main__":
    main()
