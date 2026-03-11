# 太极OS 实时发现与处置闭环 v0.1

**状态：** draft / review-pending  
**版本：** v0.1  
**日期：** 2026-03-12  
**作者：** 小九 + 珊瑚海

---

## 1. 目标与边界

### 目标

让太极OS具备最小实时值班能力：

- ✅ 能持续接收信号
- ✅ 能识别 5 类异常
- ✅ 能做 4 类低风险动作
- ✅ 能验证动作是否有效
- ✅ 能沉淀 1 条 lesson → rule

### 非目标

- ❌ 不做高风险自动修复
- ❌ 不接入 GUI 自动动作主线
- ❌ 不扩新 Agent
- ❌ 不做大而全根因分析平台

### 核心定位

v0.1 是太极OS从"定期检查"升级为"实时值班"的最小闭环。

不追求完美，只追求能跑、能验、能学。

---

## 2. v0.1 执行顺序

### Step 1：Heartbeat 升级为事件入口

**目标：** 输入原始信号，输出标准事件

**改动：**
- `heartbeat_v5.py` 增加事件输出函数
- 所有检查结果统一输出为标准事件
- 写入 `data/events.jsonl`

**验收：**
- Heartbeat 每次运行输出至少 1 个事件
- 事件符合最小 Schema
- 事件可追溯到原始证据

---

### Step 2：落 5 个检测器

**目标：** 只做最值钱的实时检测

**5 个检测器：**
1. `missing_heartbeat` - Heartbeat 超时未运行
2. `repeated_failure` - Agent 连续失败 3 次
3. `service_down` - Memory Server / Dashboard 不可达
4. `queue_stall` - 队列积压超过阈值
5. `missing_audit` - 关键动作缺失审计记录

**验收：**
- 每个检测器至少触发/验证 1 次
- 每次触发输出标准事件
- 有明确的抑制条件（避免告警风暴）

---

### Step 3：开放 4 类低风险动作

**目标：** 动作必须有边界、有审计、有验证

**4 类动作：**
1. `retry_once` - 单次重试
2. `health_probe` - 健康探测
3. `set_observation_or_quarantine` - 设置观察/隔离状态
4. `create_repair_task` - 创建修复任务（不自动执行）

**硬约束：**
- 默认只允许这 4 类
- 任何新动作不进 v0.1
- 每个动作都必须有验证步骤
- 动作失败必须可回退到"只记录/只告警"

**验收：**
- 4 类动作至少各有 1 次真实或受控验证
- 每次动作都有 event_id、evidence、verification result
- 无越权高风险自动动作

---

### Step 4：打通 1 条 lesson → rule

**目标：** 完成最小学习闭环

**样本选择：**

```
连续失败 3 次 
→ repeated_failure 
→ set_observation_or_quarantine 
→ 验证成功率恢复情况 
→ 生成 rule
```

**为什么选这条：**
- 有信号（连续失败）
- 有阈值（3 次）
- 有低风险动作（隔离观察）
- 有清晰验证（成功率恢复）

**验收：**
- 至少打通 1 条 lesson → rule
- rule 写回 `memory/lessons.json`
- rule 可被后续检测器引用

---

## 3. 最小事件 Schema

### 核心字段

```json
{
  "event_id": "evt-20260312-001",
  "timestamp": "2026-03-12T00:30:00+08:00",
  "source": "heartbeat_v5",
  "entity_type": "agent",
  "entity_id": "coder-dispatcher",
  "event_type": "repeated_failure",
  "severity": "warning",
  "status": "detected",
  "summary": "coder-dispatcher 连续失败 3 次",
  "evidence": {
    "failure_count": 3,
    "last_error": "timeout",
    "time_window": "1h"
  },
  "suggested_action": "set_observation_or_quarantine",
  "cooldown_key": "agent:coder-dispatcher:repeated_failure",
  "requires_verification": true,
  "trace_id": "trace-001"
}
```

### 三个硬约束

1. **所有事件必须可追溯到原始证据**
   - `evidence` 字段必填
   - 必须包含足够信息用于复现判断

