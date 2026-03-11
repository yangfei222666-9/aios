# P2.5-1 验收文档：Heartbeat 接入 DecideAndDispatch

## 目标

让 heartbeat 成为中枢的第一个真实入口。

## 交付物

| 交付物 | 路径 | 状态 |
|--------|------|------|
| 转换层 | `heartbeat_dispatcher_bridge.py` | ✅ |
| heartbeat 接入 | `heartbeat_v5.py` 中 6 个收集点 + 统一派发 | ✅ |
| dispatch_log | `data/dispatch_log.jsonl` | ✅ 已验证写入 |
| 验收文档 | 本文件 | ✅ |

## 架构

```
heartbeat_v5.py
  ├── Token 告警 ──────────┐
  ├── 僵尸任务回收 ────────┤
  ├── 演化分数过期 ────────┤  collect
  ├── 健康检查异常 ────────┤
  └── 技能连续失败 ────────┘
                           ↓
              HeartbeatDispatcherBridge
                           ↓
                   dispatch_all()
                           ↓
              DecideAndDispatch.process_and_log()
                           ↓
              ┌─── SkillRouter.route() ───┐
              │                           │
              │   PolicyDecision.decide() │
              │                           │
              └─── dispatch + writeback ──┘
                           ↓
                  dispatch_log.jsonl
```

## 事件类型

| 事件 | 触发条件 | 优先级 | 风险 |
|------|----------|--------|------|
| health_check | 健康度 < 80 | normal~critical | low~high |
| zombie_reclaimed | 有僵尸回收 | normal~high | low~medium |
| skill_failure | 有连续失败告警 | high~critical | medium~high |
| evolution_stale | 数据过期且重算失败 | normal | low |
| token_alert | Token 用量告警 | high~critical | medium |

## 验收标准

1. ✅ heartbeat 事件能被标准化成 task_context
2. ✅ 能进入 router → policy → dispatch 主链
3. ✅ 派发结果写入 dispatch_log.jsonl
4. ✅ 不污染现有生产链路（只在现有检查后追加收集，最后统一派发）
5. ✅ 失败时留下 fallback 记录（降级路径有 fallback_action）

## 设计决策

- 正常状态不产生事件（健康度 >= 80、无僵尸、无告警 → 不进中枢），避免噪音
- 收集-派发分离：先收集所有事件，最后统一派发，保证 heartbeat 主流程不被中枢阻塞
- 第一版模拟执行（DispatchMode.SIMULATED），不真正调用 handler，只记录决策

## 下一步

P2.5-2：dispatch_log → health-monitor（让 health-monitor 消费中枢决策日志）
