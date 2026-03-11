# Decide and Dispatch 验收文档

**版本：** v1.0.0  
**日期：** 2026-03-11  
**状态：** ✅ 验收通过

---

## 1. 核心目标

把 task/event/alert/heartbeat 四类输入，统一收进一个入口，走完主链：

```
ingest → route → policy check → dispatch → observe → writeback
```

**核心能力：** 统一编排器，把"选谁做"和"能不能做"串成"怎么真正跑起来并收口"

---

## 2. 交付物清单

### 2.1 核心代码

- ✅ `decide_and_dispatch_schema.py` - 输入输出 schema 定义
- ✅ `decide_and_dispatch.py` - 统一入口编排逻辑
- ✅ `test_decide_and_dispatch.py` - 测试套件（6 个测试用例）
- ✅ `data/dispatch_log.jsonl` - 派发日志（自动生成）

### 2.2 文档

- ✅ `DECIDE_AND_DISPATCH_ACCEPTANCE.md` - 本验收文档

---

## 3. 输入输出定义

### 3.1 标准输入 - TaskContext

```python
{
    "source": str,                      # 来源（task/event/alert/heartbeat）
    "task_type": str,                   # 任务类型
    "content": str,                     # 任务内容
    "priority": str,                    # 优先级
    "risk_level": str,                  # 风险等级
    "system_state": dict,               # 系统状态
    "recent_history": list,             # 最近历史
    "available_handlers": list          # 可用处理器
}
```

### 3.2 标准输出 - DecisionRecord

```python
{
    "current_situation": str,           # 当前情况
    "router_result": dict,              # 路由结果
    "policy_result": dict,              # 策略结果
    "chosen_handler": str | None,       # 选中的处理器
    "execution_plan": ExecutionPlan,    # 执行计划
    "dispatch_result": DispatchResult,  # 派发结果
    "observation": dict,                # 观测数据
    "memory_writeback": dict,           # 记忆回写
    "final_status": str                 # 最终状态
}
```

---

## 4. 完整主链（6 步）

### 1. Ingest - 标准化输入

**作用：** 把 4 类入口统一转成 TaskContext

**第一版：** 直接接收 TaskContext（已标准化）

### 2. Route - 路由决策

**作用：** 调用 skill-router 选择处理器

**输出：**
- situation_type
- candidate_handlers
- chosen_handler
- decision_reason

### 3. Policy Check - 策略检查

**作用：** 调用 policy-decision 做护栏判断

**输出：**
- policy_result（auto_execute/require_confirmation/degrade/reject）
- fallback_action
- policy_reason

### 4. Dispatch - 生成执行计划并派发

**作用：** 根据 router 和 policy 结果生成执行计划

**执行计划字段：**
- handler - 处理器
- mode - 模式（real/simulated/degraded）
- steps - 执行步骤
- fallback - 降级方案
- expected_output - 期望输出

**派发结果字段：**
- status - 状态（dispatched/degraded/blocked/failed）
- handler_used - 实际使用的处理器
- execution_time - 执行时间
- output - 输出
- error - 错误信息
- fallback_triggered - 是否触发降级

### 5. Observe - 观测

**作用：** 收集执行观测数据

**观测字段：**
- task_type
- priority
- risk_level
- router_confidence
- policy_result
- dispatch_status
- execution_time
- fallback_triggered

### 6. Writeback - 记忆回写

**作用：** 统一写回记录供后续消费

**回写内容：**
- 原始输入摘要
- router 决策
- policy 决策
- execution plan
- dispatch result
- failure 原因（如果有）

---

## 5. 四类最终状态

### dispatched（已派发）

**条件：** policy 放行，成功派发

**特征：**
- policy_result = auto_execute
- dispatch_result.status = dispatched
- 无错误

### degraded（已降级）

**条件：** policy 降级，走备用路径

**特征：**
- policy_result = degrade
- dispatch_result.status = degraded
- fallback_triggered = true

### blocked（已拦截）

**条件：** policy 拒绝或要求确认

**特征：**
- policy_result = reject / require_confirmation
- dispatch_result.status = blocked
- 有错误信息

### failed（失败）

**条件：** 无候选处理器或编排失败

**特征：**
- chosen_handler = None
- dispatch_result.status = failed
- 有错误信息

---

## 6. 五句话解释

decide-and-dispatch 必须能回答这 5 句话：

1. **这次输入被识别成什么情况** → `current_situation`
2. **router 选了谁，为什么** → `chosen_handler` + `decision_reason`
3. **policy 是否放行，为什么** → `policy_result` + `policy_reason`
4. **执行计划是什么** → `execution_plan`
5. **结果写回了什么，后续怎么复盘** → `memory_writeback`

**实现方式：** `explain_decision()` 方法

---

## 7. 测试用例（6 个）

### 7.1 普通监控任务

**输入：** monitor + low risk + healthy  
**期望：** router 选 monitor，policy 放行，成功派发  
**结果：** ✅ 通过（dispatched）

### 7.2 高风险修改任务

**输入：** backup + high risk + healthy  
**期望：** router 选 handler，但 policy 要求确认，最终 blocked  
**结果：** ✅ 通过（blocked）

### 7.3 命中已知 timeout 模式

**输入：** analysis + medium risk + known failures  
**期望：** router 正常，policy degrade，最终走降级路径  
**结果：** ✅ 通过（degraded，使用备用处理器）

### 7.4 heartbeat 输入

**输入：** heartbeat + monitor + safe  
**期望：** 统一入口成功转成 task_context，并完成编排  
**结果：** ✅ 通过（blocked，默认策略）

