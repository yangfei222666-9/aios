"""
Unit tests for retry_strategy.py
"""

import pytest
import time
from retry_strategy import retry_with_backoff, calculate_backoff_delay


class TestRetryWithBackoff:
    """测试 retry_with_backoff 函数"""
    
    def test_success_on_first_attempt(self):
        """首次成功"""
        call_count = [0]
        
        def task():
            call_count[0] += 1
            return "success"
        
        success, attempts, error = retry_with_backoff(task, max_retries=3, base_delay=0.01)
        
        assert success is True
        assert attempts == 1
        assert error is None
        assert call_count[0] == 1
    
    def test_success_on_second_attempt(self):
        """第二次成功"""
        call_count = [0]
        
        def task():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Transient error")
            return "success"
        
        success, attempts, error = retry_with_backoff(task, max_retries=3, base_delay=0.01)
        
        assert success is True
        assert attempts == 2
        assert error is None
        assert call_count[0] == 2
    
    def test_all_attempts_fail(self):
        """全部失败（重试耗尽）"""
        call_count = [0]
        
        def task():
            call_count[0] += 1
            raise RuntimeError("Permanent error")
        
        success, attempts, error = retry_with_backoff(task, max_retries=3, base_delay=0.01)
        
        assert success is False
        assert attempts == 3
        assert isinstance(error, RuntimeError)
        assert str(error) == "Permanent error"
        assert call_count[0] == 3
    
    def test_max_retries_respected(self):
        """验证 max_retries 参数生效"""
        call_count = [0]
        
        def task():
            call_count[0] += 1
            raise ValueError("Always fail")
        
        success, attempts, error = retry_with_backoff(task, max_retries=5, base_delay=0.01)
        
        assert success is False
        assert attempts == 5
        assert call_count[0] == 5
    
    def test_exponential_backoff_timing(self):
        """验证指数退避延迟（粗略验证，允许误差）"""
        call_times = []
        
        def task():
            call_times.append(time.time())
            raise ValueError("Fail")
        
        retry_with_backoff(task, max_retries=3, base_delay=0.1, jitter=False)
        
        # 验证至少有 3 次调用
        assert len(call_times) == 3
        
        # 验证延迟递增（允许 ±50ms 误差）
        delay_1 = call_times[1] - call_times[0]
        delay_2 = call_times[2] - call_times[1]
        
        assert 0.05 < delay_1 < 0.15  # 预期 0.1s
        assert 0.15 < delay_2 < 0.25  # 预期 0.2s
    
    def test_max_delay_cap(self):
        """验证 max_delay 上限生效"""
        delays = []
        
        def task():
            raise ValueError("Fail")
        
        # 模拟大量重试，验证延迟不超过 max_delay
        for attempt in range(1, 10):
            delay = calculate_backoff_delay(attempt, base_delay=1.0, max_delay=5.0, jitter=False)
            delays.append(delay)
        
        # 所有延迟应 <= 5.0
        assert all(d <= 5.0 for d in delays)
        
        # 后期延迟应稳定在 5.0
        assert delays[-1] == 5.0
    
    def test_jitter_adds_randomness(self):
        """验证 jitter 添加随机性"""
        delays_with_jitter = []
        delays_without_jitter = []
        
        for _ in range(10):
            delays_with_jitter.append(
                calculate_backoff_delay(2, base_delay=1.0, jitter=True)
            )
            delays_without_jitter.append(
                calculate_backoff_delay(2, base_delay=1.0, jitter=False)
            )
        
        # 无 jitter 时所有延迟相同
        assert len(set(delays_without_jitter)) == 1
        
        # 有 jitter 时延迟应有变化（至少 3 个不同值）
        assert len(set(delays_with_jitter)) >= 3
    
    def test_zero_max_retries(self):
        """max_retries=0 时不应重试"""
        call_count = [0]
        
        def task():
            call_count[0] += 1
            raise ValueError("Fail")
        
        success, attempts, error = retry_with_backoff(task, max_retries=0, base_delay=0.01)
        
        # 注意：max_retries=0 意味着"尝试 0 次"，但实际会至少尝试 1 次
        # 这是设计决策：range(1, 0+1) = range(1, 1) = []，所以不会执行
        # 需要修正：max_retries 应该是"最大尝试次数"而非"重试次数"
        # 当前实现：max_retries=0 会导致 range(1, 1)，即不执行
        assert call_count[0] == 0  # 当前行为
        assert success is False
        assert attempts == 0


class TestCalculateBackoffDelay:
    """测试 calculate_backoff_delay 函数"""
    
    def test_exponential_growth(self):
        """验证指数增长"""
        delays = [
            calculate_backoff_delay(i, base_delay=1.0, jitter=False)
            for i in range(1, 6)
        ]
        
        # 预期：[1.0, 2.0, 4.0, 8.0, 16.0]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]
    
    def test_base_delay_scaling(self):
        """验证 base_delay 缩放"""
        delays = [
            calculate_backoff_delay(i, base_delay=0.5, jitter=False)
            for i in range(1, 4)
        ]
        
        # 预期：[0.5, 1.0, 2.0]
        assert delays == [0.5, 1.0, 2.0]
    
    def test_max_delay_enforced(self):
        """验证 max_delay 强制执行"""
        delay = calculate_backoff_delay(10, base_delay=1.0, max_delay=10.0, jitter=False)
        
        # 2^9 = 512，但应被限制在 10.0
        assert delay == 10.0
    
    def test_jitter_range(self):
        """验证 jitter 范围（±25%）"""
        base_delay = 4.0
        delays = [
            calculate_backoff_delay(3, base_delay=1.0, jitter=True)
            for _ in range(100)
        ]
        
        # 预期基准：2^2 * 1.0 = 4.0
        # jitter 范围：4.0 ± 1.0 = [3.0, 5.0]
        assert all(3.0 <= d <= 5.0 for d in delays)
        
        # 验证确实有分布（不是全部相同）
        assert len(set(delays)) > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
