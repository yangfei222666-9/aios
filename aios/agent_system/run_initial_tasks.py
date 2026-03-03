"""
立即执行几个简单任务，产生初始数据
"""
import json
import time
import random
from datetime import datetime
from pathlib import Path


def simulate_task_execution(task_name, agent, duration, success_rate=0.8):
    """模拟任务执行"""
    start_time = time.time()
    
    # 模拟执行
    time.sleep(0.1)  # 快速模拟
    
    # 随机决定成功/失败
    success = random.random() < success_rate
    
    end_time = time.time()
    actual_duration = end_time - start_time
    
    return {
        "timestamp": datetime.now().isoformat(),
        "task_name": task_name,
        "agent": agent,
        "status": "completed" if success else "failed",
        "duration": actual_duration,
        "cost": actual_duration * 0.001,  # 模拟成本
    }


def main():
    """执行初始任务"""
    print("=== 执行初始任务，产生数据 ===\n")
    
    # 要执行的任务
    tasks_to_run = [
        ("系统健康检查", "System_Monitor", 1, 0.9),
        ("磁盘空间检查", "Disk_Monitor", 2, 0.95),
        ("代码质量审查", "Code_Reviewer", 3, 0.7),
        ("GitHub每日搜索", "GitHub_Researcher", 5, 0.8),
        ("数据备份", "Backup_Agent", 2, 0.9),
    ]
    
    results = []
    
    for task_name, agent, duration, success_rate in tasks_to_run:
        print(f"[执行] {task_name} ({agent})...")
        result = simulate_task_execution(task_name, agent, duration, success_rate)
        results.append(result)
        
        status_icon = "[OK]" if result["status"] == "completed" else "[FAIL]"
        print(f"  {status_icon} 状态: {result['status']}, 耗时: {result['duration']:.2f}s\n")
    
    # 保存到 tasks.jsonl
    tasks_file = Path(__file__).parent / "data" / "tasks.jsonl"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(tasks_file, "a", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    print(f"[OK] 已保存 {len(results)} 个任务结果到: {tasks_file}")
    
    # 统计
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = len(results) - completed
    success_rate = completed / len(results) * 100
    
    print(f"\n=== 统计 ===")
    print(f"总任务数: {len(results)}")
    print(f"成功: {completed}")
    print(f"失败: {failed}")
    print(f"成功率: {success_rate:.1f}%")
    
    print(f"\n现在可以运行模式识别了:")
    print(f"cd C:\\Users\\A\\.openclaw\\workspace\\aios\\pattern_recognition")
    print(f"python pattern_cli.py analyze")


if __name__ == "__main__":
    main()
