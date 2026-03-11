---
name: heartbeat-alert-deduper
version: 1.0.0
description: Heartbeat 告警去重 - 识别并过滤已发送的重复告警，避免用户被同一问题反复打扰
author: AIOS Auto-Generation
created: 2026-03-11
risk_level: low
platforms: [windows, linux, macos]
---

# heartbeat-alert-deduper

## Description

Heartbeat 告警去重 - 识别并过滤已发送的重复告警，避免用户被同一问题反复打扰

## When to Use

- heartbeat 执行时
- 检测到 alerts.jsonl 有未发送告警
- 需要判断是否为重复告警

## Trigger Conditions

**Activation Signals:**
- Heartbeat 执行时检测到未发送告警
- alerts.jsonl 文件存在且非空

**Negative Conditions:**
- alerts.jsonl 不存在
- 所有告警已标记为已发送

**Priority:** 80/100

**Required Context:**
- alerts.jsonl 路径
- alert_history.jsonl 路径

## Expected Behavior

读取历史告警记录，对比当前告警的 skill_name/version/level/error_type，如果完全匹配则判定为重复，仅在状态变化时重新通知

## Implementation

```python
# 核心逻辑（示例）
def dedupe_alerts(alerts_file, history_file):
    # 读取当前告警
    current_alerts = read_alerts(alerts_file)
    
    # 读取历史记录
    history = read_history(history_file)
    
    # 去重逻辑
    new_alerts = []
    for alert in current_alerts:
        if not is_duplicate(alert, history):
            new_alerts.append(alert)
    
    return new_alerts
```

## Dependencies

- alerts.jsonl
- alert_history.jsonl

## Risk Assessment

**Risk Level:** low

**Rationale:** 只读操作，不修改系统状态，仅过滤告警列表

## Verification

**Success Criteria:**
- 重复告警被正确识别
- 新告警正常通过
- 历史记录正确更新

**Test Cases:**
1. 相同告警连续出现 → 只发送一次
2. 告警状态变化（WARN → CRIT）→ 重新发送
3. 不同告警 → 全部发送

## Notes

- 基于真实需求自动生成
- 已通过 shadow 模式验证
- 用户确认需求（2026-03-08）

## Evidence

- memory/2026-03-08.md
- HEARTBEAT.md
- heartbeat_v5.py
