# Recovery 机制字段名对齐审查清单

## 1. 核心约束验证 ✅

### 1.1 transition_status 原子更新
- ✅ WHERE task_id AND status（CAS 语义）
- ✅ running → queued 时清空 worker_id / started_at / last_heartbeat_at
- ✅ 状态不匹配时返回 False（CAS 失败）

### 1.2 周期恢复门控
- ✅ now_ts - _last_recovery_ts >= recovery_interval_seconds
- ✅ 成功失败都更新 _last_recovery_ts（防抖）

### 1.3 启动恢复
- ✅ HeartbeatSchedulerV5.start() 调用 _recover_on_boot()
- ✅ 异常吞掉不阻塞主循环

---

## 2. 字段名对齐检查

### 2.1 Task 对象字段（task_queue.jsonl）

| 字段名 | 用途 | 清空规则 |
|--------|------|----------|
| `id` / `task_id` | 任务唯一标识 | 永不清空 |
| `status` | 任务状态（queued/running/completed/failed） | 状态转换时更新 |
| `worker_id` | 执行 worker 标识 | running → queued 时清空 |
| `started_at` | 任务开始时间戳 | running → queued 时清空 |
| `last_heartbeat_at` | 最后心跳时间戳 | running → queued 时清空 |
| `created_at` | 任务创建时间戳 | 永不清空 |
| `updated_at` | 任务更新时间戳 | 每次状态转换时更新 |
| `zombie_retries` | 僵尸任务重试次数 | 恢复时递增 |
| `zombie_note` | 恢复原因备注 | 恢复时写入 |

**验证结果：**
- ✅ `transition_status` 正确清空 worker_id / started_at / last_heartbeat_at
- ✅ `updated_at` 在每次状态转换时自动更新
- ✅ `zombie_retries` 在恢复时正确递增

### 2.2 Spawn Lock 字段（spawn_locks.json）

| 字段名 | 用途 | 清理规则 |
|--------|------|----------|
| `task_key` | 幂等 key（task_id:vN） | 锁过期时删除 |
| `worker_id` | 持有锁的 worker | 锁过期时删除 |
| `lock_token` | 锁令牌（UUID） | 锁过期时删除 |
| `locked_at` | 加锁时间戳 | 锁过期时删除 |

**验证结果：**
- ✅ `startup_cleanup()` 正确清理过期锁
- ✅ `release_spawn_lock()` 校验 lock_token（CAS 保护）

### 2.3 Metrics 字段（spawn_lock_metrics.json）

| 字段名 | 用途 | 更新时机 |
|--------|------|----------|
| `acquire_total` | 总加锁次数 | 每次 acquire() |
| `acquire_success` | 成功加锁次数 | 加锁成功时 |
| `idempotent_hit_total` | 幂等命中次数 | 幂等命中时 |
| `stale_lock_recovered_total` | 过期锁恢复次数 | 抢占过期锁时 |
| `acquire_latency_ms_sum` | 加锁延迟总和 | 每次 acquire() |

**验证结果：**
- ✅ `get_idempotency_metrics()` 正确计算 hit_rate 和 avg_latency
- ✅ Heartbeat 输出包含 idempotent_hit_rate 和 stale_lock_recovered_total

---

## 3. 易漏点检查 ✅

### 3.1 transition_status 必须是 WHERE task_id AND status
```python
# ✅ 正确实现
if task.get("status") != from_status:
    return False  # CAS 失败
```

### 3.2 running → queued 时清空 worker 字段
```python
# ✅ 正确实现
if from_status == "running" and to_status == "queued":
    task.pop("worker_id", None)
    task.pop("started_at", None)
    task.pop("last_heartbeat_at", None)
```

### 3.3 周期恢复门控（防抖）
```python
# ✅ 正确实现
elapsed = now_ts - self._last_recovery_ts
if elapsed < self.recovery_interval_seconds:
    return

# 先更新时间戳（防抖）
self._last_recovery_ts = now_ts

# 然后执行恢复（即使失败也不会立刻重试）
```

---

## 4. 集成验证 ✅

### 4.1 HeartbeatSchedulerV5 类
- ✅ `__init__()` 初始化参数（recovery_timeout_seconds / recovery_interval_seconds / recovery_scan_limit）
- ✅ `start()` 启动时执行 boot recovery
- ✅ `tick()` 每次心跳检查周期 recovery
- ✅ `_run_loop()` 主循环（调用 main() + tick()）

### 4.2 spawn_lock.py 导出接口
- ✅ `transition_status(task, from_status, to_status, extra)` - 原子状态转换
- ✅ `recover_stale_locks(timeout_seconds, scan_limit)` - 周期恢复
- ✅ `startup_cleanup()` - 启动清理
- ✅ `try_acquire_spawn_lock(task)` - 幂等加锁
- ✅ `release_spawn_lock(task, token)` - 释放锁
- ✅ `get_idempotency_metrics()` - 获取指标

### 4.3 heartbeat_v5.py 集成
- ✅ 导入 `transition_status` 和 `recover_stale_locks`
- ✅ `reclaim_zombie_tasks()` 使用 `transition_status` 原子更新
- ✅ `main()` 在开头调用 `startup_cleanup()`
- ✅ `HeartbeatSchedulerV5` 类完整实现

---

## 5. 测试覆盖 ✅

### 5.1 单元测试（test_recovery_integration.py）
- ✅ Test 1: transition_status 原子更新 + CAS 保护
- ✅ Test 2: recover_stale_locks 周期恢复（超时任务 → queued）
- ✅ Test 3: reclaim_zombie_tasks（Heartbeat 集成版本）

### 5.2 集成测试
- ✅ 导入验证（HeartbeatSchedulerV5 / transition_status / recover_stale_locks）
- ✅ 端到端测试（test_recovery_integration.py 全部通过）

---

## 6. 观察期指标（2026-03-06 ~ 2026-03-08）

### 6.1 核心指标
- `lock_acquire_latency_ms_avg` < 10ms（健康）/ > 50ms（告警）
- `idempotent_hit_rate` 5-20%（健康）/ < 1%（告警）
- `stale_lock_recovered_total` < 5（健康）/ > 10/hour（告警）

### 6.2 恢复效果
- 僵尸任务恢复率 > 95%
- 重试成功率 > 80%
- 永久失败率 < 5%

### 6.3 性能影响
- Heartbeat 延迟增加 < 100ms
- 队列扫描时间 < 50ms（1000 任务）

---

## 7. 后续优化方向

### 7.1 方案 B 迁移（Redis）
- 替换 LockStore 实现（接口保持不变）
- 分布式锁（支持多 worker）
- 更低延迟（< 5ms）

### 7.2 监控增强
- Grafana 仪表盘（实时指标）
- 告警规则（Prometheus）
- 日志聚合（ELK）

### 7.3 恢复策略优化
- 自适应超时（根据任务类型动态调整）
- 优先级队列（高优先级任务优先恢复）
- 智能重试（根据失败原因选择策略）

---

**审查结论：✅ 所有字段名对齐，三个易漏点全部覆盖，集成测试通过。**

**下一步：** 进入 48h 观察期（2026-03-06 12:00 ~ 2026-03-08 12:00）
