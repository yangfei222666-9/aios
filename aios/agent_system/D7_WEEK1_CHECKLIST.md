# Week 1 测试矩阵 + DoD 清单

**状态：** Day 3 Go ✅ → Week 1 开始  
**时间：** 2026-03-06 19:15+  
**目标：** 故障可恢复、路径可回滚、chaos 验证全链路

---

## 📋 实现顺序（最小风险）

### Step 1：DLQ 入队与结构（30min）
**文件：** `dlq.py` + `dead_letters.jsonl`

**结构：**
```json
{
  "task_id": "task-xxx",
  "attempts": 3,
  "last_error": "timeout after 120s",
  "timestamp": "2026-03-07T10:00:00",
  "status": "pending_review"
}
```

**要点：**
- 重试耗尽（attempts >= max）→ 写入 `dead_letters.jsonl`
- 人工介入 = 读文件 → 修改 → 重新 enqueue
- 每次写入必须有审计日志（append-only）

**DoD：**
- [ ] `dead_letters.jsonl` 格式正确（含 task_id/attempts/last_error/timestamp）
- [ ] 重试耗尽自动写入 DLQ
- [ ] DLQ 漏记率 = 0（单测验证）

---

### Step 2：人工介入通道（20min）
**文件：** `dlq_operator.py`

**两个动作（必须审计日志）：**
```python
def replay(task_id: str, operator: str = "human") -> bool:
    """重新入队，记录审计日志"""
    pass

def discard(task_id: str, reason: str, operator: str = "human") -> bool:
    """丢弃任务，记录审计日志"""
    pass
```

**审计日志格式：**
```json
{
  "action": "replay",
  "task_id": "task-xxx",
  "operator": "human",
  "timestamp": "2026-03-07T10:05:00",
  "reason": "fixed dependency issue"
}
```

**DoD：**
- [ ] `replay` / `discard` 两个动作均有审计日志
- [ ] 审计日志 append-only，不可修改
- [ ] Telegram 通知（DLQ 新增任务时推送）

---

### Step 3：Executor Fallback（40min）
**文件：** `executor_fallback.py`

**核心逻辑：**
```python
def execute_with_fallback(task_id: str, primary_executor: str, fallback_executor: str) -> dict:
    """
    1. 尝试 primary_executor
    2. 心跳超时 → 强制释放 spawn_lock（force_release）
    3. 切换到 fallback_executor
    4. 记录切换事件
    """
    pass
```

**⚠️ 关键：防双写**
```python
# fallback 触发前必须先强制释放原锁
spawn_lock.force_release(task_id)
# 然后再切换 fallback
```

**DoD：**
- [ ] executor 心跳超时 → 自动切换 fallback
- [ ] fallback 前强制 `spawn_lock.force_release(task_id)`（防双写）
- [ ] 切换事件记录到 `fallback_events.jsonl`
- [ ] 与 spawn_lock 交互正确（原锁释放或过期后才切换）

---

### Step 4：pipeline_timings 基线采集（15min）
**文件：** `pipeline_timings.py`

**采集点：**
```
submit → route → spawn → execute → complete
```

**输出：** `pipeline_timings.jsonl`
```json
{
  "task_id": "task-xxx",
  "submit_ts": 1000,
  "route_ts": 1001,
  "spawn_ts": 1002,
  "execute_ts": 1005,
  "complete_ts": 1025,
  "total_ms": 25000,
  "stage_ms": {
    "submit_to_route": 1,
    "route_to_spawn": 1,
    "spawn_to_execute": 3,
    "execute_to_complete": 20
  }
}
```

**DoD：**
- [ ] 真实负载跑一轮，采集基线数据
- [ ] `pipeline_timings.jsonl` 有至少 10 条记录
- [ ] submit→execute p95 延迟有基线值（Week 1 chaos 测试对比用）

---

### Step 5：Chaos + e2e 回归（60min）
**文件：** `chaos_test.py`

**测试场景：**