2. **所有事件必须能映射到 severity**
   - `info` - 信息性事件
   - `warning` - 需要关注
   - `error` - 需要处理
   - `critical` - 需要立即处理

3. **所有自动动作必须回写到对应 event_id**
   - 动作执行后更新 `status`
   - 记录 `action_taken` 和 `verification_result`

---

## 4. 5 个检测器定义

### 4.1 missing_heartbeat

**输入信号：**
- 上次 Heartbeat 时间戳
- 当前时间

**触发条件：**
- 超过 7 小时未运行

**严重级别：**
- `warning` (7-12h)
- `error` (12-24h)
- `critical` (>24h)

**抑制条件：**
- 同一 cooldown_key 6 小时内只触发 1 次

**最小动作建议：**
- `health_probe` - 检查 OpenClaw 主进程状态

**验证标准：**
- Heartbeat 恢复运行
- 时间间隔回到正常范围（<7h）

---

### 4.2 repeated_failure

**输入信号：**
- Agent 执行记录
- 失败次数统计

**触发条件：**
- 连续失败 3 次（1 小时内）

**严重级别：**
- `warning` (3 次)
- `error` (5 次)
- `critical` (10 次)

**抑制条件：**
- 同一 Agent 6 小时内只触发 1 次

**最小动作建议：**
- `set_observation_or_quarantine` - 设置观察状态

**验证标准：**
- 成功率恢复到 >70%
- 或进入隔离状态，不再影响主链路

---

### 4.3 service_down

**输入信号：**
- Memory Server 健康检查
- Dashboard 健康检查

**触发条件：**
- HTTP 请求失败或超时

**严重级别：**
- `warning` (1 次失败)
- `error` (连续 3 次失败)
- `critical` (>10 分钟不可达)

**抑制条件：**
- 同一服务 10 分钟内只触发 1 次

**最小动作建议：**
- `health_probe` - 尝试重新连接
- `create_repair_task` - 创建重启任务

**验证标准：**
- 服务恢复可达
- 健康检查返回 200

---

### 4.4 queue_stall

**输入信号：**
- 队列长度
- 最老任务等待时间

**触发条件：**
- 队列长度 >10
- 或最老任务等待 >1 小时

**严重级别：**
- `warning` (>10 tasks or >1h)
- `error` (>20 tasks or >3h)
- `critical` (>50 tasks or >6h)

**抑制条件：**
- 1 小时内只触发 1 次

**最小动作建议：**
- `health_probe` - 检查 Agent 状态
- `create_repair_task` - 创建清理任务

**验证标准：**
- 队列长度下降
- 最老任务被处理

---

### 4.5 missing_audit

**输入信号：**
- 关键动作执行记录
- 审计日志

**触发条件：**
- 关键动作（文件修改、外部调用）缺失审计记录

**严重级别：**
- `error` (单次缺失)
- `critical` (多次缺失)

**抑制条件：**
- 同一动作类型 1 小时内只触发 1 次

**最小动作建议：**
- `create_repair_task` - 补充审计记录

**验证标准：**
- 审计记录完整
- 可追溯到原始动作

---

## 5. 4 类低风险动作

### 5.1 retry_once

**定义：** 单次重试失败的操作

**适用场景：**
- 网络超时
- 临时资源不可用

**执行步骤：**
1. 记录重试事件
2. 执行原操作
3. 记录结果
4. 更新事件状态

**验证：**
- 操作成功 → `status: resolved`
- 操作失败 → `status: failed, action: escalate`

**回退：**
- 失败后不再重试，只记录

---

### 5.2 health_probe

**定义：** 探测服务/Agent 健康状态

**适用场景：**
- 服务不可达
- Agent 状态未知

**执行步骤：**
1. 发送健康检查请求
2. 记录响应时间和状态码
3. 更新服务状态
4. 记录探测结果

**验证：**
- 服务可达 → `status: healthy`
- 服务不可达 → `status: unhealthy, action: escalate`

**回退：**
- 探测失败不影响原服务，只记录

---

### 5.3 set_observation_or_quarantine

**定义：** 设置 Agent/Skill 为观察或隔离状态

