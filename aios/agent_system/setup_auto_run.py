"""
快速启动AIOS自动运行
将Cron任务添加到OpenClaw配置
"""
import json
from pathlib import Path


def create_cron_commands():
    """生成添加Cron任务的命令"""
    cron_file = Path(__file__).parent / "daily_tasks_cron.json"
    
    with open(cron_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    
    print("=== AIOS自动运行设置 ===\n")
    print("方法1：使用OpenClaw Cron工具（推荐）\n")
    
    # 生成添加命令
    for i, task in enumerate(tasks[:3], 1):  # 先添加前3个作为示例
        schedule = task["schedule"]
        payload = task["payload"]
        
        print(f"{i}. {task['name']}")
        print(f"   时间: {schedule['expr']}")
        print(f"   命令:")
        print(f'   openclaw cron add --name "{task["name"]}" --schedule "{schedule["expr"]}" --text "{payload["text"]}"')
        print()
    
    print("方法2：批量添加所有任务\n")
    print("将以下内容添加到OpenClaw配置文件的cron部分：\n")
    
    # 生成配置片段
    config_snippet = {
        "cron": {
            "jobs": tasks
        }
    }
    
    print(json.dumps(config_snippet, ensure_ascii=False, indent=2))
    
    print("\n方法3：使用配置补丁文件\n")
    
    # 创建补丁文件
    patch_file = Path(__file__).parent / "openclaw_config_patch.json"
    with open(patch_file, "w", encoding="utf-8") as f:
        json.dump(config_snippet, f, ensure_ascii=False, indent=2)
    
    print(f"已创建配置补丁文件: {patch_file}")
    print("使用命令应用补丁:")
    print(f"openclaw config patch {patch_file}")


def create_quick_start_script():
    """创建快速启动脚本"""
    script = """#!/bin/bash
# AIOS 快速启动脚本

echo "=== AIOS 自动运行启动 ==="

# 1. 添加核心Cron任务
echo "添加核心任务..."

# 系统健康检查（每小时）
openclaw cron add --name "系统健康检查" --schedule "0 * * * *" --text "执行任务: 检查AIOS系统健康度，生成报告"

# 卦象监控（每小时）
openclaw cron add --name "卦象监控" --schedule "0 * * * *" --text "执行任务: 检查当前系统卦象，记录变化"

# GitHub每日搜索（每天9点）
openclaw cron add --name "GitHub每日搜索" --schedule "0 9 * * *" --text "执行任务: 搜索GitHub最新的AIOS、Agent System、Self-Improving相关项目"

# 数据备份（每天9点）
openclaw cron add --name "数据备份" --schedule "0 9 * * *" --text "执行任务: 备份重要数据（events.jsonl, agents.json等）"

echo "核心任务已添加！"
echo ""
echo "查看已添加的任务:"
echo "openclaw cron list"
echo ""
echo "手动触发任务:"
echo "openclaw cron run --name '系统健康检查'"
"""
    
    script_file = Path(__file__).parent / "start_aios_auto.sh"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)
    
    print(f"\n已创建快速启动脚本: {script_file}")
    print("使用方法:")
    print(f"bash {script_file}")


if __name__ == "__main__":
    create_cron_commands()
    create_quick_start_script()
    
    print("\n=== 下一步 ===")
    print("1. 选择一种方法添加Cron任务")
    print("2. 验证任务已添加: openclaw cron list")
    print("3. 等待任务自动执行")
    print("4. 查看执行历史: openclaw cron runs --name '系统健康检查'")
