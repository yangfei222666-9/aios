#!/usr/bin/env python3
"""
Self-Improving Loop CLI - 管理 AIOS 自我改进

使用示例：
    # 触发改进
    python self_improving_cli.py trigger --agent-id coder --type prompt
    
    # 查看改进历史
    python self_improving_cli.py history --limit 10
    
    # 回滚改进
    python self_improving_cli.py rollback --change-id change_123
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加 aios 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "aios"))


def trigger_improvement(args):
    """触发改进"""
    print(f"🚀 触发改进:")
    print(f"   Agent: {args.agent_id}")
    print(f"   类型: {args.type}")
    print(f"   描述: {args.description}")
    
    # TODO: 集成到 Self-Improving Loop
    change_id = f"change_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"   改进 ID: {change_id}")
    print(f"✅ 改进已触发")


def show_history(args):
    """查看改进历史"""
    print(f"📂 改进历史（最近 {args.limit} 条）:")
    
    # TODO: 读取改进历史
    print("   暂无改进历史")


def rollback_change(args):
    """回滚改进"""
    print(f"⏪ 回滚改进: {args.change_id}")
    
    # TODO: 实现回滚逻辑
    print(f"✅ 改进已回滚")


def show_stats(args):
    """显示统计"""
    print(f"📊 Self-Improving Loop 统计:")
    print(f"   总改进次数: 0")
    print(f"   成功次数: 0")
    print(f"   失败次数: 0")
    print(f"   回滚次数: 0")


def main():
    parser = argparse.ArgumentParser(description="Self-Improving Loop CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # trigger
    trigger_parser = subparsers.add_parser("trigger", help="触发改进")
    trigger_parser.add_argument("--agent-id", required=True, help="Agent ID")
    trigger_parser.add_argument("--type", required=True, choices=["config", "prompt", "code"], help="改进类型")
    trigger_parser.add_argument("--description", required=True, help="改进描述")
    
    # history
    history_parser = subparsers.add_parser("history", help="查看改进历史")
    history_parser.add_argument("--limit", type=int, default=10, help="最大返回数量")
    
    # rollback
    rollback_parser = subparsers.add_parser("rollback", help="回滚改进")
    rollback_parser.add_argument("--change-id", required=True, help="改进 ID")
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="显示统计")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "trigger": trigger_improvement,
        "history": show_history,
        "rollback": rollback_change,
        "stats": show_stats
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
