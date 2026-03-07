"""
Runtime v2 CLI - Task Submission Interface

用法：
    python cli.py submit --type code --desc "refactor module" --priority high
    python cli.py list
    python cli.py status
"""

import argparse
import json
from pathlib import Path

from .queue import get_queue
from .state import get_state


def cmd_submit(args):
    """提交任务"""
    queue = get_queue()
    
    task_id = queue.enqueue(
        task_type=args.type,
        description=args.desc,
        priority=args.priority,
        source="cli"
    )
    
    print(f"[OK] Task submitted: {task_id}")
    print(f"  Type: {args.type}")
    print(f"  Description: {args.desc}")
    print(f"  Priority: {args.priority}")


def cmd_list(args):
    """列出任务"""
    state = get_state()
    
    if args.filter == "pending":
        tasks = state.list_pending_tasks()
    elif args.filter == "running":
        tasks = state.list_running_tasks()
    elif args.filter == "completed":
        tasks = state.list_completed_tasks()
    elif args.filter == "failed":
        tasks = state.list_failed_tasks()
    else:
        # 列出所有任务
        tasks = (
            state.list_pending_tasks() +
            state.list_running_tasks() +
            state.list_completed_tasks() +
            state.list_failed_tasks()
        )
    
    if not tasks:
        print(f"[INFO] No {args.filter} tasks")
        return
    
    print(f"[INFO] {len(tasks)} {args.filter} tasks:")
    for task in tasks:
        task_id = task["task_id"]
        task_state = task["state"]
        task_data = task["task_data"]
        task_type = task_data.get("type", "unknown")
        description = task_data.get("description", "")
        
        print(f"  {task_id} | {task_state} | {task_type} | {description[:50]}")


def cmd_status(args):
    """显示系统状态"""
    state = get_state()
    
    pending = len(state.list_pending_tasks())
    running = len(state.list_running_tasks())
    completed = len(state.list_completed_tasks())
    failed = len(state.list_failed_tasks())
    
    print("[RUNTIME STATUS]")
    print(f"  Pending: {pending}")
    print(f"  Running: {running}")
    print(f"  Completed: {completed}")
    print(f"  Failed: {failed}")
    print(f"  Total: {pending + running + completed + failed}")


def main():
    parser = argparse.ArgumentParser(description="Runtime v2 CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # submit 命令
    submit_parser = subparsers.add_parser("submit", help="Submit a task")
    submit_parser.add_argument("--type", required=True, choices=["code", "analysis", "monitor"], help="Task type")
    submit_parser.add_argument("--desc", required=True, help="Task description")
    submit_parser.add_argument("--priority", default="normal", choices=["high", "normal", "low"], help="Task priority")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--filter", default="all", choices=["all", "pending", "running", "completed", "failed"], help="Filter tasks")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="Show runtime status")
    
    args = parser.parse_args()
    
    if args.command == "submit":
        cmd_submit(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
