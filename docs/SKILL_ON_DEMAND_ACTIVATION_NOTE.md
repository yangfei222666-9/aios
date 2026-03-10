# Skill 按需激活机制 - 设计说明

**文档类型：** 研究附录 / 设计探索  
**状态：** design-only（不改 v1.1 冻结基线）  
**创建时间：** 2026-03-09  
**输入来源：** learn-claude-code 两层加载机制启发  
**目标版本：** 为 Skill Auto-Creation v1.2 提供输入

---

## 1. 目标

**核心问题：**
随着 Skill 数量增加，如果所有 Skill 都在启动时加载到 system prompt，会导致：
- Token 消耗爆炸
- 上下文污染
- 无关 Skill 干扰决策

**解决方案：**
设计一个"按需激活"机制，让 Skill 在需要时才被看见、展开、执行。

**关键原则：**
- 不是所有 Skill 都需要被看见
- 不是所有被看见的 Skill 都需要被展开
- 不是所有被展开的 Skill 都需要被执行

---

## 2. 边界声明

**本文档是 design-only 的研究附录，不改写已冻结的 v1.1 正式规格书。**

**与 Skill Auto-Creation MVP v1.1 的关系：**
- v1.1 专注于"如何生成 Skill"
- 本文档专注于"如何激活 Skill"
- 两者是互补关系，不是替代关系

**进入 v1.2 的条件：**
- v1.1 观察期通过
- 本设计说明经过验证
- 有真实数据支持按需激活的价值

---

## 3. 按需激活的核心定义

**按需激活 = 分层可见性 + 触发条件 + 结果回写**

### 3.1 分层可见性

借鉴 learn-claude-code 的两层加载机制，扩展为三层：

**Level 0: Metadata（元数据层）**
- 内容：Skill 名称、描述、触发信号、优先级
- 大小：~50 tokens/skill
- 何时加载：启动时全部加载
- 作用：让系统知道"有哪些 Skill 存在"

**Level 1: Summary（摘要层）**
- 内容：Skill 的核心能力、输入输出、使用场景
- 大小：~200 tokens/skill
- 何时加载：触发条件满足时
- 作用：让 Agent 判断"这个 Skill 是否适用"

**Level 2: Full Content（完整内容层）**
- 内容：完整的 SKILL.md 内容（步骤、示例、注意事项）
- 大小：~2000 tokens/skill
- 何时加载：Agent 决定执行时
- 作用：提供完整的执行指导

### 3.2 激活流程

```
启动时：加载所有 Level 0 metadata
  ↓
每次任务开始：根据触发条件筛选候选 Skill
  ↓
候选 Skill：加载 Level 1 summary
  ↓
Agent 判断：是否需要执行
  ↓
需要执行：加载 Level 2 full content
  ↓
执行完成：只返回结果摘要，不保留完整过程
```

---

## 4. 两层/三层加载如何工作

### 4.1 Level 0 → Level 1 触发条件

**输入信号：**
- 当前任务类型（code / analysis / monitor / fix）
- 最近消息摘要（关键词提取）
- 系统状态（是否有告警、错误、异常）
- 可用工具（当前 Agent 有哪些工具）
- 目标模式（是否在特定模式下，如"调试模式"）

**触发规则示例：**

```python
# heartbeat_alert_deduper Skill
activation_signals = [
    "alert",
    "告警",
    "重复",
    "去重",
    "heartbeat",
]

negative_conditions = [
    "no_alerts_file",  # alerts.jsonl 不存在
    "alerts_empty",    # alerts.jsonl 为空
]

priority_score = 80  # 0-100，越高越优先

required_context_keys = [
    "alerts_file_path",
    "notifier_module",
]
```

**触发逻辑：**

```python
def should_activate_level1(skill, context):
    # 1. 检查负面条件
    for neg in skill.negative_conditions:
        if context.get(neg):
            return False
    
    # 2. 检查激活信号
    message_text = context.get("recent_messages", "")
    for signal in skill.activation_signals:
        if signal in message_text.lower():
            return True
    
    # 3. 检查系统状态
    if context.get("has_alerts") and "alert" in skill.activation_signals:
        return True
    
    return False
```

