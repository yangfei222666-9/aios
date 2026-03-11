"""
执行时延异常检测器 v0

监控 Agent 执行耗时，识别性能退化。

核心能力：
1. 维护滚动基线（最近 20 次成功执行）
2. 检测单次异常（> 2x median 或 1.5x p95）
3. 检测连续退化（连续 3 次慢）
4. 生成标准事件
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


class ExecLatencyDetector:
    """执行时延异常检测器"""
    
    def __init__(
        self,
        baseline_window: int = 20,
        min_samples: int = 5,
        warn_threshold_median: float = 2.0,
        warn_threshold_p95: float = 1.5,
        critical_threshold_median: float = 3.0,
        consecutive_slow_threshold: int = 3
    ):
        """
        Args:
            baseline_window: 滚动窗口大小（最近 N 次成功执行）
            min_samples: 最小样本数（少于此数不做判断）
            warn_threshold_median: warn 阈值（倍数 × median）
            warn_threshold_p95: warn 阈值（倍数 × p95）
            critical_threshold_median: critical 阈值（倍数 × median）
            consecutive_slow_threshold: 连续慢执行阈值
        """
        self.baseline_window = baseline_window
        self.min_samples = min_samples
        self.warn_threshold_median = warn_threshold_median
        self.warn_threshold_p95 = warn_threshold_p95
        self.critical_threshold_median = critical_threshold_median
        self.consecutive_slow_threshold = consecutive_slow_threshold
        
        # 基线存储（entity_id -> list of duration_ms）
        self.baselines: Dict[str, List[float]] = defaultdict(list)
        
        # 连续慢执行计数（entity_id -> count）
        self.consecutive_slow: Dict[str, int] = defaultdict(int)
    
    def load_baselines(self, execution_records_path: Path) -> None:
        """
        从执行记录中加载基线
        
        Args:
            execution_records_path: agent_execution_record.jsonl 路径
        """
        if not execution_records_path.exists():
            return
        
        # 按 entity_id 分组
        records_by_entity: Dict[str, List[Dict]] = defaultdict(list)
        
        with open(execution_records_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # 只取成功的记录
                    if record.get("outcome") == "success" and "duration_sec" in record:
                        entity_id = record.get("agent_name") or record.get("task_id", "unknown")
                        records_by_entity[entity_id].append(record)
                except json.JSONDecodeError:
                    continue
        
        # 为每个 entity 构建基线（最近 N 次）
        for entity_id, records in records_by_entity.items():
            # 按时间排序（最新的在后）
            records.sort(key=lambda r: r.get("end_time", ""))
            
            # 取最近 N 次
            recent_records = records[-self.baseline_window:]
            
            # 提取 duration（转为 ms）
            durations = [r["duration_sec"] * 1000 for r in recent_records]
            
            self.baselines[entity_id] = durations
    
    def update_baseline(self, entity_id: str, duration_ms: float, success: bool) -> None:
        """
        更新基线
        
        Args:
            entity_id: 实体 ID
            duration_ms: 执行时长（毫秒）
            success: 是否成功
        """
        if not success:
            return
        
        # 添加到基线
        self.baselines[entity_id].append(duration_ms)
        
        # 保持窗口大小
        if len(self.baselines[entity_id]) > self.baseline_window:
            self.baselines[entity_id] = self.baselines[entity_id][-self.baseline_window:]
    
    def check(self, entity_id: str, duration_ms: float) -> Dict[str, Any]:
        """
        检查执行时延是否异常
        
        Args:
            entity_id: 实体 ID
            duration_ms: 当前执行时长（毫秒）
        
        Returns:
            {
                "status": "normal" | "warn" | "critical" | "degraded" | "cold_start",
                "severity": "info" | "warning" | "error" | "critical",
                "current_duration_ms": float,
                "median_ms": float | None,
                "p95_ms": float | None,
                "deviation_ratio": float | None,
                "consecutive_slow_count": int,
                "baseline_samples": int,
                "reason": str
            }
        """
        baseline = self.baselines.get(entity_id, [])
        baseline_samples = len(baseline)
        
        # 冷启动保护
        if baseline_samples < self.min_samples:
            return {
                "status": "cold_start",
                "severity": "info",
                "current_duration_ms": duration_ms,
                "median_ms": None,
                "p95_ms": None,
                "deviation_ratio": None,
                "consecutive_slow_count": 0,
                "baseline_samples": baseline_samples,
                "reason": f"baseline_insufficient (need {self.min_samples}, got {baseline_samples})"
            }
        
        # 计算统计量
        sorted_baseline = sorted(baseline)
        median_ms = sorted_baseline[len(sorted_baseline) // 2]
        p95_index = int(len(sorted_baseline) * 0.95)
        p95_ms = sorted_baseline[p95_index]
        
        # 计算偏离比例
        deviation_ratio = duration_ms / median_ms if median_ms > 0 else 0
        
        # 判断异常级别
        is_warn = duration_ms > max(
            self.warn_threshold_median * median_ms,
            self.warn_threshold_p95 * p95_ms
        )
        is_critical = duration_ms > self.critical_threshold_median * median_ms
        
        # 更新连续慢执行计数
        if is_warn:
            self.consecutive_slow[entity_id] += 1
        else:
            self.consecutive_slow[entity_id] = 0
        
        consecutive_count = self.consecutive_slow[entity_id]
        
        # 确定状态
        if is_critical:
            status = "critical"
            severity = "critical"
            reason = f"duration {deviation_ratio:.1f}x median (critical threshold: {self.critical_threshold_median}x)"
        elif consecutive_count >= self.consecutive_slow_threshold:
            status = "degraded"
            severity = "error"
            reason = f"consecutive slow executions: {consecutive_count} (threshold: {self.consecutive_slow_threshold})"
        elif is_warn:
            status = "warn"
            severity = "warning"
            reason = f"duration {deviation_ratio:.1f}x median (warn threshold: {self.warn_threshold_median}x)"
        else:
            status = "normal"
            severity = "info"
            reason = "within normal range"
        
        return {
            "status": status,
            "severity": severity,
            "current_duration_ms": round(duration_ms, 2),
            "median_ms": round(median_ms, 2),
            "p95_ms": round(p95_ms, 2),
            "deviation_ratio": round(deviation_ratio, 2),
            "consecutive_slow_count": consecutive_count,
            "baseline_samples": baseline_samples,
            "reason": reason
        }
    
    def generate_event(
        self,
        entity_id: str,
        entity_type: str,
        check_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        从检查结果生成标准事件
        
        Args:
            entity_id: 实体 ID
            entity_type: 实体类型（agent / task / service）
            check_result: check() 的返回结果
        
        Returns:
            标准事件对象（如果不需要生成事件则返回 None）
        """
        status = check_result["status"]
        
        # 正常和冷启动不生成事件
        if status in ("normal", "cold_start"):
            return None
        
        severity = check_result["severity"]
        current_duration = check_result["current_duration_ms"]
        median = check_result["median_ms"]
        deviation = check_result["deviation_ratio"]
        consecutive = check_result["consecutive_slow_count"]
        reason = check_result["reason"]
        
        # 生成摘要
        if status == "critical":
            summary = f"{entity_id} 执行严重变慢 ({current_duration}ms, {deviation}x median)"
        elif status == "degraded":
            summary = f"{entity_id} 性能退化 (连续 {consecutive} 次慢执行)"
        else:  # warn
            summary = f"{entity_id} 执行变慢 ({current_duration}ms, {deviation}x median)"
        
        # 生成建议动作
        if status == "critical":
            suggested_action = "create_repair_task"
        elif status == "degraded":
            suggested_action = "set_observation_or_quarantine"
        else:  # warn
            suggested_action = "health_probe"
        
        event = {
            "event_id": f"evt-exec-latency-{entity_id}-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "source": "exec_latency_detector",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_type": "exec_latency_anomaly",
            "severity": severity,
            "status": "detected",
            "summary": summary,
            "evidence": {
                "latency_status": status,
                "current_duration_ms": current_duration,
                "median_ms": median,
                "p95_ms": check_result["p95_ms"],
                "deviation_ratio": deviation,
                "consecutive_slow_count": consecutive,
                "baseline_samples": check_result["baseline_samples"],
                "reason": reason
            },
            "suggested_action": suggested_action,
            "cooldown_key": f"{entity_type}:{entity_id}:exec_latency",
            "requires_verification": True,
            "trace_id": f"trace-exec-latency-{entity_id}-{int(time.time())}"
        }
        
        return event
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取检测器摘要
        
        Returns:
            {
                "total_entities": int,
                "entities_with_baseline": int,
                "entities_degraded": int,
                "avg_baseline_samples": float
            }
        """
        total_entities = len(self.baselines)
        entities_with_baseline = sum(
            1 for baseline in self.baselines.values()
            if len(baseline) >= self.min_samples
        )
        entities_degraded = sum(
            1 for count in self.consecutive_slow.values()
            if count >= self.consecutive_slow_threshold
        )
        avg_baseline_samples = (
            sum(len(b) for b in self.baselines.values()) / total_entities
            if total_entities > 0 else 0
        )
        
        return {
            "total_entities": total_entities,
            "entities_with_baseline": entities_with_baseline,
            "entities_degraded": entities_degraded,
            "avg_baseline_samples": round(avg_baseline_samples, 1)
        }


def main():
    """测试执行时延异常检测"""
    from pathlib import Path
    
    print("执行时延异常检测器 v0")
    print("=" * 60)
    
    # 初始化检测器
    detector = ExecLatencyDetector()
    
    # 加载基线
    records_path = Path(__file__).parent.parent / "data" / "agent_execution_record.jsonl"
    print(f"\n加载基线: {records_path}")
    detector.load_baselines(records_path)
    
    # 显示摘要
    summary = detector.get_summary()
    print(f"\n检测器摘要:")
    print(f"  总实体数: {summary['total_entities']}")
    print(f"  有基线的实体: {summary['entities_with_baseline']}")
    print(f"  退化的实体: {summary['entities_degraded']}")
    print(f"  平均基线样本数: {summary['avg_baseline_samples']}")
    
    # 测试：正常执行
    print(f"\n测试 1: 正常执行")
    result = detector.check("GitHub_Researcher", 1.5)
    print(f"  状态: {result['status']}")
    print(f"  严重级别: {result['severity']}")
    print(f"  当前耗时: {result['current_duration_ms']}ms")
    print(f"  中位数: {result['median_ms']}ms")
    print(f"  偏离比例: {result['deviation_ratio']}x")
    print(f"  原因: {result['reason']}")
    
    # 测试：单次慢执行
    print(f"\n测试 2: 单次慢执行（warn）")
    result = detector.check("GitHub_Researcher", 5.0)
    print(f"  状态: {result['status']}")
    print(f"  严重级别: {result['severity']}")
    print(f"  当前耗时: {result['current_duration_ms']}ms")
    print(f"  中位数: {result['median_ms']}ms")
    print(f"  偏离比例: {result['deviation_ratio']}x")
    print(f"  连续慢执行: {result['consecutive_slow_count']}")
    print(f"  原因: {result['reason']}")
    
    if result['status'] != 'normal':
        event = detector.generate_event("GitHub_Researcher", "agent", result)
        if event:
            print(f"\n  生成事件:")
            print(f"    摘要: {event['summary']}")
            print(f"    建议动作: {event['suggested_action']}")
    
    # 测试：连续慢执行
    print(f"\n测试 3: 连续慢执行（degraded）")
    for i in range(3):
        result = detector.check("GitHub_Researcher", 5.0)
        print(f"  第 {i+1} 次: 状态={result['status']}, 连续={result['consecutive_slow_count']}")
    
    if result['status'] == 'degraded':
        event = detector.generate_event("GitHub_Researcher", "agent", result)
        if event:
            print(f"\n  生成事件:")
            print(f"    摘要: {event['summary']}")
            print(f"    建议动作: {event['suggested_action']}")
    
    # 测试：严重慢执行
    print(f"\n测试 4: 严重慢执行（critical）")
    result = detector.check("GitHub_Researcher", 10.0)
    print(f"  状态: {result['status']}")
    print(f"  严重级别: {result['severity']}")
    print(f"  当前耗时: {result['current_duration_ms']}ms")
    print(f"  中位数: {result['median_ms']}ms")
    print(f"  偏离比例: {result['deviation_ratio']}x")
    print(f"  原因: {result['reason']}")
    
    if result['status'] == 'critical':
        event = detector.generate_event("GitHub_Researcher", "agent", result)
        if event:
            print(f"\n  生成事件:")
            print(f"    摘要: {event['summary']}")
            print(f"    建议动作: {event['suggested_action']}")


if __name__ == "__main__":
    main()
