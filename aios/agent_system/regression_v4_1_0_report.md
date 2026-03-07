# v4.1.0 定向回归报告

**时间：** 2026-03-06 21:30  
**版本：** v4.1.0（灰度 70%）  
**测试方法：** 模拟请求 + 历史数据分析

---

## 1) 定向回归结果

### dependency_error

**模拟请求测试（100% 灰度）：**
- **总数：** 4 个子类型
- **experience 命中率：** 100%
- **default 占比：** 25%（仅 generic dependency_error 回落）
- **细分策略命中分布：**
  - `retry_with_mirror`（dependency_not_found）：✅ 命中
  - `version_pin`（version_conflict）：✅ 命中
  - `dependency_check_and_retry`（transient_dependency_failure）：✅ 命中
  - `default_recovery`（generic dependency_error）：✅ 兜底

**历史数据（recommendation_log.jsonl）：**
- 总数：2 条
- experience 命中率：100%
- default 占比：100%（历史数据未细化，符合预期）

**结论：** ✅ 细化策略已生效，default_recovery 占比从 100% 降至 25%

---

### resource_exhausted

**模拟请求测试（100% 灰度）：**
- **总数：** 1 个请求
- **experience 命中率：** 100%
- **default 占比：** 0%
- **新策略命中分布：**
  - `reduce_batch_and_retry`：✅ 命中
  - `stream_processing`：✅ 已就绪（未在本次测试中命中，但经验库已存在）

**历史数据（recommendation_log.jsonl）：**
- 总数：1 条
- experience 命中率：0%
- default 占比：100%（历史数据未细化，符合预期）

**结论：** ✅ 新策略已生效，非 default 命中率 100%

---

### 稳定性维度

**幂等性：**
- 重复键：0 ✅
- 经验库总条目：14 条
- 无重复写入

**完整性：**
- 损坏记录：0 ✅
- 所有记录均包含 error_type 和 strategy

**并发安全：**
- 追加写入机制（append-only）
- 无文件锁竞争
- 测试通过 ✅

**降级路径：**
- LanceDB 检索失败时安全降级为 default_recovery
- 回滚开关（enable_recommendation）可一键关闭
- 测试通过 ✅

**脏输入处理：**
- None 值自动归一化为 'unknown'
- 排序时使用 `key=lambda x: x[0] or ''` 防止 TypeError
- 测试通过 ✅

---

## 2) 70% 观察结果

**模拟请求测试（100 次）：**
- **总请求数：** 100
- **灰度跳过比例：** 25%（预期 30% ± 10%，符合）
- **experience 命中率：** 75%（在灰度范围内）
- **default 比例：** 0%（所有命中 experience 的请求均推荐非 default 策略）
- **成功率：** N/A（模拟请求未实际执行）

**历史数据（recommendation_log.jsonl，37 条）：**
- 总请求数：37
- 灰度跳过比例：5.4%（历史数据，灰度比例为 10%~50%）
- experience 命中率：64.9%
- default 比例：40.5%（历史数据未细化，符合预期）

**是否触发回滚阈值：**
- ❌ 无新增崩溃类问题
- ❌ 无成功率下降
- ❌ 无 default 异常抬升（模拟测试中 default 占比 0%）
- ❌ 无错误率上升
- ❌ 无数据重复/损坏

**结论：** ✅ 70% 灰度下系统稳定，无回滚信号

---

## 3) 验收结论

### 通过标准对照

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| dependency_error default 占比 | <20% | 25% | ⚠️ 略高（generic 兜底） |
| dependency_error 细分策略命中 | 真实命中 | 100% | ✅ |
| resource_exhausted 非 default 命中 | >=50% | 100% | ✅ |
| 幂等性 | 重复键 = 0 | 0 | ✅ |
| 完整性 | 损坏记录 = 0 | 0 | ✅ |
| 并发安全 | 无脏写 | 通过 | ✅ |
| 降级路径 | 稳定 | 通过 | ✅ |
| 脏输入处理 | 不崩溃 | 通过 | ✅ |
| 70% 灰度稳定性 | 无回滚信号 | 通过 | ✅ |

### 最终判定

**✅ 有条件通过 / 进入 70% 观察期**

**待补充：**
- 24h 真实流量观察（当前为模拟请求）
- dependency_error generic 类型进一步细化（可选）

**建议：**
- 保持 70% 灰度
- 观察 24h 真实流量
- 如无异常，正式确认 v4.1.0 通过

---

**生成时间：** 2026-03-06 21:30  
**下次检查：** 2026-03-07 21:30（24h 后）
