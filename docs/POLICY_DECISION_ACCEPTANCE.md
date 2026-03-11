# Policy Decision 验收文档

**版本：** v1.0.0  
**日期：** 2026-03-11  
**状态：** ✅ 验收通过

---

## 1. 核心目标

把 policy-decision 做成一个**可解释、可拦截、可降级、可 fallback**的离线策略器。

**核心能力：** 在自动执行前把风险判断、降级策略、fallback 钉死

---

## 2. 交付物清单

### 2.1 核心代码

- ✅ `policy_decision_schema.py` - 输入输出 schema 定义
- ✅ `policy_decision.py` - 策略决策逻辑实现
- ✅ `policy_rules.json` - 8 条策略规则配置
- ✅ `test_policy_decision.py` - 测试套件（6 个测试用例）

### 2.2 文档

- ✅ `POLICY_DECISION_ACCEPTANCE.md` - 本验收文档

---

## 3. 输入输出定义

### 3.1 标准输入 - PolicyInput

```python
{
    "operation_type": str,              # 操作类型
    "handler_type": str,                # 处理器类型（skill/agent）
    "handler_name": str,                # 处理器名称
    "risk_level": str,                  # 风险等级
    "system_health": str,               # 系统健康状态
    "known_failure_patterns": list,     # 已知失败模式
    "user_policy": dict,                # 用户策略
    "router_decision": dict             # 路由决策结果
}
```

### 3.2 标准输出 - PolicyOutput

```python
{
    "policy_result": str,               # 策略结果（auto_execute/require_confirmation/degrade/reject）
    "fallback_action": str | None,      # 降级动作
    "policy_reason": str,               # 策略原因
    "matched_rules": list,              # 匹配的规则
    "risk_summary": dict                # 风险摘要
}
```

---

## 4. 四类策略规则

### A. auto_execute（自动执行）

**条件：** 低风险 + 系统健康 + 无已知高危失败模式

**规则：**
1. `auto_execute_low_risk` - 低风险 + 系统健康 + 无关键失败
2. `auto_execute_monitor` - 监控/分析类任务 + 系统健康

### B. require_confirmation（需要确认）

**条件：** 中高风险，或者涉及破坏性操作、状态变更、不可逆动作

**规则：**
1. `require_confirmation_high_risk` - 中高风险操作
2. `require_confirmation_destructive` - 破坏性操作（backup_restore/code_modify）

### C. degrade（降级执行）

**条件：** 命中已知失败模式，或者当前系统状态不适合全量执行

**规则：**
1. `degrade_known_failure` - 命中已知失败模式
2. `degrade_system_degraded` - 系统降级状态 + 中高风险

### D. reject（拒绝执行）

**条件：** 高风险且无安全 fallback，或者当前系统处于 critical

**规则：**
1. `reject_critical_system` - 系统 critical + 高风险操作
2. `reject_no_fallback` - 高风险且无安全 fallback

---

## 5. 四种 Fallback 动作

1. **retry_later** - 稍后重试
2. **use_backup_handler** - 使用备用处理器
3. **switch_to_readonly** - 切换到只读模式
4. **require_human** - 需要人工介入

---

## 6. 风险评估机制

### 风险评分计算（0-100）

- 风险等级：critical(40) / high(30) / medium(15) / low(0)
- 系统健康：critical(30) / degraded(15) / healthy(0)
- 已知失败模式：每个 +5
- 破坏性操作：+10
- 路由置信度低（<70）：+10

### 风险等级分类

- critical: >= 70
- high: 50-69
- medium: 30-49
- low: < 30

---

## 7. 四句话解释

policy-decision 必须能回答这 4 句话：

1. **这个动作能不能直接做** → `policy_result`
2. **为什么能做 / 不能做** → `policy_reason`
3. **不能直接做时该怎么降级** → `fallback_action`
4. **失败后下一步走哪条 fallback** → `fallback_action`

**实现方式：** `explain_decision()` 方法

---

