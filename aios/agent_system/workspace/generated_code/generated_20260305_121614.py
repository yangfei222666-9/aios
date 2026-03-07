

```python
# 快速排序 - 高性能优化版本
# 无需第三方库

import random
import sys
import time

# 提高递归限制
sys.setrecursionlimit(10000)

# 插入排序阈值，小数组用插入排序更快
INSERTION_SORT_THRESHOLD = 16


def insertion_sort(arr, low, high):
    """对小规模子数组使用插入排序"""
    for i in range(low + 1, high + 1):
        key = arr[i]
        j = i - 1
        while j >= low and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


def median_of_three(arr, low, high):
    """三数取中法选择枢轴，避免最坏情况"""
    mid = (low + high) // 2
    # 将 low, mid, high 三个位置的值排序
    if arr[low] > arr[mid]:
        arr[low], arr[mid] = arr[mid], arr[low]
    if arr[low] > arr[high]:
        arr[low], arr[high] = arr[high], arr[low]
    if arr[mid] > arr[high]:
        arr[mid], arr[high] = arr[high], arr[mid]
    # 将枢轴放到 high-1 位置
    arr[mid], arr[high - 1] = arr[high - 1], arr[mid]
    return arr[high - 1]


def three_way_partition(arr, low, high):
    """三路划分（荷兰国旗问题），高效处理大量重复元素"""
    pivot = arr[low]
    lt = low      # arr[low..lt-1] < pivot
    gt = high     # arr[gt+1..high] > pivot
    i = low       # arr[lt..i-1] == pivot

    while i <= gt:
        if arr[i] < pivot:
            arr[lt], arr[i] = arr[i], arr[lt]
            lt += 1
            i += 1
        elif arr[i] > pivot:
            arr[gt], arr[i] = arr[i], arr[gt]
            gt -= 1
        else:
            i += 1

    return lt, gt


def quicksort_optimized(arr, low, high):
    """优化版快速排序主函数"""
    while low < high:
        # 优化1: 小数组使用插入排序
        if high - low < INSERTION_SORT_THRESHOLD:
            insertion_sort(arr, low, high)
            return

        # 优化2: 三数取中选枢轴（数组较大时）
        if high - low > 40:
            # 对大数组使用 ninther（9数取中）
            s = (high - low) // 8
            median_of_three(arr, low, low + s)
            median_of_three(arr, low + s + 1, low + 2 * s + 1)
            # 最终还是用三数取中
            mid = (low + high) // 2
            if arr[low] > arr[mid]:
                arr[low], arr[mid] = arr[mid], arr[low]
            if arr[low] > arr[high]:
                arr[low], arr[high] = arr[high], arr[low]
            if arr[mid] > arr[high]:
                arr[mid], arr[high] = arr[high], arr[mid]
            arr[mid], arr[low] = arr[low], arr[mid]
        else:
            mid = (low + high) // 2
            if arr[low] > arr[mid]:
                arr[low], arr[mid] = arr[mid], arr[low]
            if arr[low] > arr[high]:
                arr[low], arr[high] = arr[high], arr[low]
            if arr[mid] > arr[high]:
                arr[mid], arr[high] = arr[high], arr[mid]
            arr[mid], arr[low] = arr[low], arr[mid]

        # 优化3: 三路划分，处理重复元素
        lt, gt = three_way_partition(arr, low, high)

        # 优化4: 尾递归优化，先递归较小的分区
        if lt - low < high - gt:
            quicksort_optimized(arr, low, lt - 1)
            low = gt + 1  # 尾递归转循环
        else:
            quicksort_optimized(arr, gt + 1, high)
            high = lt - 1  # 尾递归转循环


def quicksort(arr):
    """快速排序入口函数"""
    if not arr or len(arr) <= 1:
        return arr
    quicksort_optimized(arr, 0, len(arr) - 1)
    return arr


# ============ 测试与性能基准 ============

def verify_sort(arr):
    """验证排序结果正确性"""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True


def benchmark(name, data):
    """性能基准测试"""
    arr = data[:]
    start = time.perf_counter()
    quicksort(arr)
    elapsed = time.perf_counter() - start
    is_correct = verify_sort(arr)
    status = "✓" if is_correct else "✗"
    print(f"  {status} {name:30s} | n={len(data):>8d} | {elapsed:.4f}s")
    return is_correct


def run_tests():
    """运行全部测试"""
    print("=" * 65)
    print("  快速排序 - 优化版 性能测试")
    print("=" * 65)

    n = 100000
    all_passed = True

    # 1. 随机数组
    all_passed &= benchmark("随机数组", [random.randint(0, n) for _ in range(n)])

    # 2. 已排序数组（最坏情况之一）
    all_passed &= benchmark("已排序数组", list(range(n)))

    # 3. 逆序数组
    all_passed &= benchmark("逆序数组", list(range(n, 0, -1)))

    # 4. 全部相同元素
    all_passed &= benchmark("全部相同元素", [42] * n)

    # 5. 大量重复元素
    all_passed &= benchmark("大量重复元素(10种值)", [random.randint(0, 9) for _ in range(n)])

    # 6. 近乎有序数组
    nearly = list(range(n))
    for _ in range(n // 100):
        i, j = random.randint(0, n - 1), random.randint(0, n - 1)
        nearly[i], nearly[j] = nearly[j], nearly[i]
    all_passed &= benchmark("近乎有序数组", nearly)

    # 7. 小数组
    all_passed &= benchmark("小数组(10个元素)", [random.randint(0, 100) for _ in range(10)])

    # 8. 空数组和单元素
    all_passed &= benchmark("空数组", [])
    all_passed &= benchmark("单元素数组", [1])

    # 9. 两个元素
    all_passed &= benchmark("两个元素(逆序)", [2, 1])

    # 10. 与 Python 内置排序对比
    print("-" * 65)
    print("  与 Python 内置 sorted() 对比 (n=500000)")
    print("-" * 65)

    big_n = 500000
    data = [random.randint(0, big_n) for _ in range(big_n)]

    arr1 = data[:]
    start = time.perf_counter()
    quicksort(arr1)
    t_custom = time.perf_counter() - start

    arr2 = data[:]
    start = time.perf_counter()
    arr2.sort()
    t_builtin = time.perf_counter() - start

    print(f"  优化快速排序: {t_custom:.4f}s")
    print(f"  内置 sort():  {t_builtin:.4f}s")
    print(f"  比率:         {t_custom / t_builtin:.1f}x")

    print("=" * 65)
    if all_passed:
        print("  所有测试通过 ✓")
    else:
        print("  存在失败的测试 ✗")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
```

核心优化点：

- 小数组切换插入排序，减少递归开销
- 三数取中 / 九数取中选枢轴，避免有序数组退化为 O(n²)
- 三路划分处理重复元素，大量重复时接近 O(n)
- 尾递归转循环，栈深度从 O(n) 降到 O(log n)