**适用场景：**
- 连续失败
- 成功率低于阈值

**执行步骤：**
1. 更新 Agent 状态为 `observation` 或 `quarantined`
2. 记录状态变更事件
3. 设置观察期（默认 24h）
4. 记录观察指标

**验证：**
- 观察期内成功率恢复 → `status: production-ready`
- 观察期内持续失败 → `status: quarantined`

**回退：**
- 可手动恢复为 `production-ready`

---

### 5.4 create_repair_task

**定义：** 创建修复任务，不自动执行

**适用场景：**
- 需要人工介入
- 高风险操作

**执行步骤：**
1. 创建任务记录
2. 写入 `task_queue.jsonl`
3. 设置优先级和描述
4. 通知用户

**验证：**
- 任务创建成功 → `status: task_created`
- 任务被执行 → `status: resolved`

**回退：**
- 任务可删除或标记为 `cancelled`

---

## 6. 验证器

### 验证步骤

每次动作后必须回答：

1. **状态恢复了吗？**
   - 检查 Agent/Service 状态
   - 对比动作前后指标

2. **指标改善了吗？**
   - 成功率
   - 响应时间
   - 队列长度

3. **有没有副作用？**
   - 是否影响其他 Agent
   - 是否产生新的错误

4. **要不要回滚？**
   - 如果副作用严重，立即回滚
   - 记录回滚原因

5. **要不要进入冷却？**
   - 如果动作无效，进入冷却期
   - 避免重复无效动作

### 验证记录格式

```json
{
  "event_id": "evt-20260312-001",
  "action_taken": "set_observation_or_quarantine",
  "verification_result": {
    "status_recovered": true,
    "metrics_improved": true,
    "side_effects": false,
    "rollback_needed": false,
    "cooldown_needed": false
  },
  "verification_timestamp": "2026-03-12T01:00:00+08:00"
}
```

---

## 7. 1 条 lesson → rule

### 样本选择

**场景：** Agent 连续失败 3 次

**完整流程：**

```
1. 检测器触发
   repeated_failure 检测到 coder-dispatcher 连续失败 3 次

2. 输出事件
   event_type: repeated_failure
   severity: warning
   suggested_action: set_observation_or_quarantine

3. 执行动作
   set_observation_or_quarantine(agent_id="coder-dispatcher")

4. 验证结果
   观察期 24h，成功率从 0% 恢复到 80%

5. 生成 lesson
   {
     "lesson_id": "lesson-001",
     "pattern": "repeated_failure",
     "context": "coder-dispatcher 连续失败 3 次",
     "action": "set_observation_or_quarantine",
     "outcome": "success",
     "metrics": {
       "success_rate_before": 0.0,
       "success_rate_after": 0.8
     }
   }

6. 提炼 rule
   {
     "rule_id": "rule-001",
     "condition": "agent.consecutive_failures >= 3",
     "action": "set_observation_or_quarantine",
     "cooldown": "6h",
     "confidence": 0.9
   }

7. 写回 lessons.json
   rule 进入 rules_derived 区域

8. 后续检测器引用
   repeated_failure 检测器自动应用 rule-001
```

### 为什么选这条

- ✅ 有信号（连续失败）
- ✅ 有阈值（3 次）
- ✅ 有低风险动作（隔离观察）
- ✅ 有清晰验证（成功率恢复）
- ✅ 容易复现和测试

---

## 8. 验收标准

### 最小验收（6 项）

1. ✅ **Heartbeat 能输出标准事件**
   - 每次运行输出至少 1 个事件
   - 事件符合最小 Schema
   - 写入 `data/events.jsonl`

2. ✅ **5 个检测器至少各触发/验证 1 次**
   - missing_heartbeat
   - repeated_failure
   - service_down
   - queue_stall
   - missing_audit

3. ✅ **4 类动作至少各有 1 次真实或受控验证**
   - retry_once
   - health_probe
   - set_observation_or_quarantine
   - create_repair_task

4. ✅ **每次动作都有 event_id、evidence、verification result**
   - 可追溯
   - 可验证
   - 可复现

