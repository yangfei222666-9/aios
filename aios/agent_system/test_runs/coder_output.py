"""
斐波那契数列生成器及测试用例
"""
from typing import List


def fibonacci(n: int) -> List[int]:
    """
    返回前 n 个斐波那契数列。
    
    斐波那契数列定义：F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)
    
    Args:
        n: 要生成的斐波那契数列长度
        
    Returns:
        包含前 n 个斐波那契数的列表
        
    Raises:
        ValueError: 当 n 为负数时
        
    Examples:
        >>> fibonacci(5)
        [0, 1, 1, 2, 3]
        >>> fibonacci(0)
        []
        >>> fibonacci(1)
        [0]
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    
    if n == 0:
        return []
    
    if n == 1:
        return [0]
    
    result = [0, 1]
    for i in range(2, n):
        result.append(result[i-1] + result[i-2])
    
    return result


def test_fibonacci():
    """运行测试用例验证 fibonacci 函数"""
    
    # 测试用例 1: 基本情况 - 生成前 8 个数
    print("测试用例 1: fibonacci(8)")
    result1 = fibonacci(8)
    expected1 = [0, 1, 1, 2, 3, 5, 8, 13]
    assert result1 == expected1, f"失败: 期望 {expected1}, 得到 {result1}"
    print(f"[PASS] 通过: {result1}")
    
    # 测试用例 2: 边界情况 - n = 0 和 n = 1
    print("\n测试用例 2: fibonacci(0) 和 fibonacci(1)")
    result2_0 = fibonacci(0)
    result2_1 = fibonacci(1)
    assert result2_0 == [], f"失败: fibonacci(0) 期望 [], 得到 {result2_0}"
    assert result2_1 == [0], f"失败: fibonacci(1) 期望 [0], 得到 {result2_1}"
    print(f"[PASS] 通过: fibonacci(0) = {result2_0}")
    print(f"[PASS] 通过: fibonacci(1) = {result2_1}")
    
    # 测试用例 3: 较大数值 - 生成前 15 个数
    print("\n测试用例 3: fibonacci(15)")
    result3 = fibonacci(15)
    expected3 = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
    assert result3 == expected3, f"失败: 期望 {expected3}, 得到 {result3}"
    print(f"[PASS] 通过: {result3}")
    
    print("\n" + "="*50)
    print("所有测试用例通过！")
    print("="*50)


if __name__ == "__main__":
    test_fibonacci()
