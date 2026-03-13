#!/usr/bin/env python3
"""
Unit tests for executor_fallback.py
"""

import json
import pytest
from pathlib import Path
from executor_fallback import (
    handle_timeout,
    FALLBACK_AUDIT_FILE,
    DEFAULT_FALLBACK_MAP,
)
from spawn_lock import get_lock_store, try_acquire_spawn_lock


@pytest.fixture(autouse=True)
def cleanup():
    """每个测试前清理文件"""
    store = get_lock_store()
    store.lock_file.unlink(missing_ok=True)
    metrics_file = Path(__file__).parent.parent / "spawn_lock_metrics.json"
    metrics_file.unlink(missing_ok=True)
    FALLBACK_AUDIT_FILE.unlink(missing_ok=True)
    spawn_file = Path(__file__).parent.parent / "spawn_requests.jsonl"
    spawn_file.unlink(missing_ok=True)
    yield
    store.lock_file.unlink(missing_ok=True)
    metrics_file.unlink(missing_ok=True)
    FALLBACK_AUDIT_FILE.unlink(missing_ok=True)
    spawn_file.unlink(missing_ok=True)


class TestExecutorFallback:
    def test_normal_timeout_fallback_triggered(self):
        """测试 1: 正常超时 → force_release 成功 → fallback 拿锁成功 → 任务完成"""
        result = handle_timeout(
            task_id="test-001",
            original_executor_id="coder-dispatcher",
        )
        
        assert result["success"] is True
        assert result["action"] == "fallback_triggered"
        assert result["fallback_executor_id"] == "analyst-dispatcher"
        assert result["lock_token"] is not None
        
        # 验证审计日志
        with open(FALLBACK_AUDIT_FILE, "r", encoding="utf-8") as f:
            audit = json.loads(f.readline())
            assert audit["action"] == "fallback_triggered"
            assert audit["task_id"] == "test-001"
            assert audit["original_executor"] == "coder-dispatcher"
            assert audit["fallback_executor"] == "analyst-dispatcher"
        
        # 验证 spawn 请求
        spawn_file = Path(__file__).parent.parent / "spawn_requests.jsonl"
        assert spawn_file.exists()
        with open(spawn_file, "r", encoding="utf-8") as f:
            spawn_req = json.loads(f.readline())
            assert spawn_req["task_id"] == "test-001"
            assert spawn_req["agent_id"] == "analyst-dispatcher"
            assert spawn_req["is_fallback"] is True
    
    def test_fallback_lock_acquire_failed(self):
        """测试 3: fallback 拿锁失败（原 executor 复活）→ fallback 退出 → 无双写
        
        模拟场景：
        1. force_release 释放了原锁
        2. 原 executor 在 force_release 和 fallback acquire 之间复活，重新拿锁
        3. fallback acquire 失败 → 退出，无双写
        """
        task = {"id": "test-002"}
        
        # 模拟：在 force_release 之后、fallback acquire 之前，原 executor 复活
        # 通过 monkeypatch force_release_spawn_lock，让它释放后立刻被原 executor 重新拿锁
        import executor_fallback as fb_module
        original_force_release = fb_module.force_release_spawn_lock
        
        def mock_force_release(t):
            # 先真正释放
            result = original_force_release(t)
            # 然后模拟原 executor 复活，重新拿锁（用相同的 task）
            try_acquire_spawn_lock(t)
            return result
        
        fb_module.force_release_spawn_lock = mock_force_release
        
        try:
            result = handle_timeout(
                task_id="test-002",
                original_executor_id="coder-dispatcher",
                task=task,
            )
        finally:
            fb_module.force_release_spawn_lock = original_force_release
        
        assert result["success"] is False
        assert result["action"] == "fallback_skipped"
        assert "original executor may have recovered" in result["message"]
        
        # 验证审计日志
        with open(FALLBACK_AUDIT_FILE, "r", encoding="utf-8") as f:
            audit = json.loads(f.readline())
            assert audit["action"] == "fallback_skipped"
    
    def test_fallback_disabled(self):
        """测试 4: fallback_enabled=false → 只记日志"""
        import os
        os.environ["FALLBACK_ENABLED"] = "false"
        
        # 重新导入以应用环境变量
        import importlib
        import executor_fallback
        importlib.reload(executor_fallback)
        
        result = executor_fallback.handle_timeout(
            task_id="test-003",
            original_executor_id="coder-dispatcher",
        )
        
        assert result["success"] is False
        assert result["action"] == "fallback_disabled"
        
        # 恢复环境变量
        os.environ["FALLBACK_ENABLED"] = "true"
        importlib.reload(executor_fallback)
    
    def test_no_fallback_defined(self):
        """测试：没有定义 fallback executor → 返回 error"""
        result = handle_timeout(
            task_id="test-004",
            original_executor_id="unknown-executor",
        )
        
        assert result["success"] is False
        assert result["action"] == "error"
        assert "no fallback defined" in result["message"]
    
    def test_custom_fallback_executor(self):
        """测试：指定自定义 fallback executor"""
        result = handle_timeout(
            task_id="test-005",
            original_executor_id="coder-dispatcher",
            fallback_executor_id="custom-executor",
        )
        
        assert result["success"] is True
        assert result["fallback_executor_id"] == "custom-executor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
