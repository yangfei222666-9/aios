"""
分析卦象变化历史
"""
import json
from pathlib import Path
from datetime import datetime


def analyze_task_batches():
    """分析任务批次和对应的卦象"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "pattern_recognition"))
    
    from change_detector import SystemChangeMonitor
    from hexagram_patterns import HexagramMatcher
    from hexagram_patterns_extended import extend_hexagram_patterns
    
    extend_hexagram_patterns()
    
    data_dir = Path(__file__).parent / "data"
    tasks_file = data_dir / "tasks.jsonl"
    
    # 加载所有任务
    tasks = []
    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            tasks.append(json.loads(line))
    
    # 按agent分组
    batches = {}
    for task in tasks:
        agent = task.get("agent", "unknown")
        if agent not in batches:
            batches[agent] = []
        batches[agent].append(task)
    
    print("=== 任务批次分析 ===\n")
    
    # 分析每个批次
    for agent in ["HighSuccess_Agent", "MediumSuccess_Agent", "LowSuccess_Agent", "Recovery_Agent"]:
        if agent not in batches:
            continue
        
        batch_tasks = batches[agent]
        completed = sum(1 for t in batch_tasks if t["status"] == "completed")
        total = len(batch_tasks)
        success_rate = completed / total if total > 0 else 0
        
        print(f"【{agent}】")
        print(f"  任务数: {total}")
        print(f"  成功: {completed}")
        print(f"  失败: {total - completed}")
        print(f"  成功率: {success_rate:.1%}")
        
        # 模拟这个批次的系统状态
        if success_rate > 0.85:
            expected_pattern = "泰卦或类似（顺利期）"
        elif success_rate > 0.60:
            expected_pattern = "中间卦象（稳定期）"
        elif success_rate > 0.40:
            expected_pattern = "屯卦或类似（困难期）"
        else:
            expected_pattern = "否卦或大过卦（危机期）"
        
        print(f"  预期卦象: {expected_pattern}")
        print()
    
    # 分析整体趋势
    print("=== 整体趋势 ===")
    print(f"总任务数: {len(tasks)}")
    
    completed = sum(1 for t in tasks if t["status"] == "completed")
    print(f"总成功率: {completed/len(tasks):.1%}")
    
    # 按时间顺序分析（每30个任务一组）
    print("\n=== 时间序列分析（每30个任务一组）===")
    window_size = 30
    for i in range(0, len(tasks), window_size):
        window = tasks[i:i+window_size]
        if len(window) < 10:
            break
        
        completed = sum(1 for t in window if t["status"] == "completed")
        success_rate = completed / len(window)
        
        first_time = datetime.fromisoformat(window[0]["timestamp"]).strftime("%H:%M:%S")
        last_time = datetime.fromisoformat(window[-1]["timestamp"]).strftime("%H:%M:%S")
        
        print(f"任务 {i+1}-{i+len(window)} ({first_time} - {last_time})")
        print(f"  成功率: {success_rate:.1%}")
        
        # 简单的卦象预测
        if success_rate > 0.85:
            pattern = "泰卦（顺利）"
        elif success_rate > 0.60:
            pattern = "恒卦（稳定）"
        elif success_rate > 0.40:
            pattern = "屯卦（困难）"
        else:
            pattern = "否卦/大过卦（危机）"
        
        print(f"  预期卦象: {pattern}")
        print()


if __name__ == "__main__":
    analyze_task_batches()
