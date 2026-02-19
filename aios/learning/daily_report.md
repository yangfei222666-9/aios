# AIOS Daily Report
Generated: 2026-02-19T10:25:13Z
Window: 2026-02-18T10:25:13Z → 2026-02-19T10:25:13Z

## A. Metrics
- events: 242  matches: 10  corrections: 2  tools: 183
- correction_rate: 16.67%
- tool_success_rate: 95.63%
- http_502: 1  http_404: 1
- p95/p50:
  - exec: p95=6640ms p50=4320ms
  - write: p95=129ms p50=81ms
  - edit: p95=81ms p50=55ms
  - read: p95=92ms p50=59ms
  - web_fetch: p95=3100ms p50=3100ms
  - image: p95=300ms p50=240ms
  - memory_search: p95=160ms p50=120ms
  - message: p95=120ms p50=120ms
  - cron: p95=400ms p50=400ms

## B. Top Issues
- corrected: "卡特" x1
- corrected: "亚恒" x1
- failed: exec x3
- failed: web_search x2
- failed: web_fetch x1
- failed: cron x1
- failed: nonexistent_tool x1

## C. Alias Suggestions (L1)

## D. Tool Suggestions (L2)
- exec: cooldown_10m conf=0.6 (repeat_fail>=3)
- web_search: monitor conf=0.4 (repeat_fail>=2)
- runtime_error: cooldown_10m conf=0.6 (repeat_fail>=3)
- exec: optimize_or_cache conf=0.66 (p95>6640ms)

## F. Evolution Score
- score: 0.3396  grade: ok
  - tool_success_rate: 0.9602 (w=0.4)
  - correction_rate: 0.1111 (w=-0.2)
  - http_502_rate: 0.0 (w=-0.2)
  - p95_slow_ratio: 0.111 (w=-0.2)

## G. Regression Gate ✓
- gate_passed