### 4.2 Level 1 → Level 2 触发条件

**由 Agent 决定，但有规则辅助：**

```python
def should_activate_level2(skill, context, agent_intent):
    # 1. Agent 明确表示要使用这个 Skill
    if agent_intent.get("use_skill") == skill.name:
        return True
    
    # 2. Agent 的任务与 Skill 的能力高度匹配
    if skill.match_score(agent_intent) > 0.8:
        return True
    
    # 3. 当前任务失败，且 Skill 可能解决问题
    if context.get("task_failed") and skill.can_fix(context.get("error")):
        return True
    
    return False
```

### 4.3 实现示例

```python
class SkillActivationManager:
    def __init__(self, skills_dir):
        self.skills = self._load_all_level0(skills_dir)
    
    def get_active_skills(self, context):
        """返回当前应该激活的 Skill（Level 1）"""
        active = []
        for skill in self.skills.values():
            if self._should_activate_level1(skill, context):
                active.append({
                    "name": skill.name,
                    "summary": skill.level1_summary,
                    "priority": skill.priority_score,
                })
        return sorted(active, key=lambda x: x["priority"], reverse=True)
    
    def load_full_skill(self, skill_name):
        """加载完整的 Skill 内容（Level 2）"""
        skill = self.skills.get(skill_name)
        if not skill:
            return None
        return skill.level2_full_content
```

---

## 5. 激活判断输入

### 5.1 上下文信号

**任务相关：**
- `task_type`: code / analysis / monitor / fix / deploy
- `task_description`: 任务描述文本
- `task_priority`: high / normal / low

**系统状态：**
- `has_alerts`: 是否有未处理告警
- `has_errors`: 是否有错误日志
- `system_health`: 系统健康度（0-100）
- `recent_failures`: 最近失败的任务列表

**消息上下文：**
- `recent_messages`: 最近 5 条消息的文本
- `keywords`: 提取的关键词列表
- `intent`: 用户意图（如果能识别）

**工具可用性：**
- `available_tools`: 当前 Agent 可用的工具列表
- `required_tools`: Skill 需要的工具列表

### 5.2 谁来做激活判断

**第一版建议：规则优先，LLM 辅助**

```
规则引擎（70%）
  ↓
  判断是否满足激活条件
  ↓
  是 → 激活
  否 → 进入 LLM 辅助判断
  ↓
LLM 辅助（30%）
  ↓
  "这个 Skill 是否适用于当前任务？"
  ↓
  是 → 激活
  否 → 不激活
```

**为什么规则优先？**
- 规则快、便宜、可预测
- LLM 慢、贵、可能不稳定
- 规则可以覆盖 70% 的常见场景

**什么时候用 LLM？**
- 规则无法判断（边界模糊）
- 需要理解复杂上下文
- 需要推理因果关系

---

## 6. 激活结果如何回写

### 6.1 避免上下文污染

**核心原则：只返回结果摘要，不保留完整过程**

借鉴 learn-claude-code 的子代理机制：

```python
def execute_skill_isolated(skill_name, context):
    """在独立上下文中执行 Skill"""
    # 1. 创建子代理
    sub_agent = SubAgent(
        messages=[],  # 独立的 messages[]
        tools=skill.required_tools,
        system_prompt=skill.level2_full_content,
    )
    
    # 2. 执行任务
    result = sub_agent.run(context.get("task_description"))
    
    # 3. 只返回摘要
    summary = result.get_summary()  # 不超过 500 tokens
    
    # 4. 丢弃子代理的完整上下文
    del sub_agent
    
    return summary
```

### 6.2 回写内容

**返回给父 Agent 的内容：**

```json
{
  "skill_name": "heartbeat_alert_deduper",
  "status": "success",
  "summary": "已去重 3 条告警，保留 1 条新告警",
  "result": {
    "alerts_processed": 3,
    "alerts_sent": 1,
    "alerts_suppressed": 2
  },
  "execution_time": 2.3,
  "token_used": 450
}
```

**不返回的内容：**
- 完整的执行日志
- 中间步骤的详细输出
- 子代理的完整 messages[]

