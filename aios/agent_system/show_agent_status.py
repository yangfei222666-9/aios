"""
查看全部 Agent 信息和工作状态
"""
import json
from pathlib import Path
from datetime import datetime

workspace = Path("C:/Users/A/.openclaw/workspace")

# 1. 读取 Agent 配置
agents_file = workspace / "aios" / "agent_system" / "data" / "agents.json"
agents = []
if agents_file.exists():
    with open(agents_file, encoding="utf-8") as f:
        agents = json.load(f).get("agents", [])

print("=" * 80)
print("AGENT 信息和工作状态")
print("=" * 80)
print()

# 2. 显示每个 Agent 的详细信息
for i, agent in enumerate(agents, 1):
    print(f"{i}. {agent.get('id', 'unknown')}")
    print(f"   类型: {agent.get('type', 'unknown')}")
    print(f"   环境: {agent.get('env', 'unknown')}")
    print(f"   模型: {agent.get('model', 'unknown')}")
    print(f"   状态: {'✅ active' if agent.get('status') == 'active' else '❌ inactive'}")
    
    # 角色信息
    if agent.get('role'):
        print(f"   角色: {agent.get('role')}")
    if agent.get('goal'):
        print(f"   目标: {agent.get('goal')}")
    
    # 统计信息
    stats = agent.get('stats', {})
    completed = stats.get('tasks_completed', 0)
    failed = stats.get('tasks_failed', 0)
    total = completed + failed
    success_rate = stats.get('success_rate', 0)
    
    print(f"   任务统计:")
    print(f"     - 已完成: {completed}")
    print(f"     - 失败: {failed}")
    print(f"     - 总计: {total}")
    print(f"     - 成功率: {success_rate:.1f}%")
    
    if stats.get('avg_duration_sec'):
        print(f"     - 平均耗时: {stats['avg_duration_sec']:.1f}秒")
    
    # 配置信息
    print(f"   配置:")
    print(f"     - 超时: {agent.get('timeout', 60)}秒")
    print(f"     - 最大重试: {agent.get('max_retries', 3)}次")
    
    # 创建时间
    created = agent.get('created_at', '')
    if created:
        print(f"   创建时间: {created}")
    
    print()

# 3. 总览统计
print("=" * 80)
print("总览统计")
print("=" * 80)
print(f"总 Agent 数: {len(agents)}")
print(f"活跃 Agent: {len([a for a in agents if a.get('status') == 'active'])}")
print(f"非活跃 Agent: {len([a for a in agents if a.get('status') != 'active'])}")

# 按类型统计
types = {}
for agent in agents:
    agent_type = agent.get('type', 'unknown')
    types[agent_type] = types.get(agent_type, 0) + 1

print(f"\n按类型分布:")
for agent_type, count in types.items():
    print(f"  - {agent_type}: {count}")

# 4. 工作流执行状态
print()
print("=" * 80)
print("工作流执行状态")
print("=" * 80)

try:
    from workflow_engine import WorkflowEngine
    engine = WorkflowEngine(workspace=workspace)
    
    executions = engine.list_executions()
    print(f"总执行数: {len(executions)}")
    print(f"运行中: {len([e for e in executions if e['status'] == 'running'])}")
    print(f"已完成: {len([e for e in executions if e['status'] == 'completed'])}")
    print(f"失败: {len([e for e in executions if e['status'] == 'failed'])}")
    
    # 显示最近5个执行
    if executions:
        print(f"\n最近执行:")
        for exec in executions[-5:]:
            status_icon = "✅" if exec['status'] == 'completed' else "🔄" if exec['status'] == 'running' else "❌"
            print(f"  {status_icon} {exec['execution_id']}")
            print(f"     Agent: {exec['agent_id']}")
            print(f"     工作流: {exec['workflow_id']}")
            print(f"     状态: {exec['status']}")
            print(f"     进度: {exec['current_stage']}/{len(exec.get('stages_completed', []))+exec['current_stage']}")
except Exception as e:
    print(f"无法读取工作流状态: {e}")

# 5. 任务队列状态
print()
print("=" * 80)
print("任务队列状态")
print("=" * 80)

queue_file = workspace / "aios" / "agent_system" / "task_queue.jsonl"
if queue_file.exists():
    with open(queue_file, encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    
    print(f"队列中任务数: {len(tasks)}")
    
    # 按优先级统计
    priorities = {}
    for task in tasks:
        priority = task.get('priority', 'normal')
        priorities[priority] = priorities.get(priority, 0) + 1
    
    print(f"按优先级:")
    for priority, count in priorities.items():
        print(f"  - {priority}: {count}")
    
    # 按类型统计
    task_types = {}
    for task in tasks:
        task_type = task.get('type', 'unknown')
        task_types[task_type] = task_types.get(task_type, 0) + 1
    
    print(f"按类型:")
    for task_type, count in task_types.items():
        print(f"  - {task_type}: {count}")
else:
    print("队列为空")

print()
print("=" * 80)
