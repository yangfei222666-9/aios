#!/usr/bin/env python3
"""
批量修改 cron jobs 的 delivery mode
新规则：
- 日常维护类（备份、清理、优化、安全、学习）→ delivery: none
- 监控类（健康、异常、资源、自愈）→ delivery: none
- 只有真正需要人看的 → 保留 announce
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

JOBS_FILE = Path(r"C:\Users\A\.openclaw\cron\jobs.json")

# 应该改成静默的任务名关键词
SILENT_KEYWORDS = [
    "健康监控", "Anomaly Detector", "Self-Healing", "自愈",
    "安全守护", "Security Agent", "安全审计",
    "Optimizer Agent", "资源优化", "AIOS 优化",
    "Monitor Agent", "系统监控",
    "Notification Manager Agent", "通知管理",
    "Learning Agent", "自动学习", "AIOS 学习",
    "Meta-Agent", "自适应调整",
    "Backup Agent", "数据备份",
    "Knowledge Graph", "知识图谱",
    "Experiment Agent", "实验优化",
    "Prediction Agent", "预测预警",
    "Task Scheduler Agent", "任务调度",
    "每日自动清理", "每日数据备份",
    "每晚学习总结",
    "AIOS 产品化", "AIOS 性能优化",
    "AIOS 功能开发", "AIOS 竞品分析",
    "Agent 最佳实践",
    "feedback_monitor",
    "AIOS Heartbeat",
    "AIOS Cleanup",
    "Daily GitHub Push",
    "hexagram-daily",
    "meta_meta_observation",
    "意识观察日志",
    "memory_eval",
    "task-exec-format",
]

# 应该保留 announce 的任务
KEEP_ANNOUNCE = [
    "每周健康周报",
    "Reviewer 代码审查",
    "Analyst Agent 每日简报",
    "Agent 定时任务检查",
    "AIOS Alert Dispatcher",
    "世界杯",
    "周末 AIOS 大版本开发",
]

def should_silence(name):
    """判断任务是否应该静默"""
    # 先检查是否在保留列表
    for keep in KEEP_ANNOUNCE:
        if keep in name:
            return False
    # 再检查是否匹配静默关键词
    for kw in SILENT_KEYWORDS:
        if kw in name:
            return True
    return False

def main():
    data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    
    changed = []
    unchanged = []
    
    for job in data["jobs"]:
        name = job.get("name", "")
        delivery = job.get("delivery", {})
        current_mode = delivery.get("mode", "none")
        enabled = job.get("enabled", True)
        
        if not enabled:
            continue
            
        if should_silence(name) and current_mode == "announce":
            old_mode = current_mode
            job["delivery"] = {"mode": "none"}
            changed.append(f"  ✅ {name}: announce → none")
        elif current_mode == "announce":
            unchanged.append(f"  ⏭️ {name}: 保留 announce")
    
    # 备份原文件
    backup = JOBS_FILE.with_suffix(f".json.bak-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(JOBS_FILE, backup)
    print(f"备份: {backup}")
    
    # 写入修改
    JOBS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n已修改 {len(changed)} 个任务:")
    for c in changed:
        print(c)
    
    print(f"\n保留 announce {len(unchanged)} 个任务:")
    for u in unchanged:
        print(u)

if __name__ == "__main__":
    main()
