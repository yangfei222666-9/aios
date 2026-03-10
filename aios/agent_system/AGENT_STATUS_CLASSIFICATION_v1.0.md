# Agent 运营状态分类规范 v1.0

**日期：** 2026-03-10  
**版本：** 1.0  
**维护者：** 小九 + 珊瑚海

---

## 1. 背景

**问题：**
- 不同模块对 Agent 状态的解释不一致
- "未执行"被误解为"故障"
- "零失败"被误解为"稳定运行"
- standby Agent 被误报为"需要关注"

**目标：**
- 统一 Agent 状态语义
- 让所有模块（health report / lifecycle / suggestion generator / diagnostics）使用同一套分类
- 能自动区分"正常待命"和"确实有故障"

---

## 2. 状态分类

### 2.1. active_routable（活跃可路由）

**定义：**
- 正在处理任务或随时可以接收新任务
- 已注册到调度器
- 健康状态良好

**判定条件：**
- enabled: true
- mode: "active"
- production_ready: true
- 最近 24h 有任务执行记录
- 失败率 < 20%

**典型 Agent：**
- coder-dispatcher
- analyst-dispatcher
- monitor-dispatcher

**报告语义：**
- lifecycle: "既济 - 功成身退（稳定运行）"
- health: "GOOD"
- suggestion: 无

---

### 2.2. schedulable_idle（可调度闲置）

**定义：**
- 已注册到调度器，但当前没有任务
- 可以随时接收新任务
- 不是故障，只是暂时空闲

**判定条件：**
- enabled: true
- mode: "active"
- production_ready: true
- 最近 24h 无任务执行记录
- 但有历史执行记录（tasks_total > 0）

**典型 Agent：**
- 定时任务 Agent（非触发时段）
- 低频 Agent（每周一次）

**报告语义：**
- lifecycle: "屯 - 蓄势待发（闲置中）"
- health: "IDLE"
- suggestion: 无（正常闲置）

---

### 2.3. standby_emergency（应急待命）

**定义：**
- 应急响应型 Agent
- 只在特定条件触发（如失败数量增加）
- 未触发时处于待命状态

**判定条件：**
- enabled: true
- mode: "active"
- production_ready: false
- tasks_total == 0（从未执行）
- 有明确的条件触发逻辑

**典型 Agent：**
- Bug_Hunter（失败数量增加 ≥3 时触发）
- Error_Analyzer（unknown 错误 ≥3 时触发）

**报告语义：**
- lifecycle: "坎 - 险中求进（待命中）"
- health: "STANDBY"
- suggestion: 无（按设计待命）

**关键：**
- 不生成"建议激活"类文案
- 不误报为"24h 未运行，需要关注"

---

### 2.4. shadow（影子模式）

**定义：**
- 已定义但未启用
- 可能在观察期、测试期或保留状态
- 不参与生产任务

**判定条件：**
- enabled: false 或 true
- mode: "shadow"
- production_ready: false

**典型 Agent：**
- GitHub_Deep_Analyzer
- Competitor_Tracker
- Idea_Generator

**报告语义：**
- lifecycle: "蒙 - 启蒙待发（影子模式）"
- health: "SHADOW"
- suggestion: 无（按设计保留）

---

### 2.5. disabled（已禁用）

**定义：**
- 明确禁用的 Agent
- 不参与任何调度
- 可能是低优先级或已废弃

**判定条件：**
- enabled: false
- mode: "disabled"
- priority: "disabled" 或 "low"

**典型 Agent：**
- Community_Manager
- Marketing_Writer
- Integration_Tester

**报告语义：**
- lifecycle: "剥 - 剥落退场（已禁用）"
- health: "DISABLED"
- suggestion: 无（按设计禁用）

---

### 2.6. degraded（降级运行）

**定义：**
- 正在运行但性能下降
- 失败率高或超时频繁
- 需要关注和修复

**判定条件：**
- enabled: true
- mode: "active"
- production_ready: true
- 失败率 ≥ 20% 或连续失败 ≥ 3 次

**典型 Agent：**
- 任何出现性能问题的 Agent

**报告语义：**
- lifecycle: "困 - 困境求变（降级运行）"
- health: "DEGRADED"
- suggestion: "检查失败原因，考虑调整超时或拆分任务"

---

## 3. 状态转换规则

```
disabled → shadow → standby_emergency → schedulable_idle → active_routable
                                                                    ↓
                                                                degraded
```

