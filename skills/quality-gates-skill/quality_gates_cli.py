#!/usr/bin/env python3
"""
Quality Gates CLI - 快速检查改进是否可以应用

使用示例：
    # 检查 L0 门禁
    python quality_gates_cli.py check --level L0 --agent-id coder
    
    # 检查改进
    python quality_gates_cli.py improvement --agent-id coder --change-type code --risk-level high
    
    # 查看门禁历史
    python quality_gates_cli.py history --limit 10
"""

import sys
import json
import argparse
from pathlib import Path

# 添加 aios 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "aios"))

from data_collector.quality_gates import QualityGateSystem


def check_gates(args):
    """检查门禁"""
    system = QualityGateSystem()
    
    context = {"agent_id": args.agent_id}
    result = system.check_all(args.level, context)
    
    print(f"🔍 {args.level} 门禁检查:")
    print(f"   总门禁数: {result['total']}")
    print(f"   通过数: {result['passed_count']}")
    print(f"   失败数: {result['failed_count']}")
    print(f"   整体结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
    
    for gate_result in result['results']:
        status = "✅" if gate_result['passed'] else "❌"
        message = gate_result['result'].get('message', '')
        print(f"     {status} {gate_result['gate']}: {message}")


def check_improvement(args):
    """检查改进"""
    system = QualityGateSystem()
    
    result = system.check_improvement(
        agent_id=args.agent_id,
        change_type=args.change_type,
        risk_level=args.risk_level
    )
    
    if result['approved']:
        print(f"✅ 改进已批准")
    else:
        print(f"❌ 改进被拒绝")
    
    print(f"   原因: {result['reason']}")
    
    if 'details' in result:
        if 'L0' in result['details']:
            l0 = result['details']['L0']
            print(f"   L0: {'✅ 通过' if l0['passed'] else '❌ 失败'} ({l0['passed_count']}/{l0['total']})")
        
        if 'L1' in result['details']:
            l1 = result['details']['L1']
            print(f"   L1: {'✅ 通过' if l1['passed'] else '❌ 失败'} ({l1['passed_count']}/{l1['total']})")
        
        if 'L2' in result['details']:
            l2 = result['details']['L2']
            print(f"   L2: {'✅ 通过' if l2['passed'] else '❌ 失败'} ({l2['passed_count']}/{l2['total']})")


def show_history(args):
    """查看门禁历史"""
    system = QualityGateSystem()
    
    # 读取最近的门禁结果
    results_dir = system.results_dir
    result_files = sorted(results_dir.glob("gate_*.json"), reverse=True)
    
    if not result_files:
        print("📂 没有门禁历史")
        return
    
    print(f"📂 门禁历史（最近 {args.limit} 条）:")
    
    for i, result_file in enumerate(result_files[:args.limit]):
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        
        status = "✅" if result['passed'] else "❌"
        print(f"   {i+1}. {status} {result['level']} - {result['timestamp']}")
        print(f"      通过: {result['passed_count']}/{result['total']}")


def list_gates(args):
    """列出所有门禁"""
    system = QualityGateSystem()
    
    print("📋 已注册的门禁:")
    
    for level in ["L0", "L1", "L2"]:
        gates = system.gates.get(level, [])
        print(f"\n   {level} ({len(gates)} 个门禁):")
        for gate in gates:
            required = "必需" if gate.required else "可选"
            print(f"     - {gate.name} ({required})")


def main():
    parser = argparse.ArgumentParser(description="Quality Gates CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # check
    check_parser = subparsers.add_parser("check", help="检查门禁")
    check_parser.add_argument("--level", required=True, choices=["L0", "L1", "L2"], help="门禁级别")
    check_parser.add_argument("--agent-id", help="Agent ID")
    
    # improvement
    improvement_parser = subparsers.add_parser("improvement", help="检查改进")
    improvement_parser.add_argument("--agent-id", required=True, help="Agent ID")
    improvement_parser.add_argument("--change-type", required=True, choices=["config", "prompt", "code"], help="改进类型")
    improvement_parser.add_argument("--risk-level", default="medium", choices=["low", "medium", "high"], help="风险级别")
    
    # history
    history_parser = subparsers.add_parser("history", help="查看门禁历史")
    history_parser.add_argument("--limit", type=int, default=10, help="最大返回数量")
    
    # list
    list_parser = subparsers.add_parser("list", help="列出所有门禁")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "check": check_gates,
        "improvement": check_improvement,
        "history": show_history,
        "list": list_gates
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
