# 计算1到10的和
def calculate_sum():
    """计算1到10的和"""
    try:
        total = sum(range(1, 11))
        return total
    except Exception as e:
        print(f"计算出错: {e}")
        return None

# 执行函数并输出结果
if __name__ == "__main__":
    result = calculate_sum()
    if result is not None:
        print(f"1到10的和为: {result}")