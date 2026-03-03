"""
卦象变化观察器
实时监控系统状态，记录卦象变化
"""
import json
import time
from pathlib import Path
from datetime import datetime


def observe_pattern_changes(duration_minutes=10, interval_seconds=30):
    """
    观察卦象变化
    
    Args:
        duration_minutes: 观察时长（分钟）
        interval_seconds: 检查间隔（秒）
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "pattern_recognition"))
    
    from change_detector import SystemChangeMonitor
    from hexagram_patterns import HexagramMatcher
    from hexagram_patterns_extended import extend_hexagram_patterns
    
    # 扩展到64卦
    extend_hexagram_patterns()
    
    data_dir = Path(__file__).parent / "data"
    monitor = SystemChangeMonitor(data_dir)
    matcher = HexagramMatcher()
    
    # 记录历史
    history = []
    last_pattern = None
    
    print("=== 卦象变化观察器 ===")
    print(f"观察时长: {duration_minutes} 分钟")
    print(f"检查间隔: {interval_seconds} 秒")
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}\n")
    
    start_time = time.time()
    end_time = start_time + duration_minutes * 60
    check_count = 0
    
    while time.time() < end_time:
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 加载任务
        tasks = monitor.load_recent_tasks(hours=24)
        if len(tasks) == 0:
            print(f"[{current_time}] 没有任务数据，跳过")
            time.sleep(interval_seconds)
            continue
        
        # 更新检测器
        monitor.update_from_tasks(tasks)
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
        pattern, confidence = matcher.match(system_metrics)
        
        # 记录
        record = {
            "timestamp": current_time,
            "check_number": check_count,
            "total_tasks": len(tasks),
            "success_rate": success_rate,
            "pattern": pattern.name,
            "pattern_number": pattern.number,
            "confidence": confidence,
            "risk_level": pattern.risk_level,
            "trend": success_trend,
        }
        history.append(record)
        
        # 显示
        print(f"[{current_time}] 检查 #{check_count}")
        print(f"  任务数: {len(tasks)}")
        print(f"  成功率: {success_rate:.1%}")
        print(f"  趋势: {success_trend}")
        print(f"  卦象: {pattern.name} (第{pattern.number}卦)")
        print(f"  置信度: {confidence:.1%}")
        print(f"  风险: {pattern.risk_level}")
        
        # 检测变化
        if last_pattern and last_pattern != pattern.name:
            print(f"  [!] 卦象转变: {last_pattern} -> {pattern.name}")
        
        last_pattern = pattern.name
        print()
        
        # 等待下次检查
        time.sleep(interval_seconds)
    
    # 保存历史
    history_file = Path(__file__).parent / "data" / "pattern_history.jsonl"
    with open(history_file, "a", encoding="utf-8") as f:
        for record in history:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"=== 观察完成 ===")
    print(f"总检查次数: {check_count}")
    print(f"历史已保存到: {history_file}")
    
    # 统计
    patterns_seen = set(r["pattern"] for r in history)
    print(f"\n观察到的卦象: {', '.join(patterns_seen)}")
    
    # 卦象变化次数
    changes = 0
    for i in range(1, len(history)):
        if history[i]["pattern"] != history[i-1]["pattern"]:
            changes += 1
    print(f"卦象变化次数: {changes}")


def main():
    """主函数"""
    import sys
    
    # 默认观察10分钟，每30秒检查一次
    duration = 10
    interval = 30
    
    if len(sys.argv) > 1:
        duration = int(sys.argv[1])
    if len(sys.argv) > 2:
        interval = int(sys.argv[2])
    
    try:
        observe_pattern_changes(duration, interval)
    except KeyboardInterrupt:
        print("\n\n[中断] 观察已停止")


if __name__ == "__main__":
    main()