5. ✅ **至少打通 1 条 lesson → rule**
   - lesson 记录完整
   - rule 写回 lessons.json
   - rule 可被后续检测器引用

6. ✅ **全程无越权高风险自动动作**
   - 无文件删除
   - 无外部写入
   - 无高权限执行

---

## 9. 实施路径

### Phase 1：事件基础设施（1-2 天）

- [ ] 定义事件 Schema
- [ ] 实现事件写入函数
- [ ] Heartbeat 升级为事件入口
- [ ] 验证事件可追溯

### Phase 2：检测器实现（2-3 天）

- [ ] 实现 5 个检测器
- [ ] 每个检测器至少触发 1 次
- [ ] 验证抑制条件有效

### Phase 3：动作执行器（2-3 天）

- [ ] 实现 4 类动作
- [ ] 每类动作至少验证 1 次
- [ ] 验证回退机制有效

### Phase 4：验证与学习（1-2 天）

- [ ] 实现验证器
- [ ] 打通 1 条 lesson → rule
- [ ] 验证 rule 可被引用

### Phase 5：集成测试（1 天）

- [ ] 完整流程测试
- [ ] 验收标准检查
- [ ] 文档更新

**总计：** 7-11 天

---

## 10. 风险与约束

### 风险

1. **事件风暴** - 检测器触发过于频繁
   - 缓解：抑制条件 + cooldown_key

2. **动作冲突** - 多个动作同时作用于同一实体
   - 缓解：动作互斥锁 + 优先级

3. **验证失败** - 动作执行后状态未恢复
   - 缓解：回退机制 + 冷却期

### 约束

1. **只做低风险动作** - 不做文件删除、外部写入、高权限执行
2. **默认不自动应用** - 高风险动作只创建任务，不自动执行
3. **可追溯** - 所有事件和动作必须可追溯
4. **可回退** - 所有动作必须可回退

---

## 附录 A：今日 GitHub 学习启发

### Hive Agent

**核心启发：**
- 统一事件总线（Event Bus）
- 标准化事件 Schema
- 事件驱动的 Agent 协作

**对太极OS 的价值：**
- 事件 Schema 设计参考
- 事件总线架构参考
- Agent 间通信模式参考

### Agents

**核心启发：**
- 分层检测器设计
- 动作执行器与验证器分离
- 学习闭环设计

**对太极OS 的价值：**
- 检测器分层参考
- 验证器设计参考
- 学习闭环参考

### DeerFlow

**核心启发：**
- 轻量级事件记录
- 最小化动作集
- 快速验证反馈

**对太极OS 的价值：**
- 事件记录简化参考
- 动作集设计参考
- 验证反馈机制参考

---

## 附录 B：Top 5 可执行改进建议

1. **统一事件 Schema** - 所有检测器输出标准事件
2. **分层检测器** - 按严重级别分层，避免告警风暴
3. **动作验证器** - 每次动作后必须验证
4. **学习闭环** - 至少打通 1 条 lesson → rule
5. **抑制机制** - cooldown_key 避免重复告警

---

## 附录 C：与太极OS现状映射表

| 能力 | 当前状态 | v0.1 目标 | 差距 |
|------|---------|----------|------|
| 事件记录 | 分散在各模块 | 统一事件总线 | 需要统一 Schema |
| 检测器 | Heartbeat 内置 | 5 个独立检测器 | 需要拆分和标准化 |
| 动作执行 | 部分自动化 | 4 类低风险动作 | 需要边界和验证 |
| 验证机制 | 部分模块有 | 统一验证器 | 需要标准化 |
| 学习闭环 | lesson 系统存在 | 1 条 lesson → rule | 需要打通 |

---

## 结语

v0.1 的核心不是"做得多完美"，而是"能跑、能验、能学"。

先把这条最小闭环立起来，再逐步扩展。

**一句话总结：**

> 太极OS v0.1 实时发现与处置闭环 = 统一事件 + 5 个检测器 + 4 类动作 + 验证器 + 1 条学习闭环

---

**下一步：**
- 珊瑚海 review
- 确认执行顺序
- 开始 Phase 1 实施
