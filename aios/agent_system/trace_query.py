#!/usr/bin/env python3
"""
trace_query.py - Tracing 最小查询 + 汇总工具

用法：
  python trace_query.py                          # 汇总统计
  python trace_query.py --task task-xxx          # 按 task_id 查
  python trace_query.py --trace trace-xxx        # 按 trace_id 查
  python trace_query.py --failed                 # 查所有失败
  python trace_query.py --agent coder-dispatcher # 按 agent 查
  python trace_query.py --gaps                   # 检测断链（step 缺失）
"""

import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

try:
    from paths import TASK_TRACES
except ImportError:
    TASK_TRACES = Path(__file__).parent / "data" / "task_traces.jsonl"

# 完整链路的 step 顺序
FULL_CHAIN = [
    "task_created",
    "task_enqueued",
    "spawn_requested",
    "spawn_consumed",
    "execution_started",
    "execution_finished",  # 或 execution_failed
]


def load_events() -> list:
    if not TASK_TRACES.exists():
        return []
    events = []
    with open(TASK_TRACES, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def query_by_field(events: list, field: str, value: str) -> list:
    return [e for e in events if e.get(field) == value]


def print_events(events: list):
    for e in events:
        err = f" error_type={e['error_type']}" if "error_type" in e else ""
        dur = f" {e['duration_ms']}ms" if e.get("duration_ms") else ""
        print(f"  [{e['step_name']}] {e['status']} | {e.get('agent_name', '?')}{dur}{err}")
        if e.get("result_summary"):
            print(f"    → {e['result_summary'][:120]}")


def print_chain(events: list, task_id: str):
    """打印单个任务的完整链路"""
    task_events = sorted(
        [e for e in events if e.get("task_id") == task_id],
        key=lambda e: e.get("created_at", ""),
    )
    if not task_events:
        print(f"  No events for {task_id}")
        return

    trace_id = task_events[0].get("trace_id", "?")
    print(f"\n  trace_id: {trace_id}")
    print(f"  task_id:  {task_id}")
    print(f"  events:   {len(task_events)}")
    print()
    print_events(task_events)

    # 检测缺失 step
    steps_seen = {e["step_name"] for e in task_events}
    terminal = steps_seen & {"execution_finished", "execution_failed"}
    expected = set(FULL_CHAIN[:-1])  # 去掉 execution_finished
    if terminal:
        expected.add(list(terminal)[0])
    missing = expected - steps_seen
    if missing:
        print(f"\n  ⚠ Missing steps: {', '.join(sorted(missing))}")
    else:
        print(f"\n  ✓ Chain complete")


def detect_gaps(events: list) -> dict:
    """检测所有任务的断链情况"""
    by_task = defaultdict(list)
    for e in events:
        by_task[e.get("task_id", "?")].append(e)

    gaps = {}
    for task_id, task_events in by_task.items():
        steps_seen = {e["step_name"] for e in task_events}
        has_terminal = bool(steps_seen & {"execution_finished", "execution_failed"})

        # 只检查有 task_created 的任务（排除中途接入的）
        if "task_created" not in steps_seen:
            continue

        expected = {"task_created", "task_enqueued", "spawn_requested",
                    "spawn_consumed", "execution_started"}
        if has_terminal:
            terminal = steps_seen & {"execution_finished", "execution_failed"}
            expected.add(list(terminal)[0])

        missing = expected - steps_seen
        if missing:
            gaps[task_id] = sorted(missing)

    return gaps


def summary(events: list):
    """汇总统计"""
    if not events:
        print("[INFO] task_traces.jsonl is empty — no events yet")
        print("[INFO] Waiting for real tasks to generate trace data")
        return

    by_task = defaultdict(list)
    for e in events:
        by_task[e.get("task_id", "?")].append(e)

    total_tasks = len(by_task)

    # 统计终态
    completed = 0
    failed = 0
    in_progress = 0
    for task_id, task_events in by_task.items():
        steps = {e["step_name"] for e in task_events}
        if "execution_finished" in steps:
            completed += 1
        elif "execution_failed" in steps:
            failed += 1
        else:
            in_progress += 1

    # 平均执行时长（只看有 duration_ms > 0 的 finished/failed）
    durations = []
    for e in events:
        if e["step_name"] in ("execution_finished", "execution_failed") and e.get("duration_ms", 0) > 0:
            durations.append(e["duration_ms"])

    avg_dur = round(sum(durations) / len(durations)) if durations else 0
    p50 = sorted(durations)[len(durations) // 2] if durations else 0
    p90 = sorted(durations)[int(len(durations) * 0.9)] if durations else 0
    max_dur = max(durations) if durations else 0

    # step 丢失率
    gaps = detect_gaps(events)
    gap_rate = round(len(gaps) / total_tasks * 100, 1) if total_tasks else 0

    # agent 失败分布
    agent_failures = Counter()
    for e in events:
        if e["step_name"] == "execution_failed":
            agent_failures[e.get("agent_name", "?")] += 1

    # error_type 分布
    error_types = Counter()
    for e in events:
        if e.get("error_type"):
            error_types[e["error_type"]] += 1

    print("=" * 50)
    print("  AIOS Trace Summary")
    print("=" * 50)
    print(f"  Total tasks:    {total_tasks}")
    print(f"  Completed:      {completed}")
    print(f"  Failed:         {failed}")
    print(f"  In progress:    {in_progress}")
    print(f"  Gap rate:       {gap_rate}% ({len(gaps)}/{total_tasks} tasks with missing steps)")
    print()
    print(f"  Duration (ms):  avg={avg_dur}  P50={p50}  P90={p90}  max={max_dur}")
    print()

    if agent_failures:
        print("  Agent failures:")
        for agent, count in agent_failures.most_common(10):
            print(f"    {agent}: {count}")
        print()

    if error_types:
        print("  Error types:")
        for etype, count in error_types.most_common(10):
            print(f"    {etype}: {count}")
        print()

    if gaps:
        print(f"  Broken chains ({len(gaps)}):")
        for task_id, missing in list(gaps.items())[:5]:
            print(f"    {task_id}: missing {', '.join(missing)}")
        if len(gaps) > 5:
            print(f"    ... and {len(gaps) - 5} more")

    print("=" * 50)


def main():
    events = load_events()

    if "--task" in sys.argv:
        idx = sys.argv.index("--task") + 1
        if idx < len(sys.argv):
            print_chain(events, sys.argv[idx])
        return

    if "--trace" in sys.argv:
        idx = sys.argv.index("--trace") + 1
        if idx < len(sys.argv):
            matched = query_by_field(events, "trace_id", sys.argv[idx])
            print(f"\nEvents for trace {sys.argv[idx]}: {len(matched)}")
            print_events(matched)
        return

    if "--failed" in sys.argv:
        failed = [e for e in events if e.get("status") == "failed"]
        print(f"\nFailed events: {len(failed)}")
        print_events(failed)
        return

    if "--agent" in sys.argv:
        idx = sys.argv.index("--agent") + 1
        if idx < len(sys.argv):
            matched = query_by_field(events, "agent_name", sys.argv[idx])
            print(f"\nEvents for agent {sys.argv[idx]}: {len(matched)}")
            print_events(matched)
        return

    if "--gaps" in sys.argv:
        gaps = detect_gaps(events)
        if not gaps:
            print("[OK] No broken chains detected")
        else:
            print(f"[WARN] {len(gaps)} tasks with broken chains:")
            for task_id, missing in gaps.items():
                print(f"  {task_id}: missing {', '.join(missing)}")
        return

    # 默认：汇总
    summary(events)


if __name__ == "__main__":
    main()
