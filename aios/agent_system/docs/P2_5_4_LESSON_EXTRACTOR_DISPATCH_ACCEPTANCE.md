# P2.5-4 Lesson Extractor Dispatch 验收文档

**版本：** 1.0.0  
**日期：** 2026-03-11  
**状态：** ✅ 验收通过

---

## 目标

让 lesson-extractor 消费 dispatch patterns + health diagnosis + dispatch_log，把中枢层面的重复现象沉淀成结构化 lesson。

把"总是降级、总是 retry_later、总是同一个 handler"从"观察结果"升级成"可复用规则"。

---

## 交付物

### 1. 核心模块

**dispatch_lesson_extractor.py**
- ✅ 支持 4 类 lesson 提取
- ✅ 支持去重（避免重复 lesson）
- ✅ 每条 lesson 都有证据
- ✅ 每条 lesson 都指向消费模块
- ✅ 生成结构化 JSON 和可读总结

### 2. 测试套件

**test_dispatch_lesson_extractor.py**
- ✅ 9 个测试用例全部通过
- ✅ 覆盖 4 类 lesson 提取
- ✅ 覆盖去重逻辑
- ✅ 覆盖保存和追加逻辑

### 3. 输出文件

- ✅ `new_dispatch_lessons.json` - 新提取的 lesson
- ✅ `dispatch_lessons_summary.md` - 可读总结
- ✅ 写回 `lessons.json` 的新条目

### 4. 文档

**docs/P2_5_4_LESSON_EXTRACTOR_DISPATCH_ACCEPTANCE.md**（本文档）

---

## 验收标准（5/5 通过）

### 1. ✅ 能从 dispatch pattern 中提取 lesson

