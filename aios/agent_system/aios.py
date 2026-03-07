#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 统一命令行入口
集成：任务队列、Agent市场、系统监控、自我改进
"""

import argparse
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import unified paths
from paths import TASK_QUEUE

def main():
    parser = argparse.ArgumentParser(
        description="AIOS - AI Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python aios.py submit --desc "重构代码" --type code --priority high
  python aios.py list
  python aios.py health
  python aios.py market list
  python aios.py market install smart_researcher
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # ============== 任务队列命令 ==============
    submit_parser = subparsers.add_parser("submit", help="提交新任务")
    submit_parser.add_argument("--desc", required=True, help="任务描述")
    submit_parser.add_argument("--type", choices=["code", "analysis", "monitor", "research"], 
                              default="code", help="任务类型")
    submit_parser.add_argument("--priority", choices=["low", "normal", "high", "critical"],
                              default="normal", help="优先级")
    
    subparsers.add_parser("list", help="列出所有任务")
    subparsers.add_parser("health", help="系统健康检查")
    
    # ============== Agent 市场命令 ==============
    market_parser = subparsers.add_parser("market", help="ClawdHub Agent 市场")
    market_parser.add_argument("action", choices=["list", "install", "search"], 
                              help="市场操作")
    market_parser.add_argument("agent_name", nargs="?", help="Agent 名称（install 时使用）")
    market_parser.add_argument("--keyword", help="搜索关键词（search 时使用）")
    
    # ============== 自我改进命令 ==============
    subparsers.add_parser("improve", help="触发自我改进循环")
    subparsers.add_parser("stats", help="显示系统统计")
    
    # ============== 意识监控命令 ==============
    monitor_parser = subparsers.add_parser("monitor", help="意识观察监控")
    monitor_parser.add_argument("action", choices=["track"], help="监控操作")
    monitor_parser.add_argument("target", nargs="?", default="consciousness", 
                               help="监控目标（默认: consciousness）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # ============== 任务队列处理 ==============
    if args.command == "submit":
        import json
        from pathlib import Path
        from datetime import datetime
        
        # Generate task ID
        task_id = f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create task
        task = {
            "id": task_id,
            "description": args.desc,
            "type": args.type,
            "priority": args.priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        # Save to queue
        with open(TASK_QUEUE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
        
        print(f"✅ 任务已提交: {task_id}")
        print(f"   类型: {args.type}")
        print(f"   优先级: {args.priority}")
        print(f"   描述: {args.desc}")
    
    elif args.command == "list":
        import task_manager
        task_manager.list_tasks()
    
    elif args.command == "health":
        import task_manager
        task_manager.show_stats()
    
    # ============== Agent 市场处理 ==============
    elif args.command == "market":
        import agent_market
        
        if args.action == "list":
            print("\n🏪 ClawdHub Agent 市场\n")
            agent_market.list_remote_agents()
        
        elif args.action == "install":
            if not args.agent_name:
                print("❌ 错误: 请指定 Agent 名称")
                print("用法: python aios.py market install <agent_name>")
                return
            
            print(f"\n📦 正在安装 {args.agent_name}...\n")
            agent_market.install_agent(args.agent_name)
        
        elif args.action == "search":
            keyword = args.keyword or args.agent_name
            if not keyword:
                print("❌ 错误: 请指定搜索关键词")
                print("用法: python aios.py market search <keyword>")
                return
            
            print(f"\n🔍 搜索结果: {keyword}\n")
            agent_market.search_agents(keyword)
    
    # ============== 自我改进处理 ==============
    elif args.command == "improve":
        print("\n🔄 触发自我改进循环...\n")
        # TODO: 集成 self_improving_loop
        print("⚠️  功能开发中")
    
    elif args.command == "stats":
        print("\n📊 系统统计\n")
        # TODO: 集成统计模块
        print("⚠️  功能开发中")
    
    # ============== 意识监控处理 ==============
    elif args.command == "monitor":
        if args.action == "track":
            if args.target == "consciousness":
                import consciousness_tracker
                consciousness_tracker.track_consciousness()
            else:
                print(f"❌ 未知监控目标: {args.target}")
        else:
            print(f"❌ 未知监控操作: {args.action}")

if __name__ == "__main__":
    main()