---

## 7. 如何留下激活证据

### 7.1 激活日志

**记录到 `skill_activation.jsonl`：**

```json
{
  "timestamp": "2026-03-09T11:20:00Z",
  "skill_name": "heartbeat_alert_deduper",
  "activation_level": "level2",
  "trigger_reason": "has_alerts=true, keyword='alert' in recent_messages",
  "context": {
    "task_type": "monitor",
    "has_alerts": true,
    "recent_messages": "Check alerts.jsonl for unsent alerts"
  },
  "result": {
    "status": "success",
    "summary": "已去重 3 条告警",
    "token_used": 450
  }
}
```

### 7.2 激活统计

**记录到 `skill_activation_stats.json`：**

```json
{
  "heartbeat_alert_deduper": {
    "total_activations": 15,
    "level1_activations": 20,  // 被考虑了 20 次
    "level2_activations": 15,  // 实际执行了 15 次
    "success_count": 14,
    "failure_count": 1,
    "avg_token_used": 420,
    "avg_execution_time": 2.1,
    "last_activated": "2026-03-09T11:20:00Z"
  }
}
```

### 7.3 上下文污染检测

**记录哪些 Skill 被激活了但没有贡献：**

```json
{
  "timestamp": "2026-03-09T11:20:00Z",
  "skill_name": "log_analyzer",
  "activation_level": "level1",
  "trigger_reason": "keyword='log' in recent_messages",
  "result": {
    "status": "not_used",
    "reason": "Agent 判断不适用",
    "token_wasted": 200
  }
}
```

**这是未来 Context Rot Awareness 的前置数据。**

---

## 8. 与 Skill Auto-Creation v1.1 的关系

### 8.1 v1.1 专注于"生成"

**v1.1 的核心流程：**

```
发现候选 → 生成草案 → 验证 → 隔离注册 → 试运行反馈
```

**v1.1 不涉及"激活"：**
- v1.1 只负责生成 Skill
- 生成的 Skill 进入 draft registry
- 如何激活这些 Skill，不在 v1.1 范围内

### 8.2 本设计说明专注于"激活"

**本设计说明的核心流程：**

```
加载 metadata → 触发条件判断 → 加载 summary → Agent 判断 → 加载 full content → 执行 → 回写摘要
```

**本设计说明不涉及"生成"：**
- 假设 Skill 已经存在（无论是手动创建还是自动生成）
- 只关心如何按需激活这些 Skill

### 8.3 两者的结合点

**v1.1 生成的 Skill 应该包含激活元数据：**

在 `skill_drafter.py` 中增加 `generate_trigger()` 函数：

```python
def generate_trigger(candidate_pattern):
    """从候选模式中提取触发条件"""
    return {
        "activation_signals": extract_keywords(candidate_pattern),
        "negative_conditions": extract_negative_conditions(candidate_pattern),
        "priority_score": calculate_priority(candidate_pattern),
        "required_context_keys": extract_required_context(candidate_pattern),
    }
```

**生成的 Skill 包含 `skill_trigger.py`：**

```python
# skills/heartbeat_alert_deduper/skill_trigger.py

activation_signals = [
    "alert",
    "告警",
    "重复",
    "去重",
    "heartbeat",
]

negative_conditions = [
    "no_alerts_file",
    "alerts_empty",
]

priority_score = 80

required_context_keys = [
    "alerts_file_path",
    "notifier_module",
]

def should_activate(context):
    """判断是否应该激活这个 Skill"""
    # 检查负面条件
    if context.get("no_alerts_file") or context.get("alerts_empty"):
        return False
    
    # 检查激活信号
    message_text = context.get("recent_messages", "")
    for signal in activation_signals:
        if signal in message_text.lower():
            return True
    
    return False
```

---

## 9. 后续进入 v1.2 的条件

### 9.1 观察期验证

**需要验证的问题：**
1. 按需激活是否真的减少了 token 消耗？
2. 按需激活是否真的提高了决策准确性？
3. 按需激活是否引入了新的复杂度？
4. 激活判断的准确率是多少？
5. 有多少 Skill 被激活了但没有贡献？

