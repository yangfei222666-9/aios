"""
统计任务数据
"""
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

tasks_file = Path(__file__).parent / "data" / "tasks.jsonl"
tasks = []

with open(tasks_file, "r", encoding="utf-8") as f:
    for line in f:
        tasks.append(json.loads(line))

print(f"=== 任务统计 ===")
print(f"总任务数: {len(tasks)}")

# 统计状态
status_count = Counter(t["status"] for t in tasks)
completed = status_count.get("completed", 0)
failed = status_count.get("failed", 0)

print(f"成功: {completed}")
print(f"失败: {failed}")
print(f"成功率: {completed/len(tasks):.1%}")

# 最近10个任务
print(f"\n最近10个任务:")
for task in tasks[-10:]:
    time = datetime.fromisoformat(task["timestamp"]).strftime("%H:%M:%S")
    status = task["status"]
    agent = task.get("agent", "unknown")
    print(f"  {time} - {agent:20s} - {status}")

# 按小时统计
print(f"\n按小时统计:")
hourly = {}
for task in tasks:
    hour = datetime.fromisoformat(task["timestamp"]).strftime("%Y-%m-%d %H:00")
    if hour not in hourly:
        hourly[hour] = {"total": 0, "completed": 0}
    hourly[hour]["total"] += 1
    if task["status"] == "completed":
        hourly[hour]["completed"] += 1

for hour in sorted(hourly.keys())[-5:]:
    stats = hourly[hour]
    rate = stats["completed"] / stats["total"] * 100
    print(f"  {hour}: {stats['completed']}/{stats['total']} ({rate:.0f}%)")
