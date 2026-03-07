#!/bin/bash
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
