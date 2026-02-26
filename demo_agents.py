#!/usr/bin/env python3
"""Agent 实战演示 - 直接用 sessions_spawn"""
import sys
import os
sys.path.insert(0, r"C:\Users\A\.openclaw\workspace")

# 模拟 sessions_spawn（因为我们在脚本里，没有真正的 OpenClaw API）
# 实际使用时应该用 OpenClaw 的 sessions_spawn 工具

tasks = [
    {
        "name": "数据分析专员",
        "agent": "analyst",
        "task": """分析 C:\\Users\\A\\.openclaw\\workspace\\aios\\data\\events.jsonl 最近的事件：
1. 统计各类事件数量
2. 找出最频繁的错误
3. 生成简要报告（保存到 workspace/agent_reports/analyst_report.md）"""
    },
    {
        "name": "系统监控专员",
        "agent": "monitor",
        "task": """检查系统当前状态：
1. CPU 和内存使用率（用 PowerShell Get-Counter）
2. 磁盘空间（Get-PSDrive）
3. 生成监控报告（保存到 workspace/agent_reports/monitor_report.md）"""
    },
    {
        "name": "信息研究专员",
        "agent": "researcher",
        "task": """搜索并整理最新的 AI Agent 框架（2024-2026）：
1. 列出 5 个主流框架
2. 对比核心特性
3. AIOS 的差异化优势
4. 保存到 workspace/agent_reports/research_report.md"""
    },
    {
        "name": "文档专员",
        "agent": "documenter",
        "task": """为 AIOS Agent System 编写快速入门文档：
1. 什么是 AIOS Agent System
2. 如何创建 Agent
3. 如何分配任务
4. 常见问题
5. 保存到 workspace/agent_reports/quickstart.md"""
    }
]

print("🚀 AIOS Agent 实战演示")
print("=" * 60)
print(f"准备启动 {len(tasks)} 个 Agent 执行任务...\n")

# 创建报告目录
os.makedirs("agent_reports", exist_ok=True)

for i, task_info in enumerate(tasks, 1):
    print(f"📋 任务 {i}: {task_info['name']} ({task_info['agent']})")
    print(f"   任务描述: {task_info['task'][:80]}...")
    print(f"   状态: 已入队，等待 sessions_spawn 执行\n")

print("=" * 60)
print("💡 提示：")
print("1. 这些任务会通过 sessions_spawn 创建子 Agent")
print("2. 每个 Agent 独立执行，互不干扰")
print("3. 结果会保存到 workspace/agent_reports/")
print("4. 用 'subagents list' 查看执行状态")
print("\n✅ 任务已入队！Agent 正在后台工作...")
