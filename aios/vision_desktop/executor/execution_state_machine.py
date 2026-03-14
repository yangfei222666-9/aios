"""
execution_state_machine.py - 执行状态机
职责：管理执行链的状态流转
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time


class State(Enum):
    """执行状态"""
    IDLE = "idle"                      # 空闲
    CONFIRMING = "confirming"          # 确认中（门控检查）
    PENDING = "pending"                # 待人工确认（v0.1 中 pending 专指此状态）
    EXECUTING = "executing"            # 执行中
    VERIFYING = "verifying"            # 验证中
    RETRY = "retry"                    # 重试中
    BLOCKED = "blocked"                # 已拦截
    DONE = "done"                      # 已完成


class Event(Enum):
    """状态转换事件"""
    PERCEPTION_DONE = "perception_done"
    GUARD_ALLOW = "guard_allow"
    GUARD_PENDING = "guard_pending"
    GUARD_BLOCKED = "guard_blocked"
    USER_CONFIRM = "user_confirm"
    USER_REJECT = "user_reject"
    EXEC_DONE = "exec_done"
    VERIFY_SUCCESS = "verify_success"
    VERIFY_NO_CHANGE = "verify_no_change"
    VERIFY_UNEXPECTED = "verify_unexpected"
    RETRY_EXHAUSTED = "retry_exhausted"


@dataclass
class ExecutionContext:
    """执行上下文"""
    task_desc: str
    action: Any  # Action 对象
    confidence: float
    retry_count: int = 0
    max_retries: int = 2
    blocked_reason: str = ""
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class ExecutionStateMachine:
    """执行状态机"""
    
    # 状态转换表
    TRANSITIONS = {
        State.IDLE: {
            Event.PERCEPTION_DONE: State.CONFIRMING
        },
        State.CONFIRMING: {
            Event.GUARD_ALLOW: State.EXECUTING,
            Event.GUARD_PENDING: State.PENDING,
            Event.GUARD_BLOCKED: State.BLOCKED
        },
        State.PENDING: {
            Event.USER_CONFIRM: State.EXECUTING,
            Event.USER_REJECT: State.BLOCKED
        },
        State.EXECUTING: {
            Event.EXEC_DONE: State.VERIFYING
        },
        State.VERIFYING: {
            Event.VERIFY_SUCCESS: State.DONE,
            Event.VERIFY_NO_CHANGE: State.RETRY,
            Event.VERIFY_UNEXPECTED: State.BLOCKED
        },
        State.RETRY: {
            Event.EXEC_DONE: State.VERIFYING,
            Event.RETRY_EXHAUSTED: State.PENDING
        }
    }
    
    def __init__(self):
        self.current_state = State.IDLE
        self.context: Optional[ExecutionContext] = None
        self.history = []  # 状态转换历史
    
    def start(self, task_desc: str, action: Any, confidence: float):
        """开始新的执行流程"""
        self.current_state = State.IDLE
        self.context = ExecutionContext(
            task_desc=task_desc,
            action=action,
            confidence=confidence
        )
        self.history = [(State.IDLE, time.time())]
    
    def transition(self, event: Event, reason: str = "") -> bool:
        """
        状态转换
        
        Args:
            event: 触发事件
            reason: 转换原因（用于 blocked 等状态）
        
        Returns:
            是否转换成功
        """
        if self.current_state not in self.TRANSITIONS:
            return False
        
        allowed_events = self.TRANSITIONS[self.current_state]
        if event not in allowed_events:
            return False
        
        # 执行转换
        old_state = self.current_state
        new_state = allowed_events[event]
        self.current_state = new_state
        
        # 记录历史
        self.history.append((new_state, time.time()))
        
        # 特殊处理
        if new_state == State.BLOCKED and reason:
            self.context.blocked_reason = reason
        
        if new_state == State.RETRY:
            self.context.retry_count += 1
        
        print(f"[STATE] {old_state.value} --[{event.value}]--> {new_state.value}")
        
        return True
    
    def can_retry(self) -> bool:
        """是否可以重试"""
        if self.context is None:
            return False
        return self.context.retry_count < self.context.max_retries
    
    def get_state(self) -> State:
        """获取当前状态"""
        return self.current_state
    
    def is_terminal(self) -> bool:
        """是否到达终态"""
        return self.current_state in [State.DONE, State.BLOCKED]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if self.context is None:
            return {"state": "idle", "context": None}
        
        return {
            "state": self.current_state.value,
            "task": self.context.task_desc,
            "confidence": self.context.confidence,
            "retry_count": self.context.retry_count,
            "blocked_reason": self.context.blocked_reason,
            "duration": time.time() - self.context.timestamp,
            "history": [(s.value, t) for s, t in self.history]
        }


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    from dataclasses import dataclass
    
    @dataclass
    class MockAction:
        type: str
        params: dict
    
    # 初始化
    sm = ExecutionStateMachine()
    
    # 场景 1：正常流程（allow → execute → verify → done）
    print("\n场景 1：正常流程")
    print("-" * 60)
    
    sm.start("点击登录按钮", MockAction("click", {"x": 100, "y": 200}), 0.9)
    sm.transition(Event.PERCEPTION_DONE)
    sm.transition(Event.GUARD_ALLOW)
    sm.transition(Event.EXEC_DONE)
    sm.transition(Event.VERIFY_SUCCESS)
    
    print(f"\n最终状态: {sm.get_state().value}")
    print(f"是否终态: {sm.is_terminal()}")
    
    # 场景 2：需要人工确认（pending → user_confirm → execute → done）
    print("\n\n场景 2：需要人工确认")
    print("-" * 60)
    
    sm.start("输入密码", MockAction("type", {"text": "***"}), 0.75)
    sm.transition(Event.PERCEPTION_DONE)
    sm.transition(Event.GUARD_PENDING)
    sm.transition(Event.USER_CONFIRM)
    sm.transition(Event.EXEC_DONE)
    sm.transition(Event.VERIFY_SUCCESS)
    
    print(f"\n最终状态: {sm.get_state().value}")
    
    # 场景 3：验证失败 → 重试 → 最终 pending
    print("\n\n场景 3：验证失败重试")
    print("-" * 60)
    
    sm.start("点击按钮", MockAction("click", {"x": 100, "y": 200}), 0.85)
    sm.transition(Event.PERCEPTION_DONE)
    sm.transition(Event.GUARD_ALLOW)
    sm.transition(Event.EXEC_DONE)
    sm.transition(Event.VERIFY_NO_CHANGE)  # 第一次失败
    
    if sm.can_retry():
        sm.transition(Event.EXEC_DONE)
        sm.transition(Event.VERIFY_NO_CHANGE)  # 第二次失败
    
    if sm.can_retry():
        sm.transition(Event.EXEC_DONE)
        sm.transition(Event.VERIFY_NO_CHANGE)  # 第三次失败
    else:
        sm.transition(Event.RETRY_EXHAUSTED)
    
    print(f"\n最终状态: {sm.get_state().value}")
    print(f"重试次数: {sm.context.retry_count}")
    
    # 场景 4：高风险拦截
    print("\n\n场景 4：高风险拦截")
    print("-" * 60)
    
    sm.start("点击删除按钮", MockAction("click", {"x": 100, "y": 200}), 0.95)
    sm.transition(Event.PERCEPTION_DONE)
    sm.transition(Event.GUARD_BLOCKED, reason="高风险操作")
    
    print(f"\n最终状态: {sm.get_state().value}")
    print(f"拦截原因: {sm.context.blocked_reason}")
    
    # 打印摘要
    print("\n\n执行摘要:")
    print("-" * 60)
    summary = sm.get_summary()
    for key, value in summary.items():
        if key != "history":
            print(f"{key}: {value}")