## 8. 测试用例（6 个）

### 8.1 低风险监控任务

**输入：** monitor + low risk + healthy  
**期望：** auto_execute  
**结果：** ✅ 通过（风险评分 0/100）

### 8.2 高风险修改任务

**输入：** code_modify + high risk + healthy  
**期望：** require_confirmation + require_human  
**结果：** ✅ 通过（风险评分 40/100）

### 8.3 命中 timeout 失败模式

**输入：** analysis + medium risk + known failures  
**期望：** degrade + use_backup_handler  
**结果：** ✅ 通过（风险评分 25/100）

### 8.4 系统 critical + 高风险操作

**输入：** backup_restore + high risk + critical system  
**期望：** reject + require_human  
**结果：** ✅ 通过（风险评分 70/100）

### 8.5 主 handler 不稳定，切备用

**输入：** analysis + medium risk + degraded system + known failures  
**期望：** degrade  
**结果：** ✅ 通过（风险评分 45/100）

### 8.6 无 fallback 的危险动作

**输入：** code_modify + critical risk + no backup  
**期望：** reject + require_human  
**结果：** ✅ 通过（风险评分 50/100）

---

## 9. 验收标准

### 9.1 核心能力

- ✅ 高风险任务不会直接放行
- ✅ 已知失败模式能命中降级策略
- ✅ fallback 有明确下一步，不是简单报错
- ✅ policy 结果可解释、可记录

### 9.2 可解释

- ✅ `explain_decision()` 输出 4 句话
- ✅ 每个决策有 policy_reason
- ✅ 风险摘要包含 risk_score 和 risk_factors

### 9.3 可拦截

- ✅ 高风险操作被拦截（require_confirmation/reject）
- ✅ 系统 critical 时拒绝高风险操作
- ✅ 无 fallback 时拒绝危险动作

### 9.4 可降级

- ✅ 命中已知失败模式时降级
- ✅ 系统降级状态时降级
- ✅ 降级有明确 fallback_action

### 9.5 可 fallback

- ✅ 4 种 fallback 动作清晰定义
- ✅ 每个策略结果有对应 fallback
- ✅ fallback 可序列化记录

---

## 10. 防跑偏检查

### 10.1 不做的事（已遵守）

- ✅ 不把 router 和 policy 混成一个模块 - 边界清晰
- ✅ 不做复杂学习型策略 - 规则简单明确
- ✅ 不提前接入 dispatch 主链 - 当前是离线策略器

### 10.2 边界清晰

- skill-router 负责"选谁做"
- policy-decision 负责"能不能做"
- decide-and-dispatch 负责"怎么做"（下一步）

---

## 11. 规则优先级

规则按优先级排序（数字越大优先级越高）：

1. `auto_execute_low_risk` (10)
2. `auto_execute_monitor` (20)
3. `require_confirmation_high_risk` (30)
4. `require_confirmation_destructive` (40)
5. `degrade_known_failure` (50)
6. `degrade_system_degraded` (60)
7. `reject_critical_system` (70)
8. `reject_no_fallback` (80)

**默认策略：** require_confirmation + require_human

---

## 12. 下一步

**Step 3: decide-and-dispatch**

在 skill-router 和 policy-decision 稳定后，开始实现 decide-and-dispatch：
- 统一入口（ingest → route → policy check → dispatch → observe → writeback）
- 执行编排
- 结果回写

**不要并行开发，先把 policy 用起来。**

---

## 13. 验收结论

**状态：** ✅ 验收通过

**理由：**
1. 所有交付物齐全
2. 输入输出 schema 已钉死
3. 4 类策略规则清晰（auto_execute/require_confirmation/degrade/reject）
4. 4 种 fallback 动作明确
5. 6 个测试用例全部通过
6. 可解释、可拦截、可降级、可 fallback
7. 防跑偏检查通过

**policy-decision v1.0 可以进入下一阶段。**

---

**验收人：** 小九  
**验收时间：** 2026-03-11 08:21
