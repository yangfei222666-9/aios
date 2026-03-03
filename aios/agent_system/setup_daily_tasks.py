"""
AIOS 日常任务配置
让系统动起来，产生真实数据
"""
import json
from datetime import datetime
from pathlib import Path


# 定义日常任务
DAILY_TASKS = [
    # 每小时任务
    {
        "name": "系统健康检查",
        "description": "检查AIOS系统健康度，生成报告",
        "agent": "System_Monitor",
        "frequency": "hourly",
        "priority": "high",
        "estimated_duration": 60,
    },
    {
        "name": "卦象监控",
        "description": "检查当前系统卦象，记录变化",
        "agent": "Pattern_Monitor",
        "frequency": "hourly",
        "priority": "normal",
        "estimated_duration": 30,
    },
    
    # 每天任务
    {
        "name": "GitHub每日搜索",
        "description": "搜索GitHub最新的AIOS、Agent System、Self-Improving相关项目",
        "agent": "GitHub_Researcher",
        "frequency": "daily",
        "priority": "normal",
        "estimated_duration": 300,
    },
    {
        "name": "代码质量审查",
        "description": "审查最近修改的代码，提出改进建议",
        "agent": "Code_Reviewer",
        "frequency": "daily",
        "priority": "normal",
        "estimated_duration": 600,
    },
    {
        "name": "磁盘空间检查",
        "description": "检查磁盘空间使用率，清理临时文件",
        "agent": "Disk_Monitor",
        "frequency": "daily",
        "priority": "low",
        "estimated_duration": 120,
    },
    {
        "name": "数据备份",
        "description": "备份重要数据（events.jsonl, agents.json等）",
        "agent": "Backup_Agent",
        "frequency": "daily",
        "priority": "high",
        "estimated_duration": 180,
    },
    {
        "name": "错误日志分析",
        "description": "分析错误日志，识别高频问题",
        "agent": "Error_Analyzer",
        "frequency": "daily",
        "priority": "normal",
        "estimated_duration": 300,
    },
    {
        "name": "成本统计",
        "description": "统计每日API成本，生成报告",
        "agent": "Cost_Tracker",
        "frequency": "daily",
        "priority": "normal",
        "estimated_duration": 60,
    },
    {
        "name": "Agent状态检查",
        "description": "检查所有Agent的运行状态，识别异常",
        "agent": "Agent_Monitor",
        "frequency": "daily",
        "priority": "high",
        "estimated_duration": 120,
    },
    
    # 每周任务
    {
        "name": "性能分析",
        "description": "分析系统性能，识别瓶颈",
        "agent": "Performance_Analyzer",
        "frequency": "weekly",
        "priority": "normal",
        "estimated_duration": 900,
    },
    {
        "name": "学习新技术",
        "description": "搜索和学习AI领域的最新技术",
        "agent": "Tech_Learner",
        "frequency": "weekly",
        "priority": "low",
        "estimated_duration": 1800,
    },
    {
        "name": "架构审查",
        "description": "审查AIOS架构，提出优化建议",
        "agent": "Architecture_Reviewer",
        "frequency": "weekly",
        "priority": "normal",
        "estimated_duration": 1200,
    },
    {
        "name": "文档更新",
        "description": "更新项目文档，保持同步",
        "agent": "Doc_Writer",
        "frequency": "weekly",
        "priority": "low",
        "estimated_duration": 600,
    },
    {
        "name": "安全审计",
        "description": "检查系统安全性，识别潜在风险",
        "agent": "Security_Auditor",
        "frequency": "weekly",
        "priority": "high",
        "estimated_duration": 900,
    },
]


def create_task_queue():
    """创建任务队列"""
    task_queue = []
    
    for task_config in DAILY_TASKS:
        task = {
            "timestamp": datetime.now().isoformat(),
            "agent": task_config["agent"],
            "task": task_config["description"],
            "priority": task_config["priority"],
            "status": "pending",
            "frequency": task_config["frequency"],
            "estimated_duration": task_config["estimated_duration"],
        }
        task_queue.append(task)
    
    return task_queue


def save_task_queue(task_queue, output_file="daily_tasks.jsonl"):
    """保存任务队列"""
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, "w", encoding="utf-8") as f:
        for task in task_queue:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    return output_path


def create_cron_jobs():
    """创建Cron任务（用于定时执行）"""
    cron_jobs = []
    
    # 每小时任务
    hourly_tasks = [t for t in DAILY_TASKS if t["frequency"] == "hourly"]
    for task in hourly_tasks:
        cron_jobs.append({
            "name": task["name"],
            "schedule": {"kind": "cron", "expr": "0 * * * *", "tz": "Asia/Shanghai"},
            "payload": {
                "kind": "systemEvent",
                "text": f"执行任务: {task['description']}"
            },
            "sessionTarget": "main",
            "enabled": True
        })
    
    # 每天任务
    daily_tasks = [t for t in DAILY_TASKS if t["frequency"] == "daily"]
    for task in daily_tasks:
        cron_jobs.append({
            "name": task["name"],
            "schedule": {"kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Shanghai"},  # 每天9点
            "payload": {
                "kind": "systemEvent",
                "text": f"执行任务: {task['description']}"
            },
            "sessionTarget": "main",
            "enabled": True
        })
    
    # 每周任务
    weekly_tasks = [t for t in DAILY_TASKS if t["frequency"] == "weekly"]
    for task in weekly_tasks:
        cron_jobs.append({
            "name": task["name"],
            "schedule": {"kind": "cron", "expr": "0 9 * * 1", "tz": "Asia/Shanghai"},  # 每周一9点
            "payload": {
                "kind": "systemEvent",
                "text": f"执行任务: {task['description']}"
            },
            "sessionTarget": "main",
            "enabled": True
        })
    
    return cron_jobs


def main():
    """主函数"""
    print("=== AIOS 日常任务配置 ===\n")
    
    # 创建任务队列
    task_queue = create_task_queue()
    print(f"[OK] 创建了 {len(task_queue)} 个日常任务")
    
    # 保存任务队列
    output_path = save_task_queue(task_queue)
    print(f"[OK] 保存到: {output_path}")
    
    # 显示任务列表
    print("\n任务列表:")
    for i, task in enumerate(task_queue, 1):
        print(f"  {i}. {task['agent']} - {task['task'][:50]}...")
        print(f"     频率: {task['frequency']}, 优先级: {task['priority']}")
    
    # 创建Cron任务配置
    cron_jobs = create_cron_jobs()
    cron_file = Path(__file__).parent / "daily_tasks_cron.json"
    with open(cron_file, "w", encoding="utf-8") as f:
        json.dump(cron_jobs, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Cron配置保存到: {cron_file}")
    print(f"[OK] 共 {len(cron_jobs)} 个定时任务")
    
    print("\n下一步:")
    print("1. 这些任务会在下次心跳时自动执行")
    print("2. 或者手动运行: python heartbeat_v6.py")
    print("3. Cron任务需要手动添加到OpenClaw配置")


if __name__ == "__main__":
    main()
