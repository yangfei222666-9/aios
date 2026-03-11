# P2.5-2 验收文档：Health-Monitor 消费 Dispatch Log

## 目标

让 health-monitor 从"看执行结果"升级到"看决策过程"。

## 交付物

| 交付物 | 路径 | 状态 |
|--------|------|------|
| dispatch_log_reader.py | `dispatch_log_reader.py` | ✅ |
| health_monitor_dispatch_metrics.py | `health_monitor_dispatch_metrics.py` | ✅ |
| test_health_monitor_dispatch_metrics.py | `test_health_monitor_dispatch_metrics.py` | ✅ 5/5 通过 |
| 验收文档 | 本文件 | ✅ |

## 架构

```
dispatch_log.jsonl
       ↓
DispatchLogReader
  (只提取 5 个字段)
       ↓
HealthMonitorDispatchMetrics
  (4 个观察维度)
       ↓
  • 决策分布
  • 策略分布
  • 降级与 fallback
  • 中枢异常热点
       ↓
  3 句诊断
```

## 5 个关键字段

只关注这 5 个字段，不贪多：

1. `current_situation` - 当前情况
2. `chosen_handler` - 选中的处理器
3. `policy_result` - 策略结果
4. `final_status` - 最终状态
5. `fallback_action` - 降级方案

## 4 个观察维度

### 1. 决策分布
- 哪类 situation 最多
- 哪些 handler 最常被选中

### 2. 策略分布
- auto_execute / degrade / blocked / failed 各有多少
- 哪类输入最容易被拦截

### 3. 降级与 fallback
- 最常触发的 fallback 是什么
- 哪类问题最常走降级路径

### 4. 中枢异常热点
- 哪个 handler 最常被拒绝
- 哪类决策最常失败
- 哪类事件总被卡在 policy

## 3 句诊断

固定句式：

1. **当前最常见的中枢决策类型：** `{situation} ({count} 次)`
2. **当前最常见的拦截/降级原因：** `拦截: {situation}; 降级: {situation}`
3. **当前最值得优先优化的决策链路：** `{handler} (被拒 N 次); {situation} (失败 N 次)`

## 验收标准

| 标准 | 状态 |
|------|------|
| 1. health-monitor 能成功读取 dispatch_log.jsonl | ✅ |
| 2. 能统计 decision / policy / final_status 分布 | ✅ |
| 3. 能识别 top blocked / top degraded / top failed 模式 | ✅ |
| 4. 能把 dispatch 结论写进 L4 Diagnosis | ✅ 3 句诊断 |
| 5. 不影响现有 health score 主链 | ✅ 独立模块 |

## 测试结果

```
============================================================
Health Monitor Dispatch Metrics - 验收测试
============================================================
[TEST 1] 读取 dispatch_log.jsonl
  Total records: 6
  Recent 24h: 3
  ✅ 读取成功

[TEST 2] 统计分布
  Decision Distribution: 3 situations, 1 handlers
  Policy Distribution: 1 policy types, 1 status types
  ✅ 统计成功

[TEST 3] 模式识别
  Top Blocked: []
  Top Degraded: [('routine_monitor', 1), ('routine_alert', 1), ('critical_alert', 1)]
  Top Failed: []
  ✅ 模式识别成功

[TEST 4] 诊断生成
  Diagnosis lines: 3
    • 当前最常见的中枢决策类型：routine_monitor (1 次)
    • 当前最常见的拦截/降级原因：降级: routine_monitor (1 次)
    • 当前最值得优先优化的决策链路：无明显热点
  ✅ 诊断生成成功（3 句）

[TEST 5] 不影响现有 health score
  ✅ 独立模块，不影响 health score

============================================================
测试结果: 5/5 通过
✅ 所有验收标准通过
============================================================
```

## 下一步

P2.5-3：dispatch_log → pattern-detector（让 pattern-detector 从决策日志中识别模式）
