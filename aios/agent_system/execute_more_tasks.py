"""
执行更多任务，提高成功率
观察卦象变化
"""
import json
import time
import random
from datetime import datetime
from pathlib import Path


def execute_task_batch(batch_name, num_tasks, success_rate=0.85):
    """执行一批任务"""
    print(f"\n=== {batch_name} ===")
    print(f"执行 {num_tasks} 个任务，目标成功率: {success_rate:.0%}\n")
    
    results = []
    agents = ["System_Monitor", "Code_Reviewer", "GitHub_Researcher", "Backup_Agent", "Performance_Analyzer"]
    
    for i in range(num_tasks):
        agent = random.choice(agents)
        task_name = f"{batch_name}_task_{i+1}"
        
        # 模拟执行
        success = random.random() < success_rate
        duration = random.uniform(5, 30)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "task_name": task_name,
            "agent": agent,
            "status": "completed" if success else "failed",
            "duration": duration,
            "cost": duration * 0.001,
        }
        results.append(result)
        
        status_icon = "[OK]" if success else "[FAIL]"
        print(f"{i+1:2d}. {agent:20s} {status_icon}")
        
        time.sleep(0.05)  # 小延迟
    
    return results


def save_results(results, data_dir):
    """保存结果"""
    tasks_file = data_dir / "tasks.jsonl"
    
    with open(tasks_file, "a", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    return tasks_file


def analyze_pattern(data_dir):
    """分析当前卦象"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "pattern_recognition"))
    
    from change_detector import SystemChangeMonitor
    from hexagram_patterns import HexagramMatcher
    from hexagram_patterns_extended import extend_hexagram_patterns
    
    # 扩展到64卦
    extend_hexagram_patterns()
    
    # 创建监控器
    monitor = SystemChangeMonitor(data_dir)
    
    # 加载任务
    tasks = monitor.load_recent_tasks(hours=24)
    if len(tasks) == 0:
        print("没有任务数据")
        return None
    
    # 更新检测器
    monitor.update_from_tasks(tasks)
    
    # 获取趋势
    trends = monitor.get_all_trends()
    
    # 计算系统指标
    success_rate = trends["success_rate"]["current_value"] or 0.5
    success_trend = trends["success_rate"]["trend"]
    
    if success_trend == "rising":
        growth_rate = 0.2
    elif success_trend == "falling":
        growth_rate = -0.2
    else:
        growth_rate = 0.0
    
    success_std = trends["success_rate"]["std_dev"] or 0.1
    stability = max(0, 1.0 - success_std * 2)
    
    avg_duration = trends["avg_duration"]["current_value"] or 30
    resource_usage = min(avg_duration / 30, 2.0) / 2
    
    system_metrics = {
        "success_rate": success_rate,
        "growth_rate": growth_rate,
        "stability": stability,
        "resource_usage": resource_usage,
    }
    
    # 匹配卦象
    matcher = HexagramMatcher()
    pattern, confidence = matcher.match(system_metrics)
    
    return {
        "total_tasks": len(tasks),
        "success_rate": success_rate,
        "pattern": pattern.name,
        "pattern_number": pattern.number,
        "confidence": confidence,
        "risk_level": pattern.risk_level,
        "strategy": pattern.strategy["priority"],
    }


def main():
    """主函数"""
    print("=== 执行更多任务，观察卦象变化 ===")
    
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 第一批：高成功率任务
    batch1 = execute_task_batch("Batch_1", 20, success_rate=0.90)
    save_results(batch1, data_dir)
    
    print("\n--- 分析当前状态 ---")
    state1 = analyze_pattern(data_dir)
    if state1:
        print(f"总任务数: {state1['total_tasks']}")
        print(f"成功率: {state1['success_rate']:.1%}")
        print(f"当前卦象: {state1['pattern']} (第{state1['pattern_number']}卦)")
        print(f"置信度: {state1['confidence']:.1%}")
        print(f"风险等级: {state1['risk_level']}")
        print(f"推荐策略: {state1['strategy']}")
    
    # 第二批：继续高成功率
    batch2 = execute_task_batch("Batch_2", 20, success_rate=0.85)
    save_results(batch2, data_dir)
    
    print("\n--- 分析当前状态 ---")
    state2 = analyze_pattern(data_dir)
    if state2:
        print(f"总任务数: {state2['total_tasks']}")
        print(f"成功率: {state2['success_rate']:.1%}")
        print(f"当前卦象: {state2['pattern']} (第{state2['pattern_number']}卦)")
        print(f"置信度: {state2['confidence']:.1%}")
        print(f"风险等级: {state2['risk_level']}")
        print(f"推荐策略: {state2['strategy']}")
    
    # 对比
    if state1 and state2:
        print("\n=== 卦象变化 ===")
        print(f"之前: {state1['pattern']} (成功率: {state1['success_rate']:.1%})")
        print(f"现在: {state2['pattern']} (成功率: {state2['success_rate']:.1%})")
        
        if state1['pattern'] != state2['pattern']:
            print(f"\n[!] 检测到卦象转变: {state1['pattern']} -> {state2['pattern']}")
            print(f"    风险变化: {state1['risk_level']} -> {state2['risk_level']}")
        else:
            print(f"\n卦象保持不变: {state2['pattern']}")


if __name__ == "__main__":
    main()
