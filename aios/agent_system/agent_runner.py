"""
AIOS Agent Runner v1.0
让所有 Agent 跑一次真实任务，验证能力
"""

import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
REGISTRY_PATH = WORKSPACE / "aios" / "agent_system" / "unified_registry.json"
RESULTS_PATH = WORKSPACE / "aios" / "agent_system" / "agent_run_results.json"

# 每个 Agent 的真实任务
AGENT_TASKS = {
    "coder": {
        "task": "写一个 Python 函数 fibonacci(n)，返回前 n 个斐波那契数列，包含类型注解和 docstring。然后写 3 个测试用例验证它。把代码保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\coder_output.py",
        "timeout": 120,
    },
    "analyst": {
        "task": "分析 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\unified_registry.json，统计：1) 每个分类有多少 Skill 2) 有脚本 vs 纯文档的比例 3) Agent 数量分布。把分析报告保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\analyst_report.md",
        "timeout": 90,
    },
    "monitor": {
        "task": "检查当前系统状态：CPU 使用率、内存使用率、磁盘使用率、Python 进程数。把结果保存为 JSON 到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\monitor_status.json",
        "timeout": 60,
    },
    "reactor": {
        "task": "检查 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system 目录下所有 .py 文件的语法是否正确（用 py_compile），列出有语法错误的文件。把结果保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\reactor_check.json",
        "timeout": 90,
    },
    "researcher": {
        "task": "搜索 GitHub 上最新的 AIOS 或 Agent OS 相关项目（2026年），找出 Star 数最高的 3 个，分析它们的核心架构。把报告保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\researcher_report.md",
        "timeout": 120,
    },
    "designer": {
        "task": "阅读 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\unified_registry.json，评估当前 Agent-Skill 架构设计，提出 3 个改进建议。把设计文档保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\designer_review.md",
        "timeout": 120,
    },
    "evolution": {
        "task": "分析 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\unified_registry.json 中所有 Agent 的 stats，计算整体健康度评分（0-100），并给出改进建议。保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\evolution_score.json",
        "timeout": 90,
    },
    "security": {
        "task": "扫描 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system 目录，检查：1) 是否有硬编码的密钥/token 2) 文件权限是否合理 3) 是否有不安全的 eval/exec 调用。保存报告到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\security_audit.md",
        "timeout": 90,
    },
    "automation": {
        "task": "写一个 PowerShell 脚本，自动清理 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system 下的 __pycache__ 目录和 .pyc 文件，统计清理了多少文件。保存脚本到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\cleanup.ps1，执行结果保存到 cleanup_result.txt",
        "timeout": 90,
    },
    "document": {
        "task": "阅读 C:\\Users\\A\\.openclaw\\workspace\\MEMORY.md，生成一份精简摘要（500字以内），提取 5 个关键词。保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\document_summary.md",
        "timeout": 90,
    },
    "tester": {
        "task": "为 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\unified_registry.py 写 5 个单元测试（测试 scan_skills, classify_skill, load_old_agents, deduplicate_agents, build_unified_registry），保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\test_unified_registry.py",
        "timeout": 120,
    },
    "game-dev": {
        "task": "用 HTML5 Canvas 写一个简单的弹球游戏（球在画布内弹跳，鼠标点击改变方向），保存到 C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system\\test_runs\\bounce_game.html",
        "timeout": 120,
    },
}


def main():
    print("=" * 60)
    print("AIOS Agent Runner v1.0")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print(f"\nLaunching {len(AGENT_TASKS)} agents...\n")
    
    # 确保输出目录存在
    test_runs = WORKSPACE / "aios" / "agent_system" / "test_runs"
    test_runs.mkdir(exist_ok=True)
    
    for agent_id, config in AGENT_TASKS.items():
        print(f"  [{agent_id}] Task: {config['task'][:60]}...")
    
    print(f"\nAll {len(AGENT_TASKS)} tasks defined.")
    print("Use sessions_spawn to execute each task.")


if __name__ == "__main__":
    main()