**验证方式：**
- 在 v1.1 观察期内，同时记录"全量加载"和"按需激活"的数据
- 对比两种方式的 token 消耗、执行时间、成功率
- 分析激活日志，找出误激活和漏激活的案例

### 9.2 进入 v1.2 的标准

**必须满足以下条件：**
1. v1.1 观察期通过（Skill 自动生成机制稳定）
2. 按需激活机制经过至少 30 天的真实数据验证
3. Token 消耗减少 ≥ 30%
4. 激活准确率 ≥ 85%
5. 没有引入新的系统性问题

**如果不满足条件：**
- 继续优化激活规则
- 或者放弃按需激活，回到全量加载
- 或者只在特定场景下使用按需激活

---

## 10. 实施路径（如果进入 v1.2）

### Phase 1: 最小验证（1-2 周）

**目标：** 验证两层加载机制是否可行

**实施：**
- 只实现 Level 0 + Level 1
- 手动选择 3-5 个 Skill 进行测试
- 记录激活日志和统计数据

**验收标准：**
- Level 1 激活准确率 ≥ 80%
- Token 消耗减少 ≥ 20%

### Phase 2: 规则引擎（2-3 周）

**目标：** 实现基于规则的激活判断

**实施：**
- 实现 `SkillActivationManager`
- 实现触发条件匹配逻辑
- 增加激活日志和统计

**验收标准：**
- 规则覆盖率 ≥ 70%
- 误激活率 ≤ 15%

### Phase 3: LLM 辅助（2-3 周）

**目标：** 在规则无法判断时，使用 LLM 辅助

**实施：**
- 实现 LLM 辅助判断逻辑
- 记录 LLM 判断的准确率
- 优化 LLM prompt

**验收标准：**
- LLM 辅助判断准确率 ≥ 85%
- LLM 调用次数 ≤ 30%

### Phase 4: 全面推广（1-2 周）

**目标：** 将按需激活机制应用到所有 Skill

**实施：**
- 为所有现有 Skill 生成激活元数据
- 更新 Skill Auto-Creation v1.1，自动生成激活元数据
- 全面切换到按需激活模式

**验收标准：**
- 所有 Skill 都有激活元数据
- 系统稳定运行 ≥ 7 天
- 没有重大问题

---

## 11. 风险与缓解

### 11.1 风险

**1. 激活判断不准确**
- 误激活：不需要的 Skill 被激活，浪费 token
- 漏激活：需要的 Skill 没有被激活，导致任务失败

**2. 增加系统复杂度**
- 需要维护激活规则
- 需要记录激活日志
- 需要分析激活统计

**3. 性能开销**
- 每次任务都要判断激活条件
- 可能增加延迟

### 11.2 缓解措施

**1. 激活判断不准确**
- 从简单规则开始，逐步优化
- 记录所有激活决策，定期回顾
- 提供手动激活接口，作为兜底

**2. 增加系统复杂度**
- 保持激活规则简单
- 自动化激活日志分析
- 提供可视化工具

**3. 性能开销**
- 缓存激活判断结果
- 只在任务开始时判断一次
- 使用异步判断，不阻塞主流程

---

## 12. 总结

**本设计说明提出了一个"按需激活"机制，用于解决 Skill 数量增加后的 token 消耗和上下文污染问题。**

**核心思路：**
- 分层可见性（Level 0 / Level 1 / Level 2）
- 触发条件判断（规则优先，LLM 辅助）
- 独立上下文执行（只返回摘要）
- 完整的激活证据（日志 + 统计）

**与 v1.1 的关系：**
- v1.1 专注于"生成 Skill"
- 本设计说明专注于"激活 Skill"
- 两者互补，不冲突

**进入 v1.2 的条件：**
- v1.1 观察期通过
- 按需激活机制经过验证
- 有真实数据支持

**当前状态：**
- design-only，不改 v1.1 冻结基线
- 作为研究附录存在
- 为未来 v1.2 提供输入

---

**文档版本：** v0.1  
**最后更新：** 2026-03-09  
**下一步：** 等待 v1.1 观察期结束，根据真实数据决定是否进入 v1.2
