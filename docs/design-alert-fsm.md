# 告警闭环状态机 - 技术设计

> 从"喊一声"升级到"发现→跟踪→解决→关闭"的完整闭环。

## 1. 状态流转

```
                 ┌──────────┐
    alerts.py ──▶│   open   │
    检测到问题    └────┬─────┘
                      │ ack（小九/珊瑚海确认）
                      ▼
                 ┌──────────┐
                 │   ack    │
                 └────┬─────┘
                      │ resolve（问题已修复）
                      ▼
                 ┌──────────┐
                 │ resolved │  ← 终态
                 └──────────┘

    超时分支（任何非终态）：
    open/ack ──SLA超时──▶ escalated（推送珊瑚海）
    escalated 仍可 → ack → resolved
```

合法流转：
- `open` → `ack` | `escalated` | `resolved`（允许跳过 ack 直接 resolve）
- `ack` → `resolved` | `escalated`
- `escalated` → `ack` → `resolved`

终态：`resolved`（不可再变更）

## 2. 数据结构

每个告警一条 JSON，状态变更时追加新行（同 ID 取最后一行为当前状态）。

```jsonc
// memory/alerts_state.jsonl - 每行一条
{
  "id": "ALT-20260219-001",       // 唯一ID: ALT-{YYYYMMDD}-{当日序号}
  "rule": "critical_files",        // 来源规则（对应 alerts.py 的 rule_id）
  "severity": "CRIT",              // INFO | WARN | CRIT
  "status": "open",                // open | ack | resolved | escalated
  "owner": "小九",                  // 默认小九，可转给珊瑚海
  "message": "关键文件缺失: events.jsonl",
  "sla_deadline": "2026-02-19T18:27:56",  // 创建时间 + SLA
  "created_at": "2026-02-19T17:27:56",
  "updated_at": "2026-02-19T17:27:56",
  "history": ["open"]              // 状态变更轨迹
}
```

SLA 时限：
| severity | SLA | 含义 |
|----------|-----|------|
| CRIT | 1h | 必须 1 小时内 resolved |
| WARN | 24h | 一天内处理 |
| INFO | 72h | 三天内关注 |

## 3. 与现有系统的集成点

### 3.1 alerts.py（告警产生）

当前 `log_event()` 只写日志。改造点：

- WARN/CRIT 级别事件 → 同时调用 `fsm.open_alert(rule, severity, message)`
- INFO 级别 → 仅落盘，不创建状态告警（保持现有行为）
- 去重：同一 rule 已有 open/ack 状态的告警 → 不重复创建，仅更新 `updated_at`

### 3.2 心跳巡检（HEARTBEAT.md）

心跳时增加一步：
1. 读取 `alerts_state.jsonl`，筛选 status ∈ {open, ack, escalated}
2. 检查 `sla_deadline` 是否已过
3. 超时的 → 自动执行 `escalate`，推送珊瑚海
4. 在心跳摘要中报告 open 告警数量

### 3.3 对话命令接口

```bash
python -m alerts list              # 列出所有 open/ack/escalated 告警
python -m alerts list --all        # 含 resolved
python -m alerts ack ALT-xxx       # 确认告警，可选 --owner 珊瑚海
python -m alerts resolve ALT-xxx   # 标记已解决
python -m alerts escalate ALT-xxx  # 手动升级
```

小九在对话中可直接调用这些命令来管理告警。

### 3.4 alerts_log.jsonl（保持不变）

原有日志继续写入，作为事件流水。`alerts_state.jsonl` 是状态层，两者独立。

## 4. 核心逻辑（伪代码级）

### ID 生成
`ALT-{YYYYMMDD}-{当日序号}`，序号从 jsonl 中当日已有 ID 推算。

### 去重策略
`open_alert()` 前先查：同 rule + status ∈ {open, ack} → 跳过创建，更新 updated_at。

### SLA 检查
```
for alert in active_alerts:
    if now > alert.sla_deadline and alert.status != 'escalated':
        escalate(alert)
        notify_coralSea(alert)
```

### 状态写入
追加模式写 jsonl。读取时按 id 分组，取每个 id 最后一行。

## 5. 实现步骤

### Phase 1：状态机核心（~80 行）
- 新建 `scripts/alert_fsm.py`
- 实现：`open_alert()`, `ack_alert()`, `resolve_alert()`, `escalate_alert()`
- 实现：`list_alerts()`, `check_sla()`
- 存储读写：追加 jsonl + 按 id 聚合

### Phase 2：集成 alerts.py（~20 行改动）
- `run_checks()` 中 WARN/CRIT 事件调用 `fsm.open_alert()`
- 加入去重逻辑

### Phase 3：命令行接口（~30 行）
- `alert_fsm.py` 的 `__main__` 块
- 支持 `list / ack / resolve / escalate` 子命令
- 也可挂到 `python -m alerts` 下作为子命令

### Phase 4：心跳集成（~10 行）
- HEARTBEAT.md 加入 SLA 检查指令
- 小九心跳时调用 `check_sla()`，超时自动 escalate + 推送

## 6. 文件清单

| 文件 | 变更 |
|------|------|
| `scripts/alert_fsm.py` | 新建，状态机核心 + CLI，≤150 行 |
| `scripts/alerts.py` | 改造，集成 fsm，~20 行改动 |
| `memory/alerts_state.jsonl` | 新建，运行时自动生成 |
| `HEARTBEAT.md` | 追加 SLA 检查步骤 |

总新增代码量预估：~150 行，不超过 200 行上限。
