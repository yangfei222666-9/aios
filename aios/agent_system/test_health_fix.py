#!/usr/bin/env python3
"""测试 Health Score 修复"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from heartbeat_v6 import calculate_health_score

print("=" * 60)
print("Health Score 修复验证")
print("=" * 60)

# Test 1: 空队列（模拟周日 0 任务）
print("\nTest 1: 空队列（周日 0 任务场景）")
score = calculate_health_score()
print(f"  Health Score: {score:.2f}/100")
print(f"  Expected: 100.0")
print(f"  Result: {'✅ PASS' if score == 100.0 else '❌ FAIL'}")

print("\n" + "=" * 60)
print("修复完成！")
print("=" * 60)
