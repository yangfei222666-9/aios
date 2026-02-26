"""查看 Coder 失败详情"""
import json
from pathlib import Path

agents_file = Path("data/agents.json")
with open(agents_file, encoding="utf-8") as f:
    data = json.load(f)

print("=" * 80)
print("Coder-Dispatcher 失败分析")
print("=" * 80)
print()

# 找到 coder-dispatcher
coder = None
for agent in data.get("agents", []):
    if agent.get("id") == "coder-dispatcher":
        coder = agent
        break

if not coder:
    print("未找到 coder-dispatcher")
    exit(1)

print("基本信息:")
print(f"  ID: {coder.get('id')}")
print(f"  类型: {coder.get('type')}")
print(f"  状态: {coder.get('status')}")
print(f"  环境: {coder.get('env')}")
print()

print("配置:")
print(f"  模型: {coder.get('model')}")
print(f"  超时: {coder.get('timeout')}秒")
print(f"  最大重试: {coder.get('max_retries')}次")
print(f"  Thinking: {coder.get('thinking', 'N/A')}")
print()

print("角色:")
print(f"  Role: {coder.get('role')}")
print(f"  Goal: {coder.get('goal')}")
print()

print("统计:")
stats = coder.get("stats", {})
completed = stats.get("tasks_completed", 0)
failed = stats.get("tasks_failed", 0)
total = completed + failed

print(f"  完成: {completed}")
print(f"  失败: {failed}")
print(f"  总计: {total}")
print(f"  成功率: {stats.get('success_rate', 0):.1f}%")
print(f"  平均耗时: {stats.get('avg_duration_sec', 0):.1f}秒")
print()

print("=" * 80)
print("问题分析")
print("=" * 80)
print()

if failed >= 3:
    print("⚠️ Coder 连续失败 3 次")
    print()
    print("可能原因:")
    print("  1. 任务太复杂（需要拆分）")
    print("  2. 超时时间不够（当前120秒）")
    print("  3. 模型选择不当（当前 opus-4-5）")
    print("  4. 没有真实的 sessions_spawn 执行环境")
    print()
    print("建议:")
    print("  1. 在 OpenClaw 主会话中运行心跳")
    print("  2. 通过 sessions_spawn 创建真实的子 Agent")
    print("  3. 简化任务描述")
    print("  4. 增加超时到 180 秒")
else:
    print("✓ Coder 状态正常")

print()
print("=" * 80)
