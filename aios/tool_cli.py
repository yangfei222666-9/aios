#!/usr/bin/env python3
"""
tool_cli.py - 工具注册中心 CLI

用法：
  python tool_cli.py list                    # 列出所有工具
  python tool_cli.py list --tag math         # 按标签筛选
  python tool_cli.py stats                   # 查看统计信息
  python tool_cli.py stats --export stats.json  # 导出统计
  python tool_cli.py call add '{"a":1,"b":2}'  # 调用工具
  python tool_cli.py history                 # 查看调用历史
"""

import sys
import json
import argparse
from pathlib import Path

# 直接导入模块文件（避免 __init__.py 的依赖问题）
sys.path.insert(0, str(Path(__file__).parent / "agent_system"))

import tool_registry
ToolRegistry = tool_registry.ToolRegistry
register_tool = tool_registry.register_tool


def cmd_list(args):
    """列出工具"""
    registry = ToolRegistry()
    
    if args.tag:
        tools = registry.list_by_tag(args.tag)
    else:
        tools = registry.list_all()
    
    if not tools:
        print("No tools found")
        return
    
    print(f"Found {len(tools)} tool(s):\n")
    for tool in tools:
        print(f"[Tool] {tool.name}")
        print(f"   {tool.description}")
        print(f"   Tags: {', '.join(tool.tags) if tool.tags else 'none'}")
        print(f"   Max retries: {tool.max_retries}")
        print()


def cmd_stats(args):
    """查看统计信息"""
    registry = ToolRegistry()
    stats = registry.get_stats()
    
    if args.export:
        registry.export_stats(args.export)
        print(f"[OK] Stats exported to {args.export}")
        return
    
    data = stats.to_dict()
    
    print(f"[Stats] Tool Usage Statistics\n")
    print(f"Total calls: {data['total_calls']}")
    print(f"Total successes: {data['total_successes']}")
    print(f"Total failures: {data['total_failures']}")
    print()
    
    if data['by_tool']:
        print("By tool:")
        for name, tool_stats in data['by_tool'].items():
            print(f"\n  {name}:")
            print(f"    Calls: {tool_stats['calls']}")
            print(f"    Success rate: {tool_stats['success_rate']:.1%}")
            print(f"    Avg duration: {tool_stats['avg_duration']:.3f}s")
            print(f"    Avg retries: {tool_stats['avg_retries']:.2f}")


def cmd_call(args):
    """调用工具"""
    registry = ToolRegistry()
    
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        return
    
    print(f"Calling {args.tool_name} with params: {params}")
    success, result, record = registry.execute(args.tool_name, params)
    
    if success:
        print(f"[OK] Success!")
        print(f"Result: {result}")
        print(f"Duration: {record.duration:.3f}s")
        print(f"Retries: {record.retries}")
    else:
        print(f"[FAIL] Failed!")
        print(f"Error: {record.error}")
        print(f"Duration: {record.duration:.3f}s")
        print(f"Retries: {record.retries}")


def cmd_history(args):
    """查看调用历史"""
    registry = ToolRegistry()
    history = registry.get_call_history(limit=args.limit)
    
    if not history:
        print("No call history")
        return
    
    print(f"[History] Recent {len(history)} calls:\n")
    for record in history:
        status = "[OK]" if record.success else "[FAIL]"
        print(f"{status} {record.tool_name}")
        print(f"   Params: {record.params}")
        print(f"   Duration: {record.duration:.3f}s, Retries: {record.retries}")
        if record.error:
            print(f"   Error: {record.error}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Tool Registry CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # list
    list_parser = subparsers.add_parser("list", help="List tools")
    list_parser.add_argument("--tag", help="Filter by tag")
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--export", help="Export to JSON file")
    
    # call
    call_parser = subparsers.add_parser("call", help="Call a tool")
    call_parser.add_argument("tool_name", help="Tool name")
    call_parser.add_argument("params", help="Parameters (JSON)")
    
    # history
    history_parser = subparsers.add_parser("history", help="Show call history")
    history_parser.add_argument("--limit", type=int, default=20, help="Number of records")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 注册示例工具（用于测试）
    _register_example_tools()
    
    # 执行命令
    if args.command == "list":
        cmd_list(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "call":
        cmd_call(args)
    elif args.command == "history":
        cmd_history(args)


def _register_example_tools():
    """注册示例工具（用于测试）"""
    
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    def multiply_numbers(a: int, b: int) -> int:
        return a * b
    
    def divide_numbers(a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    
    register_tool(
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
    
    register_tool(
        name="multiply",
        func=multiply_numbers,
        description="Multiply two numbers",
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
    
    register_tool(
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
        max_retries=1  # 除法错误不重试
    )


if __name__ == "__main__":
    main()
