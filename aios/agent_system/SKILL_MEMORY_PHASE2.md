# Skill Memory Phase 2 - 连续失败预警 + 版本对比

**完成时间：** 2026-03-07 15:50  
**状态：** ✅ 已完成并验证

---

## 核心功能

### 1. 连续失败预警（Skill Failure Alert）

**文件：** `skill_failure_alert.py`

**功能：**
- 检测连续失败（warn: 2次 / crit: 3次）
- 提取最近失败原因（自动分类 8 种错误类型）
- 推荐恢复策略（基于错误类型）
- 记录告警日志（`skill_failure_alerts.jsonl`）

**告警级别：**
- **warn**：连续失败 2 次
- **crit**：连续失败 3 次

**错误类型分类：**
- `timeout` → `increase_timeout_and_retry`
- `encoding_error` → `try_multiple_encodings`
- `file_not_found` → `check_file_path_and_retry`
- `permission_denied` → `check_permissions_and_retry`
- `resource_exhausted` → `reduce_batch_size_and_retry`
- `network_error` → `retry_with_backoff`
- `syntax_error` → `validate_input_and_retry`
- `unknown` → `default_recovery`

**输出格式：**
```
🔴 CRIT: pdf-skill v1.0.0
   连续失败: 3 次
   最近原因: timeout
   建议动作: increase_timeout_and_retry
   检测窗口: 最近 5 次执行
```

**集成点：**
- `heartbeat_v5.py`（每小时检查）
- 输出前 3 个告警

---

### 2. 版本对比（Skill Version Comparison）

**文件：** `skill_version_comparison.py`

**功能：**
- 比较同 skill_name 下相邻版本
- 对比 3 个指标：成功率、平均耗时、最近 7 天使用次数
- 输出趋势：improved / degraded / neutral
- 持久化对比结果（`skill_version_comparison.json`）

**对比指标：**
1. **成功率**：delta > 5% = improved / < -5% = degraded
2. **平均耗时**：delta < -500ms = improved / > 500ms = degraded
3. **7天使用次数**：delta > 2 = improved / < -2 = degraded

**综合趋势：**
- 3 个指标投票，2+ improved = improved
- 2+ degraded = degraded
- 其他 = neutral

**输出格式：**
```
📈 pdf-skill v1.0.0 → v1.1.0
   成功率: 72% → 89% (+17%) 📈
   耗时: 18400ms → 12100ms (-6300ms) 📈
   7天使用: 15 → 23 (+8) 📈
```

**集成点：**
- `daily_metrics.py`（每日简报）
- 显示最多 5 个版本对比

---

## 验证结果

### 连续失败预警测试

**测试场景：** test-skill 连续失败 3 次（timeout）

**结果：**
```
✓ 检测到 1 个告警
✓ alert_level: crit
✓ consecutive_failures: 3
✓ last_failure_reason: timeout
✓ suggested_recovery: increase_timeout_and_retry
```

### 版本对比测试

**测试场景：** version-test-skill v1.0.0 → v2.0.0（成功率 80% → 90%, 耗时 2450ms → 1425ms）

**结果：**
```
✓ 成功率: +10.0% (improved)
✓ 耗时: -1025ms (improved)
✓ 7天使用: +4 (improved)
✓ overall_trend: improved
```

---

## 使用方式

### 手动运行

**连续失败预警：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python skill_failure_alert.py
```

**版本对比：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python skill_version_comparison.py

# 指定 skill_id
python skill_version_comparison.py --skill pdf-skill
```

### 自动集成

**Heartbeat（每小时）：**
- 连续失败预警（显示前 3 个告警）

**Daily Metrics（每日简报）：**
- 版本对比摘要（显示最多 5 个）

---

## 数据文件

**输入：**
- `data/skill_executions.jsonl` - 执行记录（由 `skill_memory.py` 自动写入）

**输出：**
- `data/skill_failure_alerts.jsonl` - 告警日志
- `data/skill_version_comparison.json` - 版本对比结果

---

## 下一步计划

**Phase 3: 智能推荐（4小时）**
- 实现 `recommend_skill()` - 根据任务推荐最佳 Skill
- 实现 `recommend_recovery()` - 失败时推荐恢复策略
- 集成到 Router 和 LowSuccess_Agent

**Phase 4: 演化系统（5小时）**
- 实现 `calculate_skill_evolution_score()` - 计算技能演化分数
- 实现 `suggest_skill_improvements()` - 自动生成优化建议
- 集成到 Self-Improving Loop

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-07 15:50
