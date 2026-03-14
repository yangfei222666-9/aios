#!/usr/bin/env python3
"""测试 tool_registry"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_system"))

import tool_registry

# 注册示例工具
def add_numbers(a: int, b: int) -> int:
    return a + b

def divide_numbers(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

tool_registry.register_tool(
    name="add",
    func=add_numbers,
    description="Add two numbers",
    schema={
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"}
        },
        "required": ["a", "b"]
    },
    tags=["math", "basic"]
)

tool_registry.register_tool(
    name="divide",
    func=divide_numbers,
    description="Divide two numbers",
    schema={
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        "required": ["a", "b"]
    },
    tags=["math", "advanced"],
    max_retries=1
)

# 测试 1: 正常调用
print("Test 1: Normal call")
success, result = tool_registry.execute_tool("add", {"a": 10, "b": 20})
print(f"  Result: {result}, Success: {success}")
print()

# 测试 2: 参数验证失败
print("Test 2: Parameter validation failure")
success, result = tool_registry.execute_tool("add", {"a": "not a number", "b": 20})
print(f"  Result: {result}, Success: {success}")
print()

# 测试 3: 执行失败（除以零）
print("Test 3: Execution failure (division by zero)")
success, result = tool_registry.execute_tool("divide", {"a": 10, "b": 0})
print(f"  Result: {result}, Success: {success}")
print()

# 测试 4: 查看统计
print("Test 4: Statistics")
registry = tool_registry.ToolRegistry()
stats = registry.get_stats()
print(f"  Total calls: {sum(stats.calls.values())}")
print(f"  Total successes: {sum(stats.successes.values())}")
print(f"  Total failures: {sum(stats.failures.values())}")
print()

# 测试 5: 查看调用历史
print("Test 5: Call history")
history = registry.get_call_history(limit=5)
for record in history:
    status = "[OK]" if record.success else "[FAIL]"
    print(f"  {status} {record.tool_name}: {record.params}")
