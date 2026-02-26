# 判断一个数是否为质数的函数

def is_prime(n):
    """
    判断一个数是否为质数
    
    参数:
        n: 待判断的整数
    
    返回:
        bool: 如果是质数返回 True，否则返回 False
    """
    try:
        # 转换为整数
        n = int(n)
        
        # 小于2的数不是质数
        if n < 2:
            return False
        
        # 2是质数
        if n == 2:
            return True
        
        # 偶数不是质数
        if n % 2 == 0:
            return False
        
        # 只需检查到sqrt(n)
        i = 3
        while i * i <= n:
            if n % i == 0:
                return False
            i += 2
        
        return True
    
    except (ValueError, TypeError):
        return False


# 测试示例
if __name__ == "__main__":
    test_numbers = [1, 2, 3, 4, 5, 17, 20, 29, 100, 97]
    
    for num in test_numbers:
        result = is_prime(num)
        print(f"{num} 是质数: {result}")