| 场景 | 操作 | 预期结果 |
|------|------|----------|
| executor 随机 kill | `taskkill /F /PID <executor_pid>` | DLQ 兜底 + fallback 切换 |
| 网络抖动（假死） | 暂停心跳 30s | fallback 触发，原锁释放 |
| 重试耗尽 | 强制 3 次失败 | 写入 DLQ，Telegram 告警 |
| DLQ replay | 手动 replay | 任务重新执行成功 |
| 指标回归 | chaos 后等待恢复 | 成功率回归基线 |

**全链路验证：**
```
随机 kill executor
    ↓
心跳超时检测
    ↓
spawn_lock.force_release(task_id)
    ↓
fallback executor 接管
    ↓
任务完成 or 重试耗尽 → DLQ
    ↓
人工介入（replay/discard）
    ↓
指标回归基线
```

**DoD：**
- [ ] 随机 kill executor → DLQ 兜底验证通过
- [ ] fallback 切换 → 无双写（spawn_lock 正确释放）
- [ ] 恢复后指标回归基线（成功率 ≥ 90%）
- [ ] 全链路耗时 ≤ MTTR 目标（10min）

---

## ✅ 测试矩阵

| 测试类型 | 文件 | 覆盖场景 | 通过标准 |
|----------|------|----------|----------|
| 单测 | `test_dlq.py` | DLQ 写入/读取/格式 | 全绿 |
| 单测 | `test_dlq_operator.py` | replay/discard/审计日志 | 全绿 |
| 单测 | `test_executor_fallback.py` | fallback 触发/force_release/防双写 | 全绿 |
| 单测 | `test_pipeline_timings.py` | 耗时采集/格式验证 | 全绿 |
| 集成 | `test_dlq_integration.py` | 重试耗尽→DLQ→replay 全流程 | 全绿 |
| 集成 | `test_fallback_integration.py` | executor 超时→fallback→完成 | 全绿 |
| e2e | `chaos_test.py` | 随机 kill + 恢复验证 | 全链路通过 |

**总计：** 7 个测试文件，预期全绿

---

## 📊 Week 1 验收标准（DoD）

### 功能验收（5/5 全绿）
- [ ] DLQ 入队与结构（dead_letters.jsonl 格式正确）
- [ ] 人工介入通道（replay/discard 有审计日志）
- [ ] Executor fallback（超时自动切换，防双写）
- [ ] pipeline_timings 基线（至少 10 条真实数据）
- [ ] Chaos/e2e 回归（全链路验证通过）

### SLO 验收（4/4 达标）
- [ ] 重复误执行率 = 0（硬门槛不变）
- [ ] DLQ 漏记率 = 0（有监控）
- [ ] submit→execute p95 增幅 ≤ 20%（对比基线）
- [ ] MTTR ≤ 10min（chaos 测试验证）

### 风险验收（2/2 通过）
- [ ] fallback 触发时无双写（force_release 验证）
- [ ] DLQ 积压告警正常（超阈值推送 Telegram）

---

## ⚠️ 最容易踩的坑

1. **fallback 双写** - fallback 触发时原 executor 可能还活着（假死/网络抖动），必须先 `spawn_lock.force_release(task_id)` 再切换
2. **DLQ 漏记** - 重试耗尽的判断条件要和 retry_config 保持一致（`attempts >= max_attempts`）
3. **审计日志缺失** - replay/discard 必须写审计日志，不能只改状态
4. **pipeline_timings 基线** - Week 1 chaos 测试需要对比数据，尽早跑一轮真实负载

---

## 🚀 执行计划

**总时间：** 3 天（2026-03-07 ~ 2026-03-09）

| 时间 | 任务 |
|------|------|
| Day 1（03-07）上午 | DLQ 入队 + 人工介入通道 |
| Day 1（03-07）下午 | Executor fallback + 防双写 |
| Day 2（03-08）上午 | pipeline_timings 基线采集 |
| Day 2（03-08）下午 | 单测 + 集成测试全绿 |
| Day 3（03-09）全天 | Chaos/e2e 回归 + 验收报告 |

---

**版本：** v1.0  
**创建时间：** 2026-03-06 19:20  
**维护者：** 小九 + 珊瑚海
