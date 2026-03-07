# -*- coding: utf-8 -*-
"""
tracer.py - AIOS Tracing MVP

统一事件流追踪：任务创建 → 入队 → spawn → 执行 → 写回结果

设计原则：
1. trace 写失败不阻塞主流程（静默降级）
2. 同一任务全程共享 trace_id（不断链）
3. 单文件 data/task_traces.jsonl，单接口 trace_event()

字段（12个）：
- trace_id: 追踪链 ID（同一任务全程不变）
- task_id: 任务 ID
- workflow_id: 工作流 ID（可选，用于关联多任务流）
- parent_task_id: 父任务 ID（子任务场景）
- source: 事件来源模块
- agent_name: 执行 Agent
- step_name: 步骤名称（7个固定值）
- status: success | failed | skipped
- created_at: ISO 8601 时间戳
- duration_ms: 耗时（毫秒）
- result_summary: 结果摘要（≤200字符）
- error_type: 错误类型（仅 failed 时）

step_name 固定值：
- task_created
- task_enqueued
- spawn_requested
- spawn_consumed
- execution_started
- execution_finished
- execution_failed
"""

import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

# 路径：优先从 paths.py 导入，fallback 到本地
try:
    from paths import TASK_TRACES
except ImportError:
    TASK_TRACES = Path(__file__).parent / "data" / "task_traces.jsonl"

# 合法 step_name
VALID_STEPS = frozenset({
    "task_created",
    "task_enqueued",
    "spawn_requested",
    "spawn_consumed",
    "execution_started",
    "execution_finished",
    "execution_failed",
})


def new_trace_id() -> str:
    """生成新的 trace_id"""
    return f"trace-{uuid.uuid4().hex[:12]}"


def trace_event(
    trace_id: str,
    task_id: str,
    step_name: str,
    status: str = "success",
    source: str = "",
    agent_name: str = "",
    workflow_id: str = None,
    parent_task_id: str = None,
    duration_ms: int = 0,
    result_summary: str = "",
    error_type: str = None,
) -> dict | None:
    """
    写入一条 trace event 到 task_traces.jsonl
    
    写失败时静默降级，返回 None。
    成功时返回写入的 event dict。
    """
    # 校验 step_name
    if step_name not in VALID_STEPS:
        # 不阻塞，但打个警告
        try:
            print(f"  [TRACE:WARN] unknown step_name: {step_name}", flush=True)
        except Exception:
            pass

    event = {
        "trace_id": trace_id,
        "task_id": task_id,
        "workflow_id": workflow_id,
        "parent_task_id": parent_task_id,
        "source": source,
        "agent_name": agent_name,
        "step_name": step_name,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "result_summary": (result_summary or "")[:200],
    }

    # 条件字段：error_type 只在 failed 时出现
    if status == "failed" and error_type:
        event["error_type"] = error_type

    # workflow_id / parent_task_id 为 None 时不写入（保持行短）
    if workflow_id is None:
        del event["workflow_id"]
    if parent_task_id is None:
        del event["parent_task_id"]

    try:
        TASK_TRACES.parent.mkdir(parents=True, exist_ok=True)
        with open(TASK_TRACES, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event
    except Exception as e:
        # 原则 1：写失败不阻塞主流程
        try:
            print(f"  [TRACE:ERR] write failed: {e}", flush=True)
        except Exception:
            pass
        return None


class TaskTracer:
    """
    便捷封装：为单个任务维护 trace_id，简化多步骤追踪。
    
    用法：
        t = TaskTracer(task_id="task-xxx", source="auto_dispatcher", agent_name="coder")
        t.created("task submitted by user")
        t.enqueued()
        t.spawn_requested()
        t.spawn_consumed()
        t.started()
        t.finished(duration_ms=3200, result_summary="code generated")
        # 或
        t.failed(duration_ms=5000, error_type="timeout", result_summary="model timeout")
    """

    def __init__(
        self,
        task_id: str,
        source: str = "",
        agent_name: str = "",
        trace_id: str = None,
        workflow_id: str = None,
        parent_task_id: str = None,
    ):
        self.task_id = task_id
        self.source = source
        self.agent_name = agent_name
        self.trace_id = trace_id or new_trace_id()
        self.workflow_id = workflow_id
        self.parent_task_id = parent_task_id
        self._start_time = None

    def _emit(self, step_name: str, status: str = "success",
              duration_ms: int = 0, result_summary: str = "",
              error_type: str = None, source: str = None) -> dict | None:
        return trace_event(
            trace_id=self.trace_id,
            task_id=self.task_id,
            step_name=step_name,
            status=status,
            source=source or self.source,
            agent_name=self.agent_name,
            workflow_id=self.workflow_id,
            parent_task_id=self.parent_task_id,
            duration_ms=duration_ms,
            result_summary=result_summary,
            error_type=error_type,
        )

    def created(self, result_summary: str = "") -> dict | None:
        return self._emit("task_created", result_summary=result_summary)

    def enqueued(self, result_summary: str = "task queued") -> dict | None:
        return self._emit("task_enqueued", result_summary=result_summary)

    def spawn_requested(self, result_summary: str = "") -> dict | None:
        return self._emit("spawn_requested", result_summary=result_summary)

    def spawn_consumed(self, result_summary: str = "") -> dict | None:
        return self._emit("spawn_consumed", source="heartbeat", result_summary=result_summary)

    def started(self) -> dict | None:
        self._start_time = time.time()
        return self._emit("execution_started")

    def finished(self, duration_ms: int = 0, result_summary: str = "") -> dict | None:
        if duration_ms == 0 and self._start_time:
            duration_ms = round((time.time() - self._start_time) * 1000)
        return self._emit("execution_finished", duration_ms=duration_ms,
                          result_summary=result_summary)

    def failed(self, duration_ms: int = 0, error_type: str = "unknown",
               result_summary: str = "") -> dict | None:
        if duration_ms == 0 and self._start_time:
            duration_ms = round((time.time() - self._start_time) * 1000)
        return self._emit("execution_failed", status="failed",
                          duration_ms=duration_ms, error_type=error_type,
                          result_summary=result_summary)
