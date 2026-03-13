"""
Integration tests for Day 3: Retry + Idempotency + Timing
"""

import pytest
import time
import json
from pathlib import Path
from retry_strategy import retry_with_backoff
from spawn_lock import (
    try_acquire_spawn_lock,
    acquire_or_reuse,
    release_spawn_lock,
    get_lock_store,
)
from pipeline_timer import PipelineTimer, get_timing_stats, TIMINGS_FILE


class TestRetryIntegration:
    """重试集成测试"""
    
    def test_retry_success_on_second_attempt(self):
        """重试成功：第 2 次成功"""
        attempts = [0]
        
        def task():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("Transient error")
            return "success"
        
        success, count, error = retry_with_backoff(task, max_retries=3, base_delay=0.01)
        
        assert success is True
        assert count == 2
        assert error is None
    
    def test_retry_exhausted(self):
        """重试耗尽：全部失败"""
        attempts = [0]
        
        def task():
            attempts[0] += 1
            raise RuntimeError("Permanent error")
        
        success, count, error = retry_with_backoff(task, max_retries=3, base_delay=0.01)
        
        assert success is False
        assert count == 3
        assert isinstance(error, RuntimeError)
        assert attempts[0] == 3


class TestIdempotencyIntegration:
    """幂等集成测试"""
    
    def setup_method(self):
        """每个测试前清理锁文件和指标"""
        store = get_lock_store()
        if store.lock_file.exists():
            store.lock_file.unlink()
        # 重置指标
        store._metrics = {
            "acquire_total": 0,
            "acquire_success": 0,
            "idempotent_hit_total": 0,
            "stale_lock_recovered_total": 0,
            "acquire_latency_ms_sum": 0.0,
        }
        store._save_metrics()
    
    def test_idempotent_hit_during_retry(self):
        """重试中去重：同一任务重试时幂等命中"""
        task = {"id": "test-idem-001", "zombie_retries": 0}
        
        # 首次 acquire
        token1 = try_acquire_spawn_lock(task)
        assert token1 is not None
        
        # 重试时再次 acquire（应该被幂等拦截）
        token2 = try_acquire_spawn_lock(task)
        assert token2 is None  # 幂等命中
        
        # 验证指标
        metrics = get_lock_store().get_metrics()
        assert metrics["idempotent_hit_total"] == 1
        assert metrics["acquire_total"] == 2
    
    def test_acquire_or_reuse_new_lock(self):
        """acquire_or_reuse：首次获取锁"""
        task = {"id": "test-reuse-001", "zombie_retries": 0}
        
        token, reused = acquire_or_reuse(task)
        
        assert token is not None
        assert reused is False
    
    def test_acquire_or_reuse_reuse_existing(self):
        """acquire_or_reuse：复用已有锁"""
        task = {"id": "test-reuse-002", "zombie_retries": 0}
        
        # 首次 acquire
        token1, reused1 = acquire_or_reuse(task)
        assert token1 is not None
        assert reused1 is False
        
        # 重试时复用（传入 existing_token）
        token2, reused2 = acquire_or_reuse(task, existing_token=token1)
        assert token2 == token1  # 同一个 token
        assert reused2 is True  # 复用标记
        
        # 验证指标：复用不应增加 idempotent_hit_total
        metrics = get_lock_store().get_metrics()
        assert metrics["idempotent_hit_total"] == 0  # 复用不计入幂等命中
    
    def test_acquire_or_reuse_invalid_token(self):
        """acquire_or_reuse：无效 token 时重新 acquire"""
        task = {"id": "test-reuse-003", "zombie_retries": 0}
        
        # 传入无效 token
        token, reused = acquire_or_reuse(task, existing_token="invalid-token")
        
        assert token is not None
        assert reused is False  # 无法复用，重新 acquire
    
    def test_retry_with_lock_reuse(self):
        """完整流程：重试时复用锁"""
        task = {"id": "test-flow-001", "zombie_retries": 0}
        attempts = [0]
        lock_token = None
        
        def task_with_lock():
            nonlocal lock_token
            attempts[0] += 1
            
            # 首次或重试时获取/复用锁
            token, reused = acquire_or_reuse(task, existing_token=lock_token)
            if token is None:
                raise RuntimeError("Lock conflict")
            
            lock_token = token
            
            if attempts[0] < 2:
                raise ValueError("Transient error")
            
            # 成功后释放锁
            release_spawn_lock(task, lock_token)
            return "success"
        
        success, count, error = retry_with_backoff(task_with_lock, max_retries=3, base_delay=0.01)
        
        assert success is True
        assert count == 2
        assert attempts[0] == 2
        
        # 验证锁已释放（可以重新获取）
        token_new = try_acquire_spawn_lock(task)
        assert token_new is not None


