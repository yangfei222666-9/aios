import json
from datetime import datetime, timezone

file = r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\task_executions.jsonl"

start = datetime(2026, 3, 7, tzinfo=timezone.utc)
end   = datetime(2026, 3, 15, tzinfo=timezone.utc)

all_records = []
window = []
parse_errors = 0

with open(file, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            all_records.append(rec)
            ts_str = rec.get("start_time") or rec.get("timestamp") or rec.get("created_at")
            if ts_str and isinstance(ts_str, str):
                ts_str_clean = ts_str.replace("+00:00", "").replace("Z", "")
                try:
                    ts = datetime.fromisoformat(ts_str_clean).replace(tzinfo=timezone.utc)
                    if start <= ts < end:
                        window.append(rec)
                except:
                    pass
        except json.JSONDecodeError:
            parse_errors += 1

print(f"总记录数: {len(all_records)}")
print(f"解析错误: {parse_errors}")
print(f"观察期记录 (3/7~3/14): {len(window)}")

if all_records:
    times = []
    for r in all_records:
        ts_str = r.get("start_time") or r.get("timestamp") or ""
        if ts_str and isinstance(ts_str, str):
            times.append(ts_str[:10])
    times.sort()
    if times:
        print(f"数据时间范围: {times[0]} ~ {times[-1]}")

if len(window) == 0:
    print("\n--- 所有记录时间分布 ---")
    date_counts = {}
    for r in all_records:
        ts_str = r.get("start_time") or r.get("timestamp") or "unknown"
        if isinstance(ts_str, str):
            d = ts_str[:10]
        else:
            d = "invalid"
        date_counts[d] = date_counts.get(d, 0) + 1
    for d in sorted(date_counts):
        print(f"  {d}: {date_counts[d]} 条")

# 分析观察期数据
if len(window) > 0:
    print("\n=== 1) side_effects 漏填率 ===")
    total = len(window)
    empty = 0
    for r in window:
        se = r.get("side_effects")
        if se is None or se == "" or se == "[]" or (isinstance(se, list) and len(se) == 0):
            empty += 1
    miss_rate = round(empty / total * 100, 1) if total > 0 else 0
    fill_rate = round((1 - empty / total) * 100, 1) if total > 0 else 0
    print(f"总记录: {total}")
    print(f"空值数: {empty}")
    print(f"漏填率: {miss_rate}%")
    print(f"填写率: {fill_rate}%")

    print("\n=== 2) duration_ms 分布 ===")
    durations = []
    for r in window:
        d = r.get("duration_ms")
        if d is not None:
            durations.append(float(d))
    durations.sort()
    dcount = len(durations)
    print(f"有效记录: {dcount}")
    if dcount > 0:
        p50 = durations[int(dcount * 0.50)]
        p90 = durations[int(dcount * 0.90)]
        p99 = durations[int(dcount * 0.99)]
        maxd = durations[-1]
        mean = round(sum(durations) / dcount, 0)
        print(f"P50:  {p50} ms")
        print(f"P90:  {p90} ms")
        print(f"P99:  {p99} ms")
        print(f"Max:  {maxd} ms")
        print(f"Mean: {mean} ms")

    print("\n=== 3) 长尾任务 (>60s) ===")
    long_tail = []
    for r in window:
        d = r.get("duration_ms")
        if d is not None and float(d) > 60000:
            long_tail.append(r)
    long_tail.sort(key=lambda x: float(x.get("duration_ms", 0)), reverse=True)
    print(f"共 {len(long_tail)} 条")
    for r in long_tail[:20]:
        name = r.get("task_name") or r.get("skill") or r.get("agent_id") or "unknown"
        dur = round(float(r.get("duration_ms", 0)) / 1000, 1)
        ts = r.get("start_time") or r.get("timestamp") or "?"
        print(f"  {dur}s | {name} | {ts}")
