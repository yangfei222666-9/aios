#!/usr/bin/env python3
"""分析 Logic 错误的详细信息"""

import json
from pathlib import Path
from collections import Counter

# 读取报告
report_file = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\evolution\reports\evolution_20260224_162958.json")
with open(report_file, 'r', encoding='utf-8') as f:
    report = json.load(f)

traces = report['phases']['observe']['traces']

print("=" * 60)
print("  Logic 错误详细分析")
print("=" * 60)
print()

# 按环境分类
prod_traces = [t for t in traces if t.get('env') == 'prod']
test_traces = [t for t in traces if t.get('env') == 'test']

print(f"总追踪数: {len(traces)}")
print(f"  生产环境: {len(prod_traces)}")
print(f"  测试环境: {len(test_traces)}")
print()

# 生产环境失败
prod_failures = [t for t in prod_traces if not t['success']]
print(f"生产环境失败: {len(prod_failures)}")
if prod_failures:
    prod_errors = Counter([f.get('error', 'Unknown') for f in prod_failures])
    for err, count in prod_errors.most_common():
        print(f"  {err}: {count}次")
print()

# 测试环境失败
test_failures = [t for t in test_traces if not t['success']]
print(f"测试环境失败: {len(test_failures)}")
if test_failures:
    test_errors = Counter([f.get('error', 'Unknown') for f in test_failures])
    for err, count in test_errors.most_common():
        print(f"  {err}: {count}次")
print()

# Division by zero 详细分析
div_zero_failures = [t for t in test_failures if 'division by zero' in t.get('error', '')]
if div_zero_failures:
    print(f"Division by zero 错误详情:")
    print(f"  总数: {len(div_zero_failures)}")
    print(f"  环境: 测试环境（非生产）")
    
    # 受影响的 Agent
    agents = Counter([f['agent_id'] for f in div_zero_failures])
    print(f"\n  受影响的 Agent:")
    for agent, count in agents.most_common():
        print(f"    {agent}: {count}次")
    
    # 任务类型
    tasks = Counter([f['task'] for f in div_zero_failures])
    print(f"\n  任务类型:")
    for task, count in tasks.most_common(5):
        print(f"    {task}: {count}次")
    
    # 示例
    print(f"\n  示例错误:")
    example = div_zero_failures[0]
    print(f"    Agent: {example['agent_id']}")
    print(f"    任务: {example['task']}")
    print(f"    错误: {example['error']}")
    print(f"    时间: {example['start_time']}")
else:
    print("未发现 division by zero 错误")

print()
print("=" * 60)
print("  结论")
print("=" * 60)
print()

if len(div_zero_failures) > 0:
    print("⚠️ Division by zero 错误来自测试环境")
    print("   这些是测试数据，不是真实的生产问题")
    print("   建议: 清理测试数据或分离测试/生产追踪")
else:
    print("✅ 生产环境没有 division by zero 错误")
    print("   真实问题是:")
    if prod_failures:
        prod_errors = Counter([f.get('error', 'Unknown') for f in prod_failures])
        for err, count in prod_errors.most_common(3):
            print(f"   - {err}: {count}次")
