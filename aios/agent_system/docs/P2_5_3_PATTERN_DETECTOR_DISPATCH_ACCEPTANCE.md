# P2.5-3 Pattern Detector Dispatch 验收文档

**版本：** 1.0.0  
**日期：** 2026-03-11  
**状态：** ✅ 验收通过

---

## 目标

让 pattern-detector 从决策日志里识别中枢模式，回答：
- 哪类输入最常被拦截/降级
- 哪类 handler 最常被淘汰
- 哪类 policy 最常触发
- 哪类 fallback 最常被走

---

## 交付物

### 1. 核心模块

**dispatch_pattern_detector.py**
- ✅ 支持 4 类决策模式识别
- ✅ 支持嵌套和扁平两种日志格式
- ✅ 生成结构化报告（JSON）
- ✅ 输出固定句式总结
- ✅ 识别最值得优化的中枢路径

### 2. 测试套件

**test_dispatch_pattern_detector.py**
- ✅ 9 个测试用例全部通过
- ✅ 覆盖 4 类模式检测
- ✅ 覆盖完整分析流程
- ✅ 覆盖边界情况（空日志）

### 3. 文档

**docs/P2_5_3_PATTERN_DETECTOR_DISPATCH_ACCEPTANCE.md**（本文档）

---

## 验收标准

### 1. ✅ 能从 dispatch_log.jsonl 读出 decision-level 模式

**测试：**
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python dispatch_pattern_detector.py
```

**结果：**
```
总记录数：6
```

### 2. ✅ 能输出 Top degraded situations

**输出：**
```
当前最常被降级的输入类型：routine_monitor → degraded
```

**数据验证：**
- routine_monitor 出现 1 次降级
- routine_alert 出现 1 次降级
- critical_alert 出现 1 次降级

### 3. ✅ 能输出 Top rejected handlers

**输出：**
```
当前最常被淘汰的 handler：pattern-detector (原因: 被 aios-health-monitor 替代)
```

**数据验证：**
- pattern-detector 被淘汰 3 次
- agent-performance-analyzer 被淘汰 3 次

### 4. ✅ 能输出 Top policy triggers 和 Top fallback actions

**Policy Triggers：**
```
当前最常触发的 policy 原因：degrade: 匹配规则: 系统降级状态 + 中高风险 → 降级执行 | ...
```

**Fallback Actions：**
```
当前最常走的 fallback 路径：retry_later (→ degraded)
```

**数据验证：**
- degrade policy 触发 3 次
- retry_later fallback 使用 3 次

### 5. ✅ 能给出一句"当前最值得优先优化的中枢路径"

**输出：**
```
当前最值得优先优化的中枢决策模式：
  fallback 路径过于单一：retry_later (→ degraded)（使用 3 次）
```

**判断逻辑：**
- 比较 4 类模式的最高频次
- 识别出 fallback 路径过于单一（3 次）
- 给出明确的优化建议

---

## 4 类决策模式定义

### A. decision_input_pattern（输入降级模式）

**字段：**
- `current_situation` - 当前情境
- `final_status` - 最终状态

**目标：**
找出最常进入 blocked / degraded / failed 的输入类型

**示例输出：**
```json
{
  "type": "decision_input_pattern",
  "top_5": [
    {"pattern": "routine_monitor → degraded", "count": 1},
    {"pattern": "routine_alert → degraded", "count": 1},
    {"pattern": "critical_alert → degraded", "count": 1}
  ]
}
```

### B. handler_rejection_pattern（Handler 淘汰模式）

**字段：**
- `rejected_handlers` - 被淘汰的 handler 列表
- `chosen_handler` - 最终选择的 handler

**目标：**
找出最常被淘汰的 handler，判断是能力不匹配、场景不匹配，还是总被某个更强 handler 压住

**示例输出：**
```json
{
  "type": "handler_rejection_pattern",
  "top_5": [
    {
      "handler": "pattern-detector",
      "count": 3,
      "sample_reasons": [
        {"chosen_instead": "aios-health-monitor", "situation": "routine_monitor"},
        {"chosen_instead": "aios-health-monitor", "situation": "routine_alert"},
        {"chosen_instead": "aios-health-monitor", "situation": "critical_alert"}
      ]
    }
  ]
}
```

### C. policy_pattern（Policy 触发模式）

**字段：**
- `policy_result` - 策略结果（degrade / require_confirmation / reject）
- `policy_reason` - 策略原因

**目标：**
找出最常触发 degrade / require_confirmation / reject 的策略原因

**示例输出：**
```json
{
  "type": "policy_pattern",
  "top_5": [
    {
      "pattern": "degrade: 匹配规则: 系统降级状态 + 中高风险 → 降级执行 | ...",
      "count": 3
    }
  ]
}
```

### D. fallback_pattern（Fallback 路径模式）

**字段：**
- `fallback_action` - fallback 动作
- `final_status` - 最终状态

**目标：**
找出最常走的 fallback 路径，以及哪些 fallback 可能已经变成"默认出口"

**示例输出：**
```json
{
  "type": "fallback_pattern",
  "top_5": [
    {"pattern": "retry_later (→ degraded)", "count": 3}
  ]
}
```

---

## 固定结论句式

```
当前最常被降级的输入类型：<situation> → <status>
当前最常被淘汰的 handler：<handler> (原因: 被 <chosen_handler> 替代)
当前最常触发的 policy 原因：<policy_result>: <policy_reason>
当前最常走的 fallback 路径：<fallback_action> (→ <status>)

当前最值得优先优化的中枢决策模式：
  <一句话判断>
```

---

## 测试结果

### 单元测试

```bash
pytest test_dispatch_pattern_detector.py -v
```

**结果：** ✅ 9/9 通过

```
test_load_dispatch_log PASSED
test_detect_input_degradation_patterns PASSED
test_detect_handler_rejection_patterns PASSED
test_detect_policy_trigger_patterns PASSED
test_detect_fallback_route_patterns PASSED
test_full_analysis PASSED
test_summary_format PASSED
test_optimization_target PASSED
test_empty_log PASSED
```

### 真实数据测试

```bash
python dispatch_pattern_detector.py
```

**结果：** ✅ 成功识别 6 条记录，输出 4 类模式

---

## 当前发现

基于真实数据（6 条记录）的分析结果：

### 1. 中枢现在偏保守

所有 3 条决策记录都走了 `degrade` 策略，说明 policy 第一版确实在起护栏作用，没有乱放行。

### 2. Fallback 过于单一

现在几乎都落到 `retry_later`，这意味着 fallback 机制虽然通了，但还不够丰富。

**建议：**
- 增加更多 fallback 策略（如 escalate、notify、skip）
- 根据不同情境选择不同 fallback

### 3. Handler 分布过窄

当前都指向 `aios-health-monitor`，说明真实事件样本还少，路由分布还没拉开。

**建议：**
- 增加更多真实任务样本
- 观察路由分布是否会随样本增加而变化

---

## 下一步

### P2.5-4：让 lesson-extractor 消费 dispatch patterns + health diagnosis

**目标：**
让 lesson 从"执行事故总结"升级成"中枢决策经验"

**输入：**
- `dispatch_pattern_report.json`（本模块输出）
- `health_diagnosis.json`（health-monitor 输出）

**输出：**
- 结构化 lesson（包含决策层面的经验）

---

## 版本历史

- **v1.0.0** (2026-03-11) - 初始版本，支持 4 类决策模式识别

---

**验收人：** 小九  
**验收日期：** 2026-03-11  
**验收结论：** ✅ 通过
