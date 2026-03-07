# audit_context.py - 审计上下文透传
from contextvars import ContextVar

_agent_id = ContextVar("agent_id", default="unknown-agent")
_session_id = ContextVar("session_id", default="unknown-session")


def set_audit_context(agent_id: str, session_id: str):
    """设置当前审计上下文"""
    _agent_id.set(agent_id)
    _session_id.set(session_id)


def get_agent_id() -> str:
    """获取当前 Agent ID"""
    return _agent_id.get()


def get_session_id() -> str:
    """获取当前 Session ID"""
    return _session_id.get()


# 便捷包装：自动从上下文获取 agent_id/session_id
def audit_event_auto(**kwargs):
    """
    自动从上下文获取 agent_id/session_id 的审计事件记录
    
    用法：
        set_audit_context("coder-agent", "sess_123")
        audit_event_auto(
            action_type="file.write",
            target="output.txt",
            result="success",
        )
    """
    from audit_logger import audit_event
    
    return audit_event(
        agent_id=kwargs.pop("agent_id", get_agent_id()),
        session_id=kwargs.pop("session_id", get_session_id()),
        **kwargs
    )


if __name__ == "__main__":
    # 测试
    set_audit_context("test-agent", "test-session")
    print(f"[OK] Agent ID: {get_agent_id()}")
    print(f"[OK] Session ID: {get_session_id()}")
    
    audit_event_auto(
        action_type="test.event",
        target="test-target",
        result="success",
    )
    print("[OK] Audit event recorded with auto context")
