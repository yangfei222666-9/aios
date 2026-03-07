# Spawn Lock 运行文档

**动作生命周期与状态机定义见 `REALITY_LEDGER.md`**

---

## 当前方案：A（本地文件锁）

**实现：** `spawn_lock.py` + `spawn_lock_monitor.py`  
**上线时间：** 2026-03-06 11:05  
**观测期：** 48 小时（至 2026-03-08 11:05）

## 核心指标与阈值

| 指标 | 健康范围 | 告警阈值 | 触发动作 |
|------|----------|----------|----------|
| `lock_acquire_latency_ms_avg` | < 10ms | > 50ms | 考虑切换到 Redis（方案 B） |
| `idempotent_hit_rate` | 5-20% | < 1% | 检查锁失效或配置错误 |
| `stale_lock_recovered_total` | < 5 | > 10/hour | 检查频繁崩溃或任务超时 |

## 方案 A 继续使用标准（48h 观测期结束后评估）

满足以下**全部条件**则继续使用方案 A：
- ✅ `lock_acquire_latency_ms_avg` 稳定 < 10ms
- ✅ `idempotent_hit_rate` 稳定在 5-20%
- ✅ `stale_lock_recovered_total` 保持低位（< 5）
- ✅ 无告警触发

## 方案 B（Redis）迁移触发条件

满足以下**任一条件**则启动迁移：
- ❌ `lock_acquire_latency_ms_avg` 持续 > 50ms（文件锁竞争加剧）
- ❌ `idempotent_hit_rate` 异常下降 < 1%（锁失效）
- ❌ `stale_lock_recovered_total` 增长 > 10/hour（频繁崩溃）
- ❌ 需要多机部署（方案 A 仅支持单机）

## 监控与告警

- **监控脚本：** `spawn_lock_monitor.py`（每小时整点运行）
- **告警输出：** `alerts.jsonl`（由 notifier 统一发送到 Telegram）
- **指标文件：** `spawn_lock_metrics.json`

## 48h 复盘模板

**复盘时间：** 2026-03-08 11:05

### 指标快照

```
lock_acquire_latency_ms_avg: ___ ms
idempotent_hit_rate: ____%
idempotent_hit_total: ___
acquire_total: ___
stale_lock_recovered_total: ___
```

### 告警记录

- [ ] 无告警
- [ ] 有告警（列出）：

### 结论

- [ ] ✅ 继续使用方案 A（所有指标健康）
- [ ] ⚠️ 观察延长 24h（部分指标接近阈值）
- [ ] ❌ 启动方案 B 迁移（触发迁移条件）

### 备注

（记录任何异常情况、特殊事件、或需要关注的点）

---

## 1.6h 初步复盘（2026-03-06 12:42）

**观测时长：** 1.6 小时（2026-03-06 11:05 ~ 12:42）

### 指标快照

```
lock_acquire_latency_ms_avg: 1.21 ms
idempotent_hit_rate: 13.6%
idempotent_hit_total: 3
acquire_total: 22
stale_lock_recovered_total: 3
stale_per_hour: 1.85 次/小时
```

### 健康度评估

- ✅ 平均延迟健康（1.21ms < 10ms）
- ✅ 幂等命中率健康（13.6% 在 5-20% 范围内）
- ✅ 陈旧锁恢复健康（3 次 < 5 次）

### 告警记录

- [x] 无告警

### 结论

- [x] ✅ 继续使用方案 A（所有指标健康）
- [ ] ⚠️ 观察延长 24h（部分指标接近阈值）
- [ ] ❌ 启动方案 B 迁移（触发迁移条件）

### 备注

**初步观察（1.6h）：**
- 锁性能优秀：平均延迟仅 1.21ms，远低于 10ms 健康阈值
- 幂等机制正常：13.6% 命中率表明重复请求被正确拦截
- 陈旧锁恢复正常：1.85 次/小时，说明偶尔有任务超时但恢复机制有效

**下一步：**
- 继续观察至 2026-03-08 11:05（完整 48h）
- 监控脚本每小时自动检查，如有异常会触发告警
- 如 48h 后所有指标仍健康，则方案 A 正式转正

---

## 6.8h 中期快照（2026-03-06 17:55）

**观测时长：** 6.8 小时（2026-03-06 11:05 ~ 17:55）

### 指标快照

```
lock_acquire_latency_ms_avg: 1.21 ms
idempotent_hit_rate: 13.6%
idempotent_hit_total: 3
acquire_total: 22
stale_lock_recovered_total: 4
stale_per_hour: 0.59 次/小时
```

### 健康度评估

- ✅ 平均延迟健康：1.21ms < 10ms
- ✅ 幂等命中率健康：13.6% 在 5-20% 范围内
- ✅ 陈旧锁恢复健康：4 次 < 5 次（0.59次/小时，极低）

### 结论

- [x] ✅ 继续使用方案 A（所有指标健康）

### 备注

与 1.6h 快照对比：
- 延迟稳定：1.21ms（无变化，锁竞争未加剧）
- 幂等命中率稳定：13.6%（重复请求拦截正常）
- 陈旧锁从 3 增至 4（+1），速率 0.59次/小时，仍在健康范围

**下一步：** 2026-03-08 11:05 执行最终 48h 复盘

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-06 17:55
