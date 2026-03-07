# 计算斐波那契数列的函数

def fibonacci(n):
    """
    计算斐波那契数列的第 n 项
    
    参数:
        n: 整数，表示要计算的项数（从0开始）
    
    返回:
        第 n 项的斐波那契数
    """
    if not isinstance(n, int):
        raise TypeError("参数必须是整数")
    
    if n < 0:
        raise ValueError("参数必须是非负整数")
    
    if n == 0:
        return 0
    elif n == 1:
        return 1
    
    # 使用迭代方式计算，避免递归栈溢出
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b


def fibonacci_sequence(n):
    """
    生成斐波那契数列的前 n 项
    
    参数:
        n: 整数，表示要生成的项数
    
    返回:
        包含前 n 项斐波那契数的列表
    """
    if not isinstance(n, int):
        raise TypeError("参数必须是整数")
    
    if n <= 0:
        raise ValueError("参数必须是正整数")
    
    sequence = []
    for i in range(n):
        sequence.append(fibonacci(i))
    
    return sequence


# 测试代码
if __name__ == "__main__":
    try:
        # 计算第10项
        print(f"第10项: {fibonacci(10)}")
        
        # 生成前15项
        print(f"前15项: {fibonacci_sequence(15)}")
        
    except Exception as e:
        print(f"错误: {e}")