**转换条件：**
- disabled → shadow: enabled: true, mode: "shadow"
- shadow → standby_emergency: production_ready: false, 有条件触发逻辑
- standby_emergency → schedulable_idle: 触发条件满足，开始执行任务
- schedulable_idle → active_routable: 最近 24h 有任务执行
- active_routable → degraded: 失败率 ≥ 20%
- degraded → active_routable: 失败率 < 20%

---

## 4. 应用场景

### 4.1. health_report.py

**修改前：**
```python
if tasks_total == 0:
    status = "IDLE"
    suggestion = "建议激活"
```

**修改后：**
```python
if agent_type == "standby_emergency":
    status = "STANDBY"
    suggestion = None  # 不生成建议
elif tasks_total == 0:
    status = "IDLE"
    suggestion = "检查是否需要激活"
```

### 4.2. lifecycle_engine.py

**修改前：**
```python
if failure_rate == 0.0:
    stage = "既济 - 功成身退（稳定运行）"
```

**修改后：**
```python
if agent_type == "standby_emergency" and tasks_total == 0:
    stage = "坎 - 险中求进（待命中）"
elif failure_rate == 0.0 and tasks_total > 0:
    stage = "既济 - 功成身退（稳定运行）"
elif tasks_total == 0:
    stage = "屯 - 蓄势待发（闲置中）"
```

### 4.3. suggestion_generator.py

**修改前：**
```python
if tasks_total == 0:
    suggestions.append("建议激活 Agent")
```

**修改后：**
```python
if agent_type == "standby_emergency":
    pass  # 不生成建议
elif agent_type == "disabled":
    pass  # 不生成建议
elif tasks_total == 0:
    suggestions.append("检查是否需要激活")
```

### 4.4. diagnostics.py

**修改前：**
```python
if tasks_total == 0:
    diagnosis = "Agent 未运行，可能有故障"
```

**修改后：**
```python
if agent_type == "standby_emergency":
    diagnosis = "应急待命中，触发条件未满足"
elif agent_type == "shadow":
    diagnosis = "影子模式，按设计保留"
elif agent_type == "disabled":
    diagnosis = "已禁用，按设计停用"
elif tasks_total == 0:
    diagnosis = "闲置中，可能需要激活"
```

---

## 5. 实施步骤

### Phase 1: 定义分类（已完成）
- ✅ 定义 6 种状态分类
- ✅ 明确判定条件
- ✅ 确定报告语义

### Phase 2: 更新 agents.json
- 为每个 Agent 增加 `agent_type` 字段
- 标记 Bug_Hunter 为 "standby_emergency"
- 标记 disabled Agent 为 "disabled"

### Phase 3: 更新核心模块
- health_report.py
- lifecycle_engine.py
- suggestion_generator.py
- diagnostics.py

### Phase 4: 验证
- 运行 health report，确认 Bug_Hunter 不再误报
- 运行 lifecycle check，确认状态语义正确
- 运行 diagnostics，确认能区分"正常待命"和"确实有故障"

---

## 6. 验收标准

**必须满足：**
1. Bug_Hunter 不再被误报为"需要关注"
2. lifecycle 不再把"零失败"误解为"稳定运行"
3. suggestion generator 不再对 standby Agent 生成"建议激活"
4. diagnostics 能自动区分"正常待命"和"确实有故障"

**测试用例：**
- Bug_Hunter（standby_emergency）→ 状态："待命中"，建议：无
- coder-dispatcher（active_routable）→ 状态："稳定运行"，建议：无
- GitHub_Deep_Analyzer（shadow）→ 状态："影子模式"，建议：无
- Community_Manager（disabled）→ 状态："已禁用"，建议：无

---

## 7. 未来扩展

### 7.1. 自动分类

**目标：** 根据 Agent 的配置和历史行为，自动推断 agent_type。

**规则：**
- 如果 enabled: false → disabled
- 如果 mode: "shadow" → shadow
- 如果有条件触发逻辑且 tasks_total == 0 → standby_emergency
- 如果 tasks_total > 0 且最近 24h 有执行 → active_routable
- 如果 tasks_total > 0 且最近 24h 无执行 → schedulable_idle
- 如果失败率 ≥ 20% → degraded

### 7.2. 状态可视化

**目标：** 在 Dashboard 中用不同颜色标记不同状态。

**颜色方案：**
- active_routable: 绿色
- schedulable_idle: 蓝色
- standby_emergency: 黄色
- shadow: 灰色
- disabled: 黑色
- degraded: 红色

---

**规范版本：** v1.0  
**生效日期：** 2026-03-10  
**下次审查：** 2026-04-10
