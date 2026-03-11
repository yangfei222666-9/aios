#!/usr/bin/env python3
"""
统一状态适配层

所有状态推导的唯一入口。
禁止直接读取 agent['status'] 等旧字段。
"""


def get_agent_status(agent: dict) -> str:
    """
    统一 Agent 状态推导
    
    状态词表：
    - registered: 已注册，但无执行记录
    - executable: 有执行记录，但未验证
    - validated: 已验证（至少 1 次成功）
    - production-ready: 生产就绪（5+ 次成功，失败率 < 20%）
    - stable: 稳定（20+ 次成功，失败率 < 10%）
    - not-executable: 已注册但不可执行
    - archived: 已归档
    """
    stats = agent.get("stats", {})
    
    # 检查是否有执行记录
    tasks_completed = stats.get("tasks_completed", 0)
    tasks_failed = stats.get("tasks_failed", 0)
    total_tasks = tasks_completed + tasks_failed
    
    # 如果有明确的 lifecycle_status，优先使用
    if "lifecycle_status" in agent:
        return agent["lifecycle_status"]
    
    # 否则根据统计推导
    if total_tasks == 0:
        # 检查是否有 stats 字段（表示可执行但未运行）
        if stats:
            return "executable"
        return "registered"
    
    if tasks_completed == 0:
        return "not-executable"
    
    if tasks_completed < 5:
        return "validated"
    
    if tasks_completed < 20:
        failure_rate = tasks_failed / total_tasks if total_tasks > 0 else 0
        return "production-ready" if failure_rate < 0.2 else "validated"
    
    failure_rate = tasks_failed / total_tasks if total_tasks > 0 else 0
    return "stable" if failure_rate < 0.1 else "production-ready"


def get_skill_status(skill: dict) -> str:
    """
    统一 Skill 状态推导
    
    状态词表：
    - registered: 已注册，但无使用记录
    - executable: 有使用记录
    - stable: 稳定（10+ 次使用，失败率 < 10%）
    - not-executable: 已注册但不可执行
    - archived: 已归档
    """
    stats = skill.get("stats", {})
    
    uses = stats.get("uses", 0)
    failures = stats.get("failures", 0)
    
    # 如果有明确的 lifecycle_status，优先使用
    if "lifecycle_status" in skill:
        return skill["lifecycle_status"]
    
    # 否则根据统计推导
    if uses == 0:
        return "registered"
    
    if uses < 10:
        return "executable"
    
    failure_rate = failures / uses if uses > 0 else 0
    return "stable" if failure_rate < 0.1 else "executable"


def get_task_status(task: dict) -> str:
    """
    统一 Task 状态推导
    
    状态词表：
    - pending: 待处理
    - running: 运行中
    - completed: 已完成
    - failed: 失败
    """
    # Task 状态直接使用 status 字段
    return task.get("status", "pending")


def get_status_category(status: str) -> str:
    """
    获取状态分类
    
    分类：
    - healthy: registered / executable / validated / production-ready / stable
    - warning: not-executable
    - critical: archived
    """
    if status in ["registered", "executable", "validated", "production-ready", "stable"]:
        return "healthy"
    elif status == "not-executable":
        return "warning"
    elif status == "archived":
        return "critical"
    else:
        return "unknown"


def get_status_emoji(status: str) -> str:
    """获取状态对应的 emoji"""
    emoji_map = {
        "registered": "📝",
        "executable": "⚙️",
        "validated": "✅",
        "production-ready": "🚀",
        "stable": "💎",
        "not-executable": "⚠️",
        "archived": "📦",
        "pending": "⏳",
        "running": "▶️",
        "completed": "✅",
        "failed": "❌"
    }
    return emoji_map.get(status, "❓")


def get_status_description(status: str) -> str:
    """获取状态描述"""
    descriptions = {
        "registered": "已注册，但无执行记录",
        "executable": "有执行记录，但未验证",
        "validated": "已验证（至少 1 次成功）",
        "production-ready": "生产就绪（5+ 次成功，失败率 < 20%）",
        "stable": "稳定（20+ 次成功，失败率 < 10%）",
        "not-executable": "已注册但不可执行",
        "archived": "已归档",
        "pending": "待处理",
        "running": "运行中",
        "completed": "已完成",
        "failed": "失败"
    }
    return descriptions.get(status, "未知状态")
