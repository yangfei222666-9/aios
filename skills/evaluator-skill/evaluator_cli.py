#!/usr/bin/env python3
"""
Evaluator CLI - 快速评估 AIOS 系统

使用示例：
    # 评估任务
    python evaluator_cli.py tasks --time-window 24
    
    # 评估 Agent
    python evaluator_cli.py agent --agent-id coder
    
    # 评估系统
    python evaluator_cli.py system --time-window 24
    
    # 生成报告
    python evaluator_cli.py report --time-window 24
"""

import sys
import json
import argparse
from pathlib import Path

# 添加 aios 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "aios"))

from data_collector.evaluator import Evaluator


def evaluate_tasks(args):
    """评估任务"""
    evaluator = Evaluator()
    
    result = evaluator.evaluate_tasks(
        time_window_hours=args.time_window,
        task_type=args.task_type
    )
    
    print(f"📋 任务评估（最近 {args.time_window} 小时）:")
    print(f"   总任务数: {result['total']}")
    print(f"   成功任务: {result['success']}")
    print(f"   失败任务: {result['failed']}")
    print(f"   成功率: {result['success_rate']:.2%}")
    print(f"   平均耗时: {result['avg_duration_ms']:.0f} ms")
    print(f"   平均成本: ${result['avg_cost_usd']:.4f}")


def evaluate_agent(args):
    """评估 Agent"""
    evaluator = Evaluator()
    
    result = evaluator.evaluate_agent(args.agent_id)
    
    if result['status'] == 'not_found':
        print(f"❌ Agent 不存在: {args.agent_id}")
        return
    
    print(f"🤖 Agent 评估: {result['agent_id']}")
    print(f"   状态: {result['status']}")
    print(f"   成功率: {result['success_rate']:.2%}")
    print(f"   平均耗时: {result['avg_duration_ms']:.0f} ms")
    print(f"   总成本: ${result['total_cost_usd']:.4f}")
    print(f"   综合评分: {result['score']:.2f}/100")
    print(f"   等级: {result['grade']}")


def evaluate_all_agents(args):
    """评估所有 Agent"""
    evaluator = Evaluator()
    
    results = evaluator.evaluate_all_agents()
    
    print(f"📊 所有 Agent 评估:")
    for result in results:
        print(f"   - {result['agent_id']}: {result['score']:.2f}/100 ({result['grade']})")


def evaluate_system(args):
    """评估系统"""
    evaluator = Evaluator()
    
    result = evaluator.evaluate_system(time_window_hours=args.time_window)
    
    print(f"🏥 系统健康度评估（最近 {args.time_window} 小时）:")
    print(f"   健康评分: {result['health_score']:.2f}/100")
    print(f"   等级: {result['grade']}")
    print(f"   事件统计:")
    print(f"     - 总事件: {result['events']['total']}")
    print(f"     - 错误事件: {result['events']['error']}")
    print(f"     - 警告事件: {result['events']['warning']}")
    print(f"     - 错误率: {result['events']['error_rate']:.2%}")
    print(f"   任务统计:")
    print(f"     - 总任务: {result['tasks']['total']}")
    print(f"     - 成功率: {result['tasks']['success_rate']:.2%}")
    print(f"   Agent 统计:")
    print(f"     - Agent 数量: {result['agents']['total']}")
    print(f"     - 平均评分: {result['agents']['avg_score']:.2f}/100")


def evaluate_improvement(args):
    """评估改进"""
    evaluator = Evaluator()
    
    result = evaluator.evaluate_improvement(
        agent_id=args.agent_id,
        before_window_hours=args.before_window,
        after_window_hours=args.after_window
    )
    
    if result['status'] != 'ok':
        print(f"⚠️  {result['status']}")
        return
    
    print(f"📈 改进评估: {result['agent_id']}")
    print(f"   改进前:")
    print(f"     - 任务数: {result['before']['tasks']}")
    print(f"     - 成功率: {result['before']['success_rate']:.2%}")
    print(f"     - 平均耗时: {result['before']['avg_duration_ms']:.0f} ms")
    print(f"   改进后:")
    print(f"     - 任务数: {result['after']['tasks']}")
    print(f"     - 成功率: {result['after']['success_rate']:.2%}")
    print(f"     - 平均耗时: {result['after']['avg_duration_ms']:.0f} ms")
    print(f"   改进幅度:")
    print(f"     - 成功率提升: {result['improvement']['success_rate_delta']:.2f}%")
    print(f"     - 耗时降低: {result['improvement']['duration_delta_pct']:.2f}%")
    print(f"     - 综合评分: {result['improvement']['overall_score']:.2f}")


def generate_report(args):
    """生成报告"""
    evaluator = Evaluator()
    
    report = evaluator.generate_report(time_window_hours=args.time_window)
    
    print(f"📄 评估报告已生成:")
    print(f"   时间: {report['timestamp']}")
    print(f"   时间窗口: {report['time_window_hours']} 小时")
    print(f"   系统健康度: {report['system']['health_score']:.2f}/100 ({report['system']['grade']})")
    print(f"   报告已保存到: {evaluator.results_dir}")


def main():
    parser = argparse.ArgumentParser(description="Evaluator CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # tasks
    tasks_parser = subparsers.add_parser("tasks", help="评估任务")
    tasks_parser.add_argument("--time-window", type=int, default=24, help="时间窗口（小时）")
    tasks_parser.add_argument("--task-type", help="任务类型")
    
    # agent
    agent_parser = subparsers.add_parser("agent", help="评估 Agent")
    agent_parser.add_argument("--agent-id", required=True, help="Agent ID")
    
    # agents
    agents_parser = subparsers.add_parser("agents", help="评估所有 Agent")
    
    # system
    system_parser = subparsers.add_parser("system", help="评估系统")
    system_parser.add_argument("--time-window", type=int, default=24, help="时间窗口（小时）")
    
    # improvement
    improvement_parser = subparsers.add_parser("improvement", help="评估改进")
    improvement_parser.add_argument("--agent-id", required=True, help="Agent ID")
    improvement_parser.add_argument("--before-window", type=int, default=48, help="改进前时间窗口（小时）")
    improvement_parser.add_argument("--after-window", type=int, default=24, help="改进后时间窗口（小时）")
    
    # report
    report_parser = subparsers.add_parser("report", help="生成报告")
    report_parser.add_argument("--time-window", type=int, default=24, help="时间窗口（小时）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "tasks": evaluate_tasks,
        "agent": evaluate_agent,
        "agents": evaluate_all_agents,
        "system": evaluate_system,
        "improvement": evaluate_improvement,
        "report": generate_report
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
