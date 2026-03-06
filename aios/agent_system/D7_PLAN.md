# D7 Plan（Reliability First）

**版本：** v1.0  
**创建时间：** 2026-03-06  
**状态：** 草稿（待确认）

---

## 1. 目标与非目标

**目标：**
- 重试机制（指数退避，可配置）
- 幂等保障（task_id 去重，spawn_lock 扩展）
- 恢复能力（executor 故障 fallback，死信队列）
- 降低执行失败率与人工介入成本

**非目标（留到 D8）：**
- 吞吐优化 / 大规模性能调优
- 多机部署 / 分布式锁（除非方案 A 触发迁移条件）
- 新功能开发

---

## 2. 成功指标（SLO）

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 任务成功率 | >= 90% | 含重试后最终成功 |
| 重试后恢复率 | >= 75% | 失败任务经重试恢复的比例 |
| 重复任务误执行率 | = 0 | 幂等保障，同一 task_id 不重跑 |
| MTTR | <= 10 分钟 | 从故障检测到恢复完成 |

> 基线参考：当前成功率 ~80.4%（2026-03-05 观测），目标提升至 90%+

---

## 3. 里程碑

### Day 1（核心防护）
**目标：** 并发安全 + 去重基础

- [ ] 并发提交与重入安全测试（补充现有 spawn_lock 测试用例）
- [ ] task_id 去重逻辑（task_queue.jsonl 层面）
- [ ] 去重单测覆盖

**DoD：** 关键用例全绿，无重复执行

---

### Day 3（重试 + 幂等）
**目标：** 失败可重试，重复不重跑，指标可观测

- [ ] 指数退避重试（max=3，初始间隔可配置，默认 5s）
- [ ] spawn_lock 幂等扩展（覆盖 retry 场景）
- [ ] submit → route → spawn → execute 耗时基线采集
- [ ] 重试指标写入 spawn_lock_metrics.json

**DoD：** 失败可重试、重复不重跑、指标可观测

---

### Week 1（恢复能力）
**目标：** 故障可恢复，路径可回滚

- [ ] executor 故障 fallback（超时/崩溃自动切换备用路径）
- [ ] 死信队列（DLQ）：重试耗尽后进入 dlq.jsonl，触发人工介入通知
- [ ] chaos/e2e 回归（随机杀 executor + 恢复验证）
- [ ] 回滚步骤文档化

**DoD：** 故障可恢复、路径可回滚

---

## 4. 测试策略

| 层级 | 覆盖内容 |
|------|----------|
| 单测 | 重试策略逻辑、去重逻辑、退避计算 |
| 集成测试 | 并发提交、权限异常、坏输入、幂等命中 |
| e2e | 随机杀 executor + 恢复验证、DLQ 触发流程 |

---

## 5. 发布与回滚

**灰度开关：**
- `retry_enabled`（默认 true，可关闭）
- `dedup_enabled`（默认 true，可关闭）
- `dlq_enabled`（默认 true，可关闭）

**监控项：**
- `retry_total` / `retry_success_total` / `retry_exhausted_total`
- `dedup_hit_total`
- `dlq_size`
- `mttr_seconds`

**回滚步骤：**
1. 关闭灰度开关（`retry_enabled=false`）
2. 清空 retry 队列（`retry_queue.jsonl`）
3. 恢复 task_executor.py 上一版本（git revert）
4. 验证 Heartbeat 正常运行

---

## 6. 依赖与风险

| 依赖 | 状态 |
|------|------|
| spawn_lock.py（方案 A） | ✅ 运行中（观测期至 2026-03-08） |
| task_queue.jsonl | ✅ 已有 |
| task_executor.py | ✅ 已有 |
| lessons.json / LowSuccess_Agent | ✅ 已有（Phase 3 完成） |

| 风险 | 缓解措施 |
|------|----------|
| 重试风暴（retry storm） | 指数退避 + max=3 上限 + jitter |
| 幂等漏洞（clock skew） | task_id 基于内容哈希，不依赖时间戳 |
| DLQ 积压 | 每日简报自动统计 DLQ 大小，超阈值告警 |

---

## 7. 与现有系统的关系

```
D7 新增层
    ↓
[重试层] task_executor.py + retry_queue.jsonl
    ↓
[幂等层] spawn_lock.py（扩展）+ task_id 去重
    ↓
[恢复层] DLQ + fallback + LowSuccess_Agent（已有）
    ↓
现有 Heartbeat v5.0 / spawn 流程（不变）
```

D7 在现有架构上叠加，不重写核心流程。

---

**维护者：** 小九 + 珊瑚海  
**下一步：** 确认 SLO 数值（X/Y/Z），开始 Day 1 实现
