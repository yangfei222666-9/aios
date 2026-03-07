"""
Agent 动态查看工具
显示所有 Agent 的当前状态、统计和最近活动
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from self_improving_loop import SelfImprovingLoop


def format_time_ago(timestamp_str):
    """格式化时间为"多久前"""
    if not timestamp_str:
        return "从未"
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days} 天前"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600} 小时前"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60} 分钟前"
        else:
            return f"{delta.seconds} 秒前"
    except:
        return "未知"


def show_agent_dynamics():
    """显示 Agent 动态"""
    print("=" * 80)
    print("  Agent 动态监控")
    print("=" * 80)
    
    # 读取 Agent 数据
    agents_file = Path(__file__).parent / "data" / "agents.jsonl"
    if not agents_file.exists():
        print("\n未找到 Agent 数据")
        return
    
    agents = []
    with open(agents_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                agents.append(json.loads(line))
    
    # 按状态分组
    active_agents = [a for a in agents if a.get("status") == "active"]
    archived_agents = [a for a in agents if a.get("status") == "archived"]
    
    print(f"\n[REPORT] 总览")
    print(f"  总 Agent 数: {len(agents)}")
    print(f"  活跃: {len(active_agents)}")
    print(f"  已归档: {len(archived_agents)}")
    
    # Self-Improving Loop 统计
    try:
        loop = SelfImprovingLoop()
        stats = loop.get_improvement_stats()
        print(f"\n[FIX] Self-Improving Loop")
        print(f"  总改进次数: {stats.get('total_improvements', 0)}")
        print(f"  总回滚次数: {stats.get('total_rollbacks', 0)}")
        improved = stats.get('agents_improved', [])
        if improved:
            print(f"  已改进 Agent: {', '.join(improved[:3])}")
            if len(improved) > 3:
                print(f"                 ... 还有 {len(improved) - 3} 个")
    except:
        pass
    
    # 显示活跃 Agent
    if active_agents:
        print(f"\n[OK] 活跃 Agent ({len(active_agents)})")
        print("-" * 80)
        
        for agent in active_agents:
            agent_id = agent.get("id", "unknown")
            name = agent.get("name", agent.get("template", "Unknown"))
            stats = agent.get("stats", {})
            
            # 基本信息
            print(f"\n  ID: {agent_id}")
            print(f"  名称: {name}")
            
            # 统计信息
            tasks_completed = stats.get("tasks_completed", 0)
            tasks_failed = stats.get("tasks_failed", 0)
            total_tasks = tasks_completed + tasks_failed
            success_rate = stats.get("success_rate", 0)
            
            if total_tasks > 0:
                print(f"  任务: {total_tasks} 次 (成功 {tasks_completed}, 失败 {tasks_failed})")
                print(f"  成功率: {success_rate:.1%}")
                
                avg_duration = stats.get("avg_duration_sec", 0)
                if avg_duration > 0:
                    print(f"  平均耗时: {avg_duration:.1f}s")
            else:
                print(f"  任务: 0 次 (尚未执行)")
            
            # 最后活跃时间
            last_active = stats.get("last_active")
            print(f"  最后活跃: {format_time_ago(last_active)}")
            
            # 创建时间
            created_at = agent.get("created_at")
            print(f"  创建时间: {format_time_ago(created_at)}")
    
    # 显示已归档 Agent（简略）
    if archived_agents:
        print(f"\n[PACKAGE] 已归档 Agent ({len(archived_agents)})")
        print("-" * 80)
        for agent in archived_agents[:3]:
            agent_id = agent.get("id", "unknown")
            name = agent.get("name", agent.get("template", "Unknown"))
            archived_at = agent.get("archived_at")
            reason = agent.get("archive_reason", "未知")
            print(f"  • {agent_id} ({name}) - {reason} - {format_time_ago(archived_at)}")
        
        if len(archived_agents) > 3:
            print(f"  ... 还有 {len(archived_agents) - 3} 个")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    show_agent_dynamics()
