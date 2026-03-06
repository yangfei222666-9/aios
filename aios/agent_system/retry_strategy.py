"""
Retry Strategy with Exponential Backoff + Jitter

纯函数实现，不依赖外部状态。
"""

import time
import random
from typing import Callable, Tuple, Optional, Any


def retry_with_backoff(
    fn: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: bool = True
) -> Tuple[bool, int, Optional[Exception]]:
    """
    指数退避重试策略
    
    Args:
        fn: 要执行的函数（无参数）
        max_retries: 最大重试次数（默认 3）
        base_delay: 初始延迟（秒，默认 0.5）
        max_delay: 最大延迟（秒，默认 30.0）
        jitter: 是否添加随机抖动（默认 True）
    
    Returns:
        (success, attempts, last_error)
        - success: 是否最终成功
        - attempts: 实际尝试次数（含首次）
        - last_error: 最后一次失败的异常（成功时为 None）
    
    Examples:
        >>> def flaky_task():
        ...     if random.random() < 0.5:
        ...         raise ValueError("Transient error")
        ...     return "success"
        >>> success, attempts, error = retry_with_backoff(flaky_task)
        >>> if success:
        ...     print(f"Succeeded after {attempts} attempts")
        ... else:
        ...     print(f"Failed after {attempts} attempts: {error}")
    """
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            fn()
            return (True, attempt, None)
        except Exception as e:
            last_error = e
            
            # 最后一次失败不需要等待
            if attempt == max_retries:
                break
            
            # 计算延迟：base_delay * 2^(attempt-1)
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            
            # 添加 jitter（±25%）
            if jitter:
                jitter_range = delay * 0.25
                delay += random.uniform(-jitter_range, jitter_range)
            
            # 确保延迟非负
            delay = max(0, delay)
            
            time.sleep(delay)
    
    return (False, max_retries, last_error)


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: bool = True
) -> float:
    """
    计算退避延迟（不执行 sleep，仅计算）
    
    用于测试或预览延迟序列。
    
    Args:
        attempt: 当前尝试次数（从 1 开始）
        base_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        jitter: 是否添加随机抖动
    
    Returns:
        延迟时间（秒）
    
    Examples:
        >>> delays = [calculate_backoff_delay(i, jitter=False) for i in range(1, 5)]
        >>> print(delays)  # [0.5, 1.0, 2.0, 4.0]
    """
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    
    if jitter:
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


if __name__ == "__main__":
    # Demo: 模拟不稳定任务
    print("=== Retry Strategy Demo ===\n")
    
    # 测试 1: 第 2 次成功
    print("Test 1: Success on 2nd attempt")
    attempt_count = [0]
    def task_success_on_2nd():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise ValueError(f"Transient error (attempt {attempt_count[0]})")
        return "success"
    
    success, attempts, error = retry_with_backoff(task_success_on_2nd, base_delay=0.1)
    print(f"  Result: success={success}, attempts={attempts}, error={error}\n")
    
    # 测试 2: 全部失败
    print("Test 2: All attempts fail")
    def task_always_fail():
        raise RuntimeError("Permanent error")
    
    success, attempts, error = retry_with_backoff(task_always_fail, max_retries=3, base_delay=0.1)
    print(f"  Result: success={success}, attempts={attempts}, error={error}\n")
    
    # 测试 3: 首次成功
    print("Test 3: Success on 1st attempt")
    def task_immediate_success():
        return "success"
    
    success, attempts, error = retry_with_backoff(task_immediate_success)
    print(f"  Result: success={success}, attempts={attempts}, error={error}\n")
    
    # 测试 4: 延迟序列预览
    print("Test 4: Backoff delay sequence (no jitter)")
    delays = [calculate_backoff_delay(i, base_delay=0.5, jitter=False) for i in range(1, 6)]
    print(f"  Delays: {delays}")