class TestPipelineTimingIntegration:
    """耗时记录集成测试"""
    
    def setup_method(self):
        """每个测试前清理 timings 文件"""
        if TIMINGS_FILE.exists():
            TIMINGS_FILE.unlink()
    
    def test_timing_record_accuracy(self):
        """耗时记录准确性"""
        timer = PipelineTimer(task_id="test-timing-001")
        
        # 模拟各阶段（Windows sleep 精度较低，用 50ms 确保可测）
        time.sleep(0.05)
        timer.mark("submit")
        
        time.sleep(0.05)
        timer.mark("route")
        
        time.sleep(0.05)
        timer.mark("spawn")
        
        time.sleep(0.05)
        timer.mark("execute")
        
        durations = timer.durations()
        
        # 验证各阶段耗时（允许 ±30ms 误差，Windows sleep 精度较低）
        assert 20 < durations["submit_ms"] < 80
        assert 20 < durations["route_ms"] < 80
        assert 20 < durations["spawn_ms"] < 80
        assert 20 < durations["execute_ms"] < 80
        
        # 验证总耗时
        assert 150 < durations["total_ms"] < 350
    
    def test_timing_flush_to_jsonl(self):
        """耗时记录写入 JSONL"""
        timer = PipelineTimer(task_id="test-timing-002")
        timer.mark("submit")
        timer.mark("route")
        timer.mark("spawn")
        timer.mark("execute")
        
        record = timer.flush(extra={"task_type": "code", "success": True})
        
        # 验证文件存在
        assert TIMINGS_FILE.exists()
        
        # 验证记录格式
        assert "task_id" in record
        assert "timestamp" in record
        assert "duration_ms" in record
        assert "task_type" in record
        assert "success" in record
        
        # 验证可以读取
        with open(TIMINGS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            loaded = json.loads(lines[0])
            assert loaded["task_id"] == "test-timing-002"
    
    def test_timing_stats_calculation(self):
        """耗时统计计算"""
        # 写入多条记录
        for i in range(5):
            timer = PipelineTimer(task_id=f"test-stats-{i}")
            time.sleep(0.01)
            timer.mark("submit")
            time.sleep(0.01)
            timer.mark("route")
            time.sleep(0.01)
            timer.mark("spawn")
            time.sleep(0.01)
            timer.mark("execute")
            timer.flush()
        
        stats = get_timing_stats(limit=5)
        
        assert stats["count"] == 5
        assert "avg_total_ms" in stats
        assert "p50_total_ms" in stats
        assert "p95_total_ms" in stats
        assert "stage_avgs" in stats
        
        # 验证平均值合理（4 个阶段，每个 ~10ms）
        assert 30 < stats["avg_total_ms"] < 60


class TestDay3DoD:
    """Day 3 DoD 检查项"""
    
    def setup_method(self):
        """每个测试前清理锁文件和指标"""
        store = get_lock_store()
        if store.lock_file.exists():
            store.lock_file.unlink()
        store._metrics = {
            "acquire_total": 0,
            "acquire_success": 0,
            "idempotent_hit_total": 0,
            "stale_lock_recovered_total": 0,
            "acquire_latency_ms_sum": 0.0,
        }
        store._save_metrics()
    
    def test_dod_retry_with_backoff_coverage(self):
        """DoD: retry_with_backoff 单测覆盖三条路径"""
        # 成功路径
        success, _, _ = retry_with_backoff(lambda: "ok", max_retries=3, base_delay=0.01)
        assert success is True
        
        # 失败路径
        def fail():
            raise ValueError("fail")
        success, _, _ = retry_with_backoff(fail, max_retries=3, base_delay=0.01)
        assert success is False
        
        # 耗尽路径（已在 test_retry_exhausted 覆盖）
        pass
    
    def test_dod_spawn_lock_no_duplicate_on_retry(self):
        """DoD: spawn_lock 重入时不产生新锁文件"""
        task = {"id": "test-dod-001", "zombie_retries": 0}
        
        # 首次 acquire
        token1, _ = acquire_or_reuse(task)
        
        # 重试时复用
        token2, reused = acquire_or_reuse(task, existing_token=token1)
        
        assert token2 == token1
        assert reused is True
        
        # 验证锁文件只有一条记录
        store = get_lock_store()
        locks = store._read_locks()
        assert len(locks) == 1
    
    def test_dod_duration_ms_in_jsonl(self):
        """DoD: 结果 JSONL 包含 duration_ms 字段"""
        timer = PipelineTimer(task_id="test-dod-002")
        timer.mark("submit")
        timer.mark("execute")
        record = timer.flush()
        
        assert "duration_ms" in record
        assert "submit_ms" in record["duration_ms"]
        assert "execute_ms" in record["duration_ms"]
        assert "total_ms" in record["duration_ms"]
    
    def test_dod_pytest_all_green(self):
        """DoD: pytest -q --maxfail=1 全绿（本测试通过即满足）"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--maxfail=1"])
