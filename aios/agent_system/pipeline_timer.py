"""
Pipeline Timing - 耗时基线采集

在 submit → route → spawn → execute 四个节点埋 time.monotonic() 差值，
写入 pipeline_timings.jsonl。
"""

import json
import time
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

TIMINGS_FILE = Path(__file__).parent / "pipeline_timings.jsonl"


class PipelineTimer:
    """
    任务流水线耗时记录器。
    
    Usage:
        timer = PipelineTimer(task_id="task-001")
        timer.mark("submit")
        # ... do routing ...
        timer.mark("route")
        # ... do spawn ...
        timer.mark("spawn")
        # ... do execute ...
        timer.mark("execute")
        timer.flush()  # 写入 JSONL
    """
    
    STAGES = ["submit", "route", "spawn", "execute"]
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self._marks: dict[str, float] = {}
        self._start = time.monotonic()
    
    def mark(self, stage: str):
        """记录阶段时间戳"""
        self._marks[stage] = time.monotonic()
    
    def durations(self) -> dict[str, Optional[float]]:
        """
        计算各阶段耗时（ms）。
        
        Returns:
            {
                "submit_ms": float,      # 从开始到 submit
                "route_ms": float,       # submit → route
                "spawn_ms": float,       # route → spawn
                "execute_ms": float,     # spawn → execute
                "total_ms": float,       # 全程
            }
        """
        result = {}
        prev_time = self._start
        prev_stage = "start"
        
        for stage in self.STAGES:
            t = self._marks.get(stage)
            if t is not None:
                result[f"{stage}_ms"] = round((t - prev_time) * 1000, 2)
                prev_time = t
                prev_stage = stage
            else:
                result[f"{stage}_ms"] = None
        
        # 总耗时（到最后一个有效 mark）
        if self._marks:
            last_t = max(self._marks.values())
            result["total_ms"] = round((last_t - self._start) * 1000, 2)
        else:
            result["total_ms"] = None
        
        return result
    
    def flush(self, extra: Optional[dict] = None) -> dict:
        """
        将耗时记录写入 pipeline_timings.jsonl。
        
        Args:
            extra: 额外字段（如 task_type, success 等）
        
        Returns:
            写入的记录
        """
        record = {
            "task_id": self.task_id,
            "timestamp": time.time(),
            "duration_ms": self.durations(),
        }
        if extra:
            record.update(extra)
        
        with open(TIMINGS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        return record


@contextmanager
def timed_stage(timer: PipelineTimer, stage: str):
    """
    Context manager：自动在进入/退出时打 mark。
    
    Usage:
        with timed_stage(timer, "route"):
            result = router.route(task)
    """
    try:
        yield
    finally:
        timer.mark(stage)


def record_fallback_latency(task_id: str, duration_ms: float):
    """
    记录 fallback 全流程耗时（从检测超时到新 executor 接管）。
    
    Args:
        task_id: 任务 ID
        duration_ms: 耗时（毫秒）
    """
    record = {
        "task_id": task_id,
        "timestamp": time.time(),
        "fallback_latency_ms": round(duration_ms, 2),
    }
    with open(TIMINGS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_dlq_enqueue_latency(task_id: str, duration_ms: float):
    """
    记录 DLQ enqueue 耗时（从决定入队到写入 dead_letters.jsonl）。
    
    Args:
        task_id: 任务 ID
        duration_ms: 耗时（毫秒）
    """
    record = {
        "task_id": task_id,
        "timestamp": time.time(),
        "dlq_enqueue_latency_ms": round(duration_ms, 2),
    }
    with open(TIMINGS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_timing_stats(limit: int = 100) -> dict:
    """
    读取最近 N 条耗时记录，计算统计摘要。
    
    Returns:
        {
            "count": int,
            "avg_total_ms": float,
            "p50_total_ms": float,
            "p95_total_ms": float,
            "stage_avgs": {...}
        }
    """
    if not TIMINGS_FILE.exists():
        return {"count": 0}
    
    records = []
    with open(TIMINGS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    
    records = records[-limit:]
    if not records:
        return {"count": 0}
    
    totals = [r["duration_ms"].get("total_ms") for r in records if r.get("duration_ms", {}).get("total_ms")]
    
    if not totals:
        return {"count": len(records)}
    
    totals_sorted = sorted(totals)
    n = len(totals_sorted)
    
    stage_avgs = {}
    for stage in PipelineTimer.STAGES:
        key = f"{stage}_ms"
        vals = [r["duration_ms"].get(key) for r in records if r.get("duration_ms", {}).get(key)]
        if vals:
            stage_avgs[key] = round(sum(vals) / len(vals), 2)
    
    return {
        "count": len(records),
        "avg_total_ms": round(sum(totals) / n, 2),
        "p50_total_ms": totals_sorted[n // 2],
        "p95_total_ms": totals_sorted[int(n * 0.95)],
        "stage_avgs": stage_avgs,
    }


if __name__ == "__main__":
    print("=== Pipeline Timer Demo ===\n")
    
    # 模拟一个完整的任务流水线
    timer = PipelineTimer(task_id="demo-001")
    
    # submit 阶段
    time.sleep(0.01)
    timer.mark("submit")
    
    # route 阶段
    time.sleep(0.02)
    timer.mark("route")
    
    # spawn 阶段
    time.sleep(0.05)
    timer.mark("spawn")
    
    # execute 阶段
    time.sleep(0.1)
    timer.mark("execute")
    
    record = timer.flush(extra={"task_type": "code", "success": True})
    
    print("Recorded timing:")
    for k, v in record["duration_ms"].items():
        print(f"  {k}: {v} ms")
    
    print(f"\nFlushed to: {TIMINGS_FILE}")
    
    # 统计
    stats = get_timing_stats()
    print(f"\nStats: {stats}")