### 7.5 无候选 handler

**输入：** unknown + high risk  
**期望：** router 无可用候选，dispatch 失败但留下可复盘记录  
**结果：** ✅ 通过（failed，有 writeback）

### 7.6 备用 handler 切换

**输入：** analysis + medium risk + degraded system + known failures  
**期望：** 主 handler 不可用，走 fallback 到 backup handler  
**结果：** ✅ 通过（degraded，触发降级）

---

## 8. 验收标准

### 8.1 核心能力

- ✅ 任意输入都能走同一入口
- ✅ 派发前一定经过 router + policy
- ✅ 执行后一定有结果回写
- ✅ 失败时能留下可复盘记录

### 8.2 统一入口

- ✅ 4 类输入（task/event/alert/heartbeat）统一处理
- ✅ 标准化 TaskContext
- ✅ 统一输出 DecisionRecord

### 8.3 完整主链

- ✅ ingest → route → policy check → dispatch → observe → writeback
- ✅ 每一步都有明确输出
- ✅ 失败不断链，有 fallback

### 8.4 可复盘

- ✅ 所有决策记录到 dispatch_log.jsonl
- ✅ memory_writeback 包含完整上下文
- ✅ 失败原因清晰记录

### 8.5 可解释

- ✅ `explain_decision()` 输出 5 句话
- ✅ 每个决策有原因
- ✅ 每个状态有说明

---

## 9. 防跑偏检查

### 9.1 不做的事（已遵守）

- ✅ 不直接接全生产链路 - 第一版模拟派发
- ✅ 不把真实执行做太重 - dispatch 模式清晰（real/simulated/degraded）
- ✅ 不把 writeback 省掉 - 每次都有完整回写
- ✅ 不把 fallback 只写成一句报错 - 有明确降级动作

### 9.2 边界清晰

- skill-router 负责"选谁做"
- policy-decision 负责"能不能做"
- decide-and-dispatch 负责"怎么做"

**三者关系：**
```
decide-and-dispatch 是总入口
  ↓
调用 skill-router（选路）
  ↓
调用 policy-decision（护栏）
  ↓
生成 execution_plan（编排）
  ↓
执行 dispatch（派发）
  ↓
记录 writeback（回写）
```

---

## 10. 第一版限制

### 10.1 派发模式

**第一版只支持：**
- simulated - 模拟派发（默认）
- degraded - 降级派发

**未来支持：**
- real - 真实派发（需要接入 sessions_spawn）

### 10.2 输入来源

**第一版支持：**
- task
- event
- alert
- heartbeat

**统一转换为 TaskContext**

### 10.3 最终状态

**第一版支持：**
- dispatched
- degraded
- blocked
- failed

**清晰定义，便于后续消费**

---

## 11. 下一步集成

### 11.1 接入 heartbeat

在 heartbeat_v5.py 中调用 decide-and-dispatch：

```python
from decide_and_dispatch import DecideAndDispatch

dispatcher = DecideAndDispatch()
decision = dispatcher.process_and_log(task_context)
```

### 11.2 接入 health-monitor

health-monitor 可以消费 dispatch_log.jsonl：

```python
# 读取派发日志
with open('dispatch_log.jsonl') as f:
    for line in f:
        record = json.loads(line)
        # 分析 final_status, execution_time, fallback_triggered
```

### 11.3 接入 pattern-detector

pattern-detector 可以从 memory_writeback 中提取模式：

```python
# 提取失败模式
if record['final_status'] == 'failed':
    failure_reason = record['memory_writeback']['failure_reason']
    # 识别重复模式
```

### 11.4 接入 lesson-extractor

lesson-extractor 可以从 dispatch_log 中提取经验：

```python
# 提取成功/失败经验
if record['final_status'] == 'degraded' and record['dispatch_result']['fallback_triggered']:
    # 这是一次成功的降级，可以沉淀为 lesson
```

---

## 12. P2 完成总结

**P2 统一中枢判定层已完成 3/3：**

1. ✅ Step 1: skill-router（选谁做）
2. ✅ Step 2: policy-decision（能不能做）
3. ✅ Step 3: decide-and-dispatch（怎么做）

**核心成果：**

太极OS 现在具备了完整的中枢判定能力：
- 统一入口（4 类输入）
- 智能路由（选最合适的处理器）
- 安全护栏（风险判断 + 降级策略）
- 执行编排（生成计划 + 派发）
- 完整回写（可复盘 + 可消费）

**下一阶段：**

P2 完成后，太极OS 已经从"工具堆叠期"进入"系统骨架成型期"，现在可以：
- 接入 heartbeat（自动处理任务队列）
- 接入 health-monitor（消费派发日志）
- 接入 pattern-detector（识别失败模式）
- 接入 lesson-extractor（沉淀经验）

**P3 建议方向：**
- 真实派发（接入 sessions_spawn）
- 自动恢复（失败重试 + 自动降级）
- 智能调度（优先级 + 资源管理）

---

## 13. 验收结论

**状态：** ✅ 验收通过

**理由：**
1. 所有交付物齐全
2. 输入输出 schema 已钉死
3. 完整主链（6 步）已串通
4. 4 类最终状态清晰定义
5. 6 个测试用例全部通过
6. 可复盘、可解释、可集成
7. 防跑偏检查通过

**decide-and-dispatch v1.0 可以进入生产集成。**

**P2 统一中枢判定层已全部完成，可以进入下一阶段。**

---

**验收人：** 小九  
**验收时间：** 2026-03-11 08:26
