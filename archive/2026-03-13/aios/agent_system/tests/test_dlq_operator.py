#!/usr/bin/env python3
"""
Unit tests for dlq_operator.py
"""

import json
import pytest
from pathlib import Path
from dlq import enqueue_dead_letter, DLQ_FILE, DLQ_AUDIT_FILE
from dlq_operator import replay, discard


@pytest.fixture(autouse=True)
def cleanup_dlq():
    """每个测试前清理 DLQ 文件"""
    if DLQ_FILE.exists():
        DLQ_FILE.unlink()
    if DLQ_AUDIT_FILE.exists():
        DLQ_AUDIT_FILE.unlink()
    yield
    if DLQ_FILE.exists():
        DLQ_FILE.unlink()
    if DLQ_AUDIT_FILE.exists():
        DLQ_AUDIT_FILE.unlink()


class TestDLQOperator:
    def test_replay_success(self):
        """测试 replay 成功"""
        # 先入队
        enqueue_dead_letter("test-001", 3, "timeout", "timeout")
        
        # replay
        result = replay("test-001", operator="test")
        assert result["success"] is True
        assert "replayed" in result["message"]
        
        # 验证审计日志
        with open(DLQ_AUDIT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 第一行是 enqueue，第二行是 replay
            audit = json.loads(lines[-1])
            assert audit["action"] == "replay"
            assert audit["task_id"] == "test-001"
            assert audit["operator"] == "test"
    
    def test_replay_not_found(self):
        """测试 replay 不存在的 task_id"""
        result = replay("nonexistent", operator="test")
        assert result["success"] is False
        assert "not found" in result["message"]
    
    def test_replay_idempotent(self):
        """测试重复 replay（no-op）"""
        enqueue_dead_letter("test-002", 3, "timeout", "timeout")
        
        # 第一次 replay
        result1 = replay("test-002", operator="test")
        assert result1["success"] is True
        
        # 第二次 replay（应该 no-op）
        result2 = replay("test-002", operator="test")
        assert result2["success"] is False
        assert "already replayed" in result2["message"]
    
    def test_discard_success(self):
        """测试 discard 成功"""
        enqueue_dead_letter("test-003", 3, "logic error", "logic_error")
        
        result = discard("test-003", reason="not fixable", operator="test")
        assert result["success"] is True
        assert "discarded" in result["message"]
        
        # 验证审计日志
        with open(DLQ_AUDIT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            audit = json.loads(lines[-1])
            assert audit["action"] == "discard"
            assert audit["task_id"] == "test-003"
            assert audit["reason"] == "not fixable"
    
    def test_discard_idempotent(self):
        """测试重复 discard（no-op）"""
        enqueue_dead_letter("test-004", 3, "error", "unknown")
        
        # 第一次 discard
        result1 = discard("test-004", reason="test", operator="test")
        assert result1["success"] is True
        
        # 第二次 discard（应该 no-op）
        result2 = discard("test-004", reason="test", operator="test")
        assert result2["success"] is False
        assert "already discarded" in result2["message"]
    
    def test_audit_log_format(self):
        """测试审计日志格式"""
        enqueue_dead_letter("test-005", 3, "error", "timeout")
        replay("test-005", operator="human")
        
        with open(DLQ_AUDIT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            audit = json.loads(lines[-1])
            
            # 验证必需字段
            assert "action" in audit
            assert "task_id" in audit
            assert "operator" in audit
            assert "timestamp" in audit
            assert "reason" in audit  # replay 时为 None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
