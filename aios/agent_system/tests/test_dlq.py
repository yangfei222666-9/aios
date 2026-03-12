#!/usr/bin/env python3
"""
Unit tests for dlq.py
"""

import json
import pytest
from pathlib import Path
from dlq import (
    enqueue_dead_letter,
    get_dlq_size,
    get_dlq_entries,
    DLQ_FILE,
    DLQ_AUDIT_FILE
)


@pytest.fixture(autouse=True)
def cleanup_dlq():
    """每个测试前清理 DLQ 文件"""
    if DLQ_FILE.exists():
        DLQ_FILE.unlink()
    if DLQ_AUDIT_FILE.exists():
        DLQ_AUDIT_FILE.unlink()
    yield
    # 测试后清理
    if DLQ_FILE.exists():
        DLQ_FILE.unlink()
    if DLQ_AUDIT_FILE.exists():
        DLQ_AUDIT_FILE.unlink()


class TestDLQ:
    def test_enqueue_success(self):
        """测试成功写入 DLQ"""
        success = enqueue_dead_letter(
            task_id="test-001",
            attempts=3,
            last_error="timeout after 120s",
            error_type="timeout"
        )
        assert success is True
        assert DLQ_FILE.exists()
        assert DLQ_AUDIT_FILE.exists()
        
        # 验证文件内容
        with open(DLQ_FILE, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline())
            assert entry["task_id"] == "test-001"
            assert entry["attempts"] == 3
            assert entry["error_type"] == "timeout"
            assert entry["status"] == "pending_review"
    
    def test_idempotent_enqueue(self):
        """测试幂等性：同一任务不重复写入"""
        # 第一次写入
        success1 = enqueue_dead_letter(
            task_id="test-002",
            attempts=3,
            last_error="error 1",
            error_type="timeout"
        )
        assert success1 is True
        
        # 第二次写入（应该被拒绝）
        success2 = enqueue_dead_letter(
            task_id="test-002",
            attempts=5,
            last_error="error 2",
            error_type="dependency_error"
        )
        assert success2 is False
        
        # 验证只有一条记录
        assert get_dlq_size() == 1
    
    def test_get_dlq_size(self):
        """测试获取 DLQ 大小"""
        assert get_dlq_size() == 0
        
        enqueue_dead_letter("test-003", 3, "error 1", "timeout")
        assert get_dlq_size() == 1
        
        enqueue_dead_letter("test-004", 3, "error 2", "logic_error")
        assert get_dlq_size() == 2
    
    def test_get_dlq_entries(self):
        """测试获取 DLQ 条目"""
        enqueue_dead_letter("test-005", 3, "error 1", "timeout")
        enqueue_dead_letter("test-006", 2, "error 2", "dependency_error")
        
        entries = get_dlq_entries()
        assert len(entries) == 2
        assert entries[0]["task_id"] == "test-005"
        assert entries[1]["task_id"] == "test-006"
    
    def test_audit_log_created(self):
        """测试审计日志创建"""
        enqueue_dead_letter("test-007", 3, "error", "timeout")
        
        assert DLQ_AUDIT_FILE.exists()
        with open(DLQ_AUDIT_FILE, "r", encoding="utf-8") as f:
            audit = json.loads(f.readline())
            assert audit["action"] == "enqueue"
            assert audit["task_id"] == "test-007"
            assert audit["operator"] == "system"
    
    def test_metadata_preserved(self):
        """测试元数据保留"""
        metadata = {"agent": "coder", "priority": "high"}
        enqueue_dead_letter(
            task_id="test-008",
            attempts=3,
            last_error="error",
            error_type="timeout",
            metadata=metadata
        )
        
        entries = get_dlq_entries()
        assert entries[0]["metadata"] == metadata
    
    def test_empty_dlq(self):
        """测试空 DLQ"""
        assert get_dlq_size() == 0
        assert get_dlq_entries() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
