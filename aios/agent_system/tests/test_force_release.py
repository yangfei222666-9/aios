#!/usr/bin/env python3
"""
Unit tests for spawn_lock.force_release
"""

import pytest
from spawn_lock import (
    try_acquire_spawn_lock,
    force_release_spawn_lock,
    get_lock_store,
    idem_key
)


@pytest.fixture(autouse=True)
def cleanup_locks():
    """每个测试前清理锁文件"""
    store = get_lock_store()
    store.lock_file.unlink(missing_ok=True)
    from pathlib import Path
    metrics_file = Path(__file__).parent.parent / "spawn_lock_metrics.json"
    metrics_file.unlink(missing_ok=True)
    yield
    store.lock_file.unlink(missing_ok=True)
    metrics_file.unlink(missing_ok=True)


class TestForceRelease:
    def test_force_release_existing_lock(self):
        """测试强制释放已存在的锁"""
        task = {"id": "test-001"}
        
        # 获取锁
        token = try_acquire_spawn_lock(task)
        assert token is not None
        
        # 强制释放（不需要 token）
        success = force_release_spawn_lock(task)
        assert success is True
        
        # 验证锁已释放（可以重新获取）
        token2 = try_acquire_spawn_lock(task)
        assert token2 is not None
    
    def test_force_release_nonexistent_lock(self):
        """测试强制释放不存在的锁（幂等保证）"""
        task = {"id": "test-002"}
        
        # 直接强制释放（锁不存在）
        success = force_release_spawn_lock(task)
        assert success is True  # 幂等：不存在也返回 True
    
    def test_force_release_metrics(self):
        """测试强制释放计数"""
        task = {"id": "test-003"}
        
        # 获取锁
        token = try_acquire_spawn_lock(task)
        assert token is not None
        
        # 强制释放
        force_release_spawn_lock(task)
        
        # 验证指标
        store = get_lock_store()
        metrics = store._metrics
        assert metrics.get("force_release_total", 0) >= 1
    
    def test_force_release_vs_normal_release(self):
        """测试 force_release 和 normal release 的区别"""
        task = {"id": "test-004"}
        
        # 获取锁
        token = try_acquire_spawn_lock(task)
        assert token is not None
        
        # 尝试用错误的 token 释放（应该失败）
        store = get_lock_store()
        key = idem_key(task)
        success = store.release(key, "wrong-token")
        assert success is False
        
        # 强制释放（不校验 token，应该成功）
        success = force_release_spawn_lock(task)
        assert success is True
        
        # 验证锁已释放
        token2 = try_acquire_spawn_lock(task)
        assert token2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