**测试：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python dispatch_lesson_extractor.py
```

**结果：**
```
✅ 提取到 3 条新 lesson
```

### 2. ✅ 能避免和已有 lessons.json 重复

**实现：**
- 加载已有 lesson 的 `lesson_id` 和 `trigger_pattern`
- 提取前检查是否重复
- 重复的 lesson 不会被提取

**测试验证：**
- `test_avoid_duplicate_lessons` 通过

### 3. ✅ 每条 lesson 都有证据，不是空泛总结

**示例：**
```json
{
  "lesson_type": "fallback_single_path",
  "trigger_pattern": "retry_later (→ degraded) used in 100% of fallback cases",
  "evidence": [
    "retry_later (→ degraded)"
  ]
}
```

**验证：**
- 所有 lesson 的 `evidence` 字段都非空
- 证据来自真实的 dispatch_log 和 pattern_report

### 4. ✅ 每条 lesson 都能指向一个后续消费模块

**示例：**
```json
{
  "consumer_modules": ["policy-decision", "health-monitor"]
}
```

**验证：**
- 所有 lesson 的 `consumer_modules` 字段都非空
- 消费模块明确且合理

### 5. ✅ 能产出一句"当前最值得写回系统规则的经验"

**输出：**
```
当前最值得沉淀的中枢经验：degrade policy used in 100% of decisions
当前最明显的错误假设：all tasks should be degraded by default for safety
当前最应该写回系统规则的改进：add policy rules to allow safe tasks without degradation
这条经验下一步应被哪个模块消费：policy-decision, unified-router
```

---

## 4 类 Lesson 定义

### 1. policy_over_conservative（策略过于保守）

**触发条件：**
- degrade policy 占比 > 80%

**示例：**
```json
{
  "lesson_type": "policy_over_conservative",
  "trigger_pattern": "degrade policy used in 100% of decisions",
  "false_assumption": "all tasks should be degraded by default for safety",
  "correct_model": "differentiate safe tasks from risky tasks, apply degrade selectively",
  "recommended_rule": "add policy rules to allow safe tasks without degradation",
  "consumer_modules": ["policy-decision", "unified-router"]
}
```

### 2. fallback_single_path（Fallback 路径单一）

**触发条件：**
- 只有一种 fallback，或某个 fallback 占比 > 80%

**示例：**
```json
{
  "lesson_type": "fallback_single_path",
  "trigger_pattern": "retry_later (→ degraded) used in 100% of fallback cases",
  "false_assumption": "single fallback path is sufficient for all degraded states",
  "correct_model": "different degraded situations need differentiated fallback paths",
  "recommended_rule": "add fallback types: escalate (for critical), notify (for alerts), skip (for low-priority)",
  "consumer_modules": ["policy-decision", "health-monitor"]
}
```

### 3. handler_distribution_too_narrow（Handler 分布过窄）

**触发条件：**
- 某个 handler 被选择的占比 > 80%

**示例：**
```json
{
  "lesson_type": "handler_distribution_too_narrow",
  "trigger_pattern": "aios-health-monitor chosen in 100% of decisions",
  "false_assumption": "one handler can handle most tasks effectively",
  "correct_model": "diverse handler distribution indicates healthy routing",
  "recommended_rule": "add more handler routing samples, verify router is not biased",
  "consumer_modules": ["unified-router", "health-monitor"]
}
```

### 4. handler_rejection_bias（Handler 淘汰偏见）

**触发条件：**
- 某个 handler 被淘汰 >= 3 次，且总被同一个 handler 替代

**示例：**
```json
{
  "lesson_type": "handler_rejection_bias",
  "trigger_pattern": "pattern-detector always rejected in favor of aios-health-monitor",
  "false_assumption": "aios-health-monitor is always better than pattern-detector",
  "correct_model": "different handlers excel in different contexts",
  "recommended_rule": "review routing logic: is pattern-detector truly unsuitable, or is aios-health-monitor over-prioritized?",
  "consumer_modules": ["unified-router"]
}
```

---

## Lesson 结构

```json
{
  "lesson_id": "dispatch_policy_conservative_20260311_085838",
  "lesson_type": "policy_over_conservative",
  "trigger_pattern": "degrade policy used in 100% of decisions",
  "false_assumption": "all tasks should be degraded by default for safety",
  "correct_model": "differentiate safe tasks from risky tasks, apply degrade selectively",
  "evidence": [
    "degrade: 匹配规则: 系统降级状态 + 中高风险 → 降级执行 | ..."
  ],
  "recommended_rule": "add policy rules to allow safe tasks without degradation",
  "consumer_modules": ["policy-decision", "unified-router"],
  "confidence": 0.9,
  "extracted_at": "2026-03-11T08:58:38.459339"
}
```

**必需字段：**
- `lesson_id` - 唯一标识
- `lesson_type` - 类型（4 种之一）
- `trigger_pattern` - 触发模式
- `false_assumption` - 错误假设
- `correct_model` - 正确模型
- `evidence` - 证据列表
- `recommended_rule` - 推荐规则
- `consumer_modules` - 消费模块列表
- `confidence` - 置信度（0-1）
- `extracted_at` - 提取时间

---

## 测试结果

### 单元测试

```bash
pytest test_dispatch_lesson_extractor.py -v
```

**结果：** ✅ 9/9 通过

```
test_extract_policy_over_conservative PASSED
test_extract_fallback_single_path PASSED
test_extract_handler_distribution_too_narrow PASSED
test_extract_handler_rejection_bias PASSED
test_lesson_structure PASSED
test_avoid_duplicate_lessons PASSED
test_save_and_append_lessons PASSED
test_generate_summary PASSED
test_empty_pattern_report PASSED
```

### 真实数据测试

```bash
python dispatch_lesson_extractor.py
```

**结果：** ✅ 成功提取 3 条 lesson

---

## 真实数据提取结果

基于当前 dispatch_log.jsonl（6 条记录）和 dispatch_pattern_report.json：

### Lesson 1: policy_over_conservative

**触发模式：** degrade policy used in 100% of decisions

**错误假设：** all tasks should be degraded by default for safety

**正确模型：** differentiate safe tasks from risky tasks, apply degrade selectively

**推荐规则：** add policy rules to allow safe tasks without degradation

**消费模块：** policy-decision, unified-router

**置信度：** 0.90

### Lesson 2: fallback_single_path

**触发模式：** retry_later (→ degraded) used in 100% of fallback cases

**错误假设：** single fallback path is sufficient for all degraded states

**正确模型：** different degraded situations need differentiated fallback paths

**推荐规则：** add fallback types: escalate (for critical), notify (for alerts), skip (for low-priority)

**消费模块：** policy-decision, health-monitor

**置信度：** 0.90

### Lesson 3: handler_distribution_too_narrow

**触发模式：** aios-health-monitor chosen in 100% of decisions

**错误假设：** one handler can handle most tasks effectively

**正确模型：** diverse handler distribution indicates healthy routing

**推荐规则：** add more handler routing samples, verify router is not biased

**消费模块：** unified-router, health-monitor

**置信度：** 0.90

---

## 固定结论句式

```
当前最值得沉淀的中枢经验：<trigger_pattern>
当前最明显的错误假设：<false_assumption>
当前最应该写回系统规则的改进：<recommended_rule>
这条经验下一步应被哪个模块消费：<consumer_modules>
```

**实际输出：**
```
当前最值得沉淀的中枢经验：degrade policy used in 100% of decisions
当前最明显的错误假设：all tasks should be degraded by default for safety
当前最应该写回系统规则的改进：add policy rules to allow safe tasks without degradation
这条经验下一步应被哪个模块消费：policy-decision, unified-router
```

---

## 关键设计决策

### 1. 先沉淀经验，不直接改规则

P2.5-4 只做：
```
pattern → lesson
```

不做：
```
pattern → 自动修改 policy
```

**原因：** 更稳定，避免自动改规则导致的风险

### 2. 支持两种 lessons.json 格式

- 列表格式：`[{lesson1}, {lesson2}]`
- 字典格式：`{"lessons": [{lesson1}, {lesson2}]}`

**原因：** 兼容已有数据

### 3. 去重机制

- 基于 `lesson_id` 和 `trigger_pattern`
- 避免重复提取相同 lesson

---

## 下一步：P2.5-5

**目标：** 让 policy-decision 消费 lesson

**闭环：**
```
dispatch 产生决策日志
  ↓
health / pattern 看出模式
  ↓
lesson 提取经验
  ↓
policy 吃 lesson 改进护栏  ← P2.5-5
```

这就是"会学习的中枢"。

---

## 版本历史

- **v1.0.0** (2026-03-11) - 初始版本，支持 4 类 lesson 提取

---

**验收人：** 小九  
**验收日期：** 2026-03-11  
**验收结论：** ✅ 通过
