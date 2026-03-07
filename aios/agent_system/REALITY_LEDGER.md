# REALITY_LEDGER.md - 动作生命周期与状态机规范 v0.2

**版本：** v0.2  
**更新：** 2026-03-07 12:10  
**维护者：** 小九 + 珊瑚海

---

## 核心理念

Reality Ledger = 真实世界动作账本。

- ActionRecord 是当前快照
- LedgerEvent 是 append-only 审计事件流
- status 管生命周期
- outcome 管执行结果
- `released` 是生命周期终态，**不是 outcome**

---

## 1. Status / Outcome 定义

### Status（8 个）

- `proposed`
- `locked`
- `executing`
- `completed`
- `failed`
- `released`
- `skipped`
- `rejected`

### Outcome（5 个）

- `unknown`
- `completed`
- `failed`
- `skipped`
- `rejected`

---

## 2. 推荐合法主链

```
proposed -> locked
locked -> executing
executing -> completed -> released
executing -> failed -> released
proposed -> skipped
proposed -> rejected
```

## 3. 谨慎保留

```
locked -> released
```

仅用于：
- 锁超时回收
- 人工取消
- 系统 cleanup

并且必须带：

```json
{
  "release_reason": "lock_timeout | manual_cancel | cleanup"
}
```

此时：
- `status = released`
- `outcome = unknown`

## 4. 不默认支持

```
executing -> released
```

v0 禁止该迁移。
如果执行中取消/超时，应先判定失败：

```
executing -> failed -> released
```

---

## 5. Released 的 outcome 继承规则

### 1) completed -> released
- `status = released`
- `outcome = completed`
- `release_reason = execution_done`

### 2) failed -> released
- `status = released`
- `outcome = failed`
- `release_reason = execution_done`

### 3) locked -> released
- `status = released`
- `outcome = unknown`
- `release_reason = lock_timeout | manual_cancel | cleanup`

---

## 6. 指标建议

### 第一层：事件计数

- `actions_proposed_total`
- `actions_locked_total`
- `actions_executing_total`
- `actions_completed_total`
- `actions_failed_total`
- `actions_released_total`
- `actions_skipped_total`
- `actions_rejected_total`

建议同时按以下维度聚合：
- `action_type`
- `resource_type`

### 第二层：结果指标

- `action_success_rate`
- `action_failure_rate`
- `action_skip_rate`
- `action_reject_rate`
- `execution_success_rate = completed / (completed + failed)`
- `proposal_acceptance_rate = accepted / proposed`

### 第三层：时延指标

- `action_duration_ms`：proposed → completed/failed
- `lock_hold_duration_ms`：locked → released
- `queue_wait_duration_ms`：proposed → locked

---

## 7. 最推荐落地顺序

### Step 1
先做离线脚本：`ledger_metrics.py`

从 `action_ledger.jsonl` / `actions_state.jsonl` 统计：
- 最近 24h 各状态计数
- outcome 分布
- avg / p95 action_duration_ms
- avg / p95 lock_hold_duration_ms
- avg / p95 queue_wait_duration_ms

### Step 2
再接：
- heartbeat summary
- dashboard
- daily report

---

## 8. 结论

> 先修正 outcome 定义，把 `released` 从 outcome 里移出去。  
> 然后开始做 Ledger 指标化，先做离线统计脚本，不急着在线埋点。

对应文件建议：
- `ledger_metrics.py`
- `ledger_metrics_report.py`
