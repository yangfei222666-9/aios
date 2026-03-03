"""
制造卦象变化 - 执行不同成功率的任务批次
"""
import json
import time
import random
from datetime import datetime
from pathlib import Path


def execute_batch(name, count, success_rate):
    """执行一批任务"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 执行 {name}")
    print(f"  任务数: {count}, 目标成功率: {success_rate:.0%}")
    
    data_dir = Path(__file__).parent / "data"
    results = []
    
    for i in range(count):
        success = random.random() < success_rate
        result = {
            "timestamp": datetime.now().isoformat(),
            "task_name": f"{name}_task_{i+1}",
            "agent": f"{name}_Agent",
            "status": "completed" if success else "failed",
            "duration": random.uniform(10, 30),
            "cost": 0.01,
        }
        results.append(result)
    
    # 保存
    with open(data_dir / "tasks.jsonl", "a", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    completed = sum(1 for r in results if r["status"] == "completed")
    print(f"  实际成功率: {completed/count:.0%}")


def main():
    """主函数 - 制造不同的系统状态"""
    print("=== 制造卦象变化 ===")
    print("将执行不同成功率的任务批次，观察卦象变化\n")
    
    # 第1批：高成功率（应该是泰卦或类似）
    execute_batch("HighSuccess", 30, 0.95)
    time.sleep(35)  # 等待观察器检查
    
    # 第2批：中等成功率（应该是中间卦象）
    execute_batch("MediumSuccess", 30, 0.70)
    time.sleep(35)
    
    # 第3批：低成功率（应该是否卦或大过卦）
    execute_batch("LowSuccess", 30, 0.30)
    time.sleep(35)
    
    # 第4批：恢复高成功率
    execute_batch("Recovery", 30, 0.95)
    time.sleep(35)
    
    print("\n=== 完成 ===")
    print("已执行4批不同成功率的任务")
    print("观察器应该记录到卦象变化")


if __name__ == "__main__":
    main()
