"""
斐波那契数列计算模块
实现递归和迭代两种方法，并提供性能对比
"""

import time
import functools


def fibonacci_recursive(n: int) -> int:
    """
    递归方法计算斐波那契数列第 n 项
    
    时间复杂度: O(2^n) - 指数级，效率较低
    空间复杂度: O(n) - 递归调用栈深度
    
    Args:
        n: 第 n 项（从 0 开始）
        
    Returns:
        第 n 项的值
        
    Raises:
        ValueError: 当 n < 0 时
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    
    if n <= 1:
        return n
    
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


@functools.lru_cache(maxsize=None)
def fibonacci_recursive_cached(n: int) -> int:
    """
    带缓存的递归方法（记忆化）
    
    时间复杂度: O(n) - 每个值只计算一次
    空间复杂度: O(n) - 缓存空间 + 递归栈
    
    Args:
        n: 第 n 项（从 0 开始）
        
    Returns:
        第 n 项的值
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    
    if n <= 1:
        return n
    
    return fibonacci_recursive_cached(n - 1) + fibonacci_recursive_cached(n - 2)


def fibonacci_iterative(n: int) -> int:
    """
    迭代方法计算斐波那契数列第 n 项
    
    时间复杂度: O(n) - 线性时间
    空间复杂度: O(1) - 只用常量空间
    
    Args:
        n: 第 n 项（从 0 开始）
        
    Returns:
        第 n 项的值
        
    Raises:
        ValueError: 当 n < 0 时
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    
    if n <= 1:
        return n
    
    # 使用两个变量滚动计算
    prev, curr = 0, 1
    
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    
    return curr


def benchmark(func, n: int, runs: int = 1) -> tuple[int, float]:
    """
    性能测试函数
    
    Args:
        func: 要测试的函数
        n: 斐波那契数列的项数
        runs: 运行次数（取平均值）
        
    Returns:
        (结果值, 平均耗时秒数)
    """
    total_time = 0
    result = None
    
    for _ in range(runs):
        start = time.perf_counter()
        result = func(n)
        end = time.perf_counter()
        total_time += (end - start)
    
    avg_time = total_time / runs
    return result, avg_time


def performance_comparison(n: int = 30):
    """
    性能对比测试
    
    Args:
        n: 测试的斐波那契项数
    """
    print(f"\n{'='*60}")
    print(f"斐波那契数列第 {n} 项性能对比")
    print(f"{'='*60}\n")
    
    # 测试迭代方法
    result_iter, time_iter = benchmark(fibonacci_iterative, n, runs=1000)
    print(f"迭代方法:")
    print(f"  结果: {result_iter}")
    print(f"  平均耗时: {time_iter*1000:.6f} ms (1000次运行)")
    
    # 测试带缓存的递归方法
    fibonacci_recursive_cached.cache_clear()  # 清空缓存
    result_cached, time_cached = benchmark(fibonacci_recursive_cached, n, runs=1000)
    print(f"\n递归方法（带缓存）:")
    print(f"  结果: {result_cached}")
    print(f"  平均耗时: {time_cached*1000:.6f} ms (1000次运行)")
    
    # 测试普通递归方法（只在 n 较小时测试，避免等待太久）
    if n <= 35:
        result_rec, time_rec = benchmark(fibonacci_recursive, n, runs=1)
        print(f"\n递归方法（无缓存）:")
        print(f"  结果: {result_rec}")
        print(f"  耗时: {time_rec*1000:.2f} ms (1次运行)")
        print(f"  相比迭代慢: {time_rec/time_iter:.0f}x")
    else:
        print(f"\n递归方法（无缓存）: 跳过（n > 35 时太慢）")
    
    print(f"\n{'='*60}\n")


def test_fibonacci():
    """
    完整的测试用例
    """
    print("开始测试斐波那契函数...\n")
    
    # 测试用例：前 15 项的正确值
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
    
    print("测试基本功能:")
    all_passed = True
    
    for i, expected_val in enumerate(expected):
        # 测试迭代方法
        result_iter = fibonacci_iterative(i)
        # 测试递归方法
        result_rec = fibonacci_recursive(i)
        # 测试带缓存的递归方法
        result_cached = fibonacci_recursive_cached(i)
        
        if result_iter == expected_val and result_rec == expected_val and result_cached == expected_val:
            print(f"  ✓ f({i}) = {expected_val}")
        else:
            print(f"  ✗ f({i}) 失败: 期望 {expected_val}, 得到 iter={result_iter}, rec={result_rec}, cached={result_cached}")
            all_passed = False
    
    # 测试边界情况
    print("\n测试边界情况:")
    
    # 测试负数输入
    try:
        fibonacci_iterative(-1)
        print("  ✗ 负数测试失败：应该抛出 ValueError")
        all_passed = False
    except ValueError:
        print("  ✓ 负数输入正确抛出异常")
    
    # 测试较大的数
    large_n = 50
    result_large = fibonacci_iterative(large_n)
    print(f"  ✓ f({large_n}) = {result_large}")
    
    if all_passed:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    # 运行测试
    test_fibonacci()
    
    # 运行性能对比
    performance_comparison(n=30)
    
    # 可选：测试更大的数值
    print("计算更大的斐波那契数:")
    for n in [50, 100, 500]:
        result = fibonacci_iterative(n)
        print(f"  f({n}) = {result}")
