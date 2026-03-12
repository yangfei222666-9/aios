"""
执行时延异常检测 - 慢执行注入测试

模拟一次慢执行，验证检测器能否正确识别。
"""

import json
import time
from pathlib import Path
from datetime import datetime


def inject_slow_execution():
    """注入一次慢执行记录"""
    
    # 读取最后一条记录作为模板
    records_path = Path(__file__).parent / "data" / "agent_execution_record.jsonl"
    
    if not records_path.exists():
        print("❌ agent_execution_record.jsonl 不存在")
        return
    
    with open(records_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            print("❌ 没有历史记录")
            return
        
        # 找到最后一条成功记录
        last_record = None
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("outcome") == "success":
                    last_record = record
                    break
            except json.JSONDecodeError:
                continue
        
        if not last_record:
            print("❌ 没有成功记录")
            return
    
    # 创建慢执行记录（10x 正常时间）
    slow_record = last_record.copy()
    slow_record["task_id"] = f"slow-test-{int(time.time())}"
    slow_record["start_time"] = datetime.now().isoformat()
    slow_record["end_time"] = datetime.now().isoformat()
    
    # 注入慢执行时间（假设正常是 1ms，注入 10ms）
    original_duration = slow_record.get("duration_sec", 0.001)
    slow_record["duration_sec"] = original_duration * 10
    
    # 写入记录
    with open(records_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(slow_record, ensure_ascii=False) + "\n")
    
    print(f"✅ 注入慢执行记录:")
    print(f"   Agent: {slow_record.get('agent_name', 'unknown')}")
    print(f"   原始耗时: {original_duration * 1000:.2f}ms")
    print(f"   注入耗时: {slow_record['duration_sec'] * 1000:.2f}ms")
    print(f"   倍数: {slow_record['duration_sec'] / original_duration:.1f}x")
    
    return slow_record


def run_detection():
    """运行检测器"""
    from detectors.exec_latency_detector import ExecLatencyDetector
    
    print(f"\n运行执行时延异常检测...")
    
    # 初始化检测器
    detector = ExecLatencyDetector()
    
    # 加载基线
    records_path = Path(__file__).parent / "data" / "agent_execution_record.jsonl"
    detector.load_baselines(records_path)
    
    # 读取最后一条记录
    with open(records_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        last_line = lines[-1].strip()
        record = json.loads(last_line)
    
    entity_id = record.get("agent_name") or record.get("task_id", "unknown")
    duration_ms = record["duration_sec"] * 1000
    
    # 检查
    result = detector.check(entity_id, duration_ms)
    
    print(f"\n检测结果:")
    print(f"   实体: {entity_id}")
    print(f"   状态: {result['status']}")
    print(f"   严重级别: {result['severity']}")
    print(f"   当前耗时: {result['current_duration_ms']}ms")
    print(f"   中位数: {result['median_ms']}ms")
    print(f"   偏离比例: {result['deviation_ratio']}x")
    print(f"   连续慢执行: {result['consecutive_slow_count']}")
    print(f"   原因: {result['reason']}")
    
    # 生成事件
    if result["status"] not in ("normal", "cold_start"):
        event = detector.generate_event(entity_id, "agent", result)
        if event:
            print(f"\n生成事件:")
            print(f"   事件ID: {event['event_id']}")
            print(f"   摘要: {event['summary']}")
            print(f"   建议动作: {event['suggested_action']}")
            
            # 写入事件日志
            events_file = Path(__file__).parent / "data" / "events.jsonl"
            events_file.parent.mkdir(parents=True, exist_ok=True)
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            
            print(f"   ✅ 事件已写入: {events_file}")


def main():
    print("=" * 60)
    print("执行时延异常检测 - 慢执行注入测试")
    print("=" * 60)
    
    # 1. 注入慢执行
    slow_record = inject_slow_execution()
    
    if not slow_record:
        return
    
    # 2. 运行检测
    run_detection()
    
    print(f"\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
