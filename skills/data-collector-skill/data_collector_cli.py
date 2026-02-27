#!/usr/bin/env python3
"""
DataCollector CLI - 快速记录和查询数据

使用示例：
    # 记录事件
    python data_collector_cli.py log-event --type task_started --task-id task_123
    
    # 创建任务
    python data_collector_cli.py create-task --title "实现功能" --type code
    
    # 查询任务
    python data_collector_cli.py query-tasks --status success
    
    # 更新 Agent
    python data_collector_cli.py update-agent --agent-id coder --status busy
"""

import sys
import json
import argparse
from pathlib import Path

# 添加 aios 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "aios"))

from data_collector import DataCollector


def log_event(args):
    """记录事件"""
    collector = DataCollector()
    
    event_id = collector.log_event(
        type=args.type,
        severity=args.severity,
        task_id=args.task_id,
        agent_id=args.agent_id,
        payload=json.loads(args.payload) if args.payload else {}
    )
    
    print(f"✅ 事件已记录: {event_id}")


def create_task(args):
    """创建任务"""
    collector = DataCollector()
    
    task_id = collector.create_task(
        title=args.title,
        type=args.type,
        priority=args.priority,
        agent_id=args.agent_id
    )
    
    print(f"✅ 任务已创建: {task_id}")


def update_task(args):
    """更新任务"""
    collector = DataCollector()
    
    collector.update_task(
        task_id=args.task_id,
        status=args.status
    )
    
    print(f"✅ 任务已更新: {args.task_id}")


def complete_task(args):
    """完成任务"""
    collector = DataCollector()
    
    result = json.loads(args.result) if args.result else {}
    metrics = json.loads(args.metrics) if args.metrics else {}
    
    collector.complete_task(
        task_id=args.task_id,
        status=args.status,
        result=result,
        metrics=metrics
    )
    
    print(f"✅ 任务已完成: {args.task_id}")


def query_tasks(args):
    """查询任务"""
    collector = DataCollector()
    
    tasks = collector.query_tasks(
        status=args.status,
        type=args.type,
        agent_id=args.agent_id,
        priority=args.priority,
        limit=args.limit
    )
    
    print(f"📋 找到 {len(tasks)} 个任务:")
    for task in tasks:
        print(f"  - {task['id']}: {task['title']} ({task['status']})")


def query_events(args):
    """查询事件"""
    collector = DataCollector()
    
    events = collector.query_events(
        task_id=args.task_id,
        agent_id=args.agent_id,
        type=args.type,
        severity=args.severity,
        limit=args.limit
    )
    
    print(f"📝 找到 {len(events)} 个事件:")
    for event in events:
        print(f"  - {event['id']}: {event['type']} ({event['severity']})")


def update_agent(args):
    """更新 Agent"""
    collector = DataCollector()
    
    stats = json.loads(args.stats) if args.stats else None
    
    collector.update_agent(
        agent_id=args.agent_id,
        type=args.type,
        status=args.status,
        stats=stats
    )
    
    print(f"✅ Agent 已更新: {args.agent_id}")


def get_agent(args):
    """获取 Agent"""
    collector = DataCollector()
    
    agent = collector.get_agent(args.agent_id)
    
    if agent:
        print(f"🤖 Agent: {agent['id']}")
        print(f"   类型: {agent.get('type', 'N/A')}")
        print(f"   状态: {agent.get('status', 'N/A')}")
        print(f"   统计: {agent.get('stats', {})}")
    else:
        print(f"❌ Agent 不存在: {args.agent_id}")


def record_metric(args):
    """记录指标"""
    collector = DataCollector()
    
    tags = json.loads(args.tags) if args.tags else {}
    
    collector.record_metric(
        name=args.name,
        value=args.value,
        tags=tags
    )
    
    print(f"✅ 指标已记录: {args.name} = {args.value}")


def main():
    parser = argparse.ArgumentParser(description="DataCollector CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # log-event
    log_event_parser = subparsers.add_parser("log-event", help="记录事件")
    log_event_parser.add_argument("--type", required=True, help="事件类型")
    log_event_parser.add_argument("--severity", default="info", help="严重程度")
    log_event_parser.add_argument("--task-id", help="任务 ID")
    log_event_parser.add_argument("--agent-id", help="Agent ID")
    log_event_parser.add_argument("--payload", help="额外数据（JSON）")
    
    # create-task
    create_task_parser = subparsers.add_parser("create-task", help="创建任务")
    create_task_parser.add_argument("--title", required=True, help="任务标题")
    create_task_parser.add_argument("--type", required=True, help="任务类型")
    create_task_parser.add_argument("--priority", default="normal", help="优先级")
    create_task_parser.add_argument("--agent-id", help="Agent ID")
    
    # update-task
    update_task_parser = subparsers.add_parser("update-task", help="更新任务")
    update_task_parser.add_argument("--task-id", required=True, help="任务 ID")
    update_task_parser.add_argument("--status", required=True, help="状态")
    
    # complete-task
    complete_task_parser = subparsers.add_parser("complete-task", help="完成任务")
    complete_task_parser.add_argument("--task-id", required=True, help="任务 ID")
    complete_task_parser.add_argument("--status", default="success", help="状态")
    complete_task_parser.add_argument("--result", help="结果（JSON）")
    complete_task_parser.add_argument("--metrics", help="指标（JSON）")
    
    # query-tasks
    query_tasks_parser = subparsers.add_parser("query-tasks", help="查询任务")
    query_tasks_parser.add_argument("--status", help="状态")
    query_tasks_parser.add_argument("--type", help="类型")
    query_tasks_parser.add_argument("--agent-id", help="Agent ID")
    query_tasks_parser.add_argument("--priority", help="优先级")
    query_tasks_parser.add_argument("--limit", type=int, help="最大返回数量")
    
    # query-events
    query_events_parser = subparsers.add_parser("query-events", help="查询事件")
    query_events_parser.add_argument("--task-id", help="任务 ID")
    query_events_parser.add_argument("--agent-id", help="Agent ID")
    query_events_parser.add_argument("--type", help="事件类型")
    query_events_parser.add_argument("--severity", help="严重程度")
    query_events_parser.add_argument("--limit", type=int, help="最大返回数量")
    
    # update-agent
    update_agent_parser = subparsers.add_parser("update-agent", help="更新 Agent")
    update_agent_parser.add_argument("--agent-id", required=True, help="Agent ID")
    update_agent_parser.add_argument("--type", help="Agent 类型")
    update_agent_parser.add_argument("--status", help="状态")
    update_agent_parser.add_argument("--stats", help="统计数据（JSON）")
    
    # get-agent
    get_agent_parser = subparsers.add_parser("get-agent", help="获取 Agent")
    get_agent_parser.add_argument("--agent-id", required=True, help="Agent ID")
    
    # record-metric
    record_metric_parser = subparsers.add_parser("record-metric", help="记录指标")
    record_metric_parser.add_argument("--name", required=True, help="指标名称")
    record_metric_parser.add_argument("--value", type=float, required=True, help="指标值")
    record_metric_parser.add_argument("--tags", help="标签（JSON）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "log-event": log_event,
        "create-task": create_task,
        "update-task": update_task,
        "complete-task": complete_task,
        "query-tasks": query_tasks,
        "query-events": query_events,
        "update-agent": update_agent,
        "get-agent": get_agent,
        "record-metric": record_metric
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
