# Skill Router 验收文档

**版本：** v1.0.0  
**日期：** 2026-03-11  
**状态：** ✅ 验收通过

---

## 1. 核心目标

把 skill-router 做成一个**可回放、可解释、可测试**的离线路由器。

**核心能力：** 回答"现在发生了什么，该由谁处理，为什么这么处理"

---

## 2. 交付物清单

### 2.1 核心代码

- ✅ `skill_router_schema.py` - 输入输出 schema 定义
- ✅ `skill_router.py` - 三层判定逻辑实现
- ✅ `test_skill_router.py` - 测试套件
- ✅ `fixtures/router_cases.json` - 8 个固定测试样本

### 2.2 文档

- ✅ `SKILL_ROUTER_ACCEPTANCE.md` - 本验收文档

---

## 3. 输入输出定义

### 3.1 标准输入 - TaskContext

```python
{
    "source": str,              # 来源（heartbeat/user/system/cron）
    "task_type": str,           # 任务类型
    "content": str,             # 任务内容描述
    "priority": str,            # 优先级（critical/high/normal/low）
    "risk_level": str,          # 风险等级（high/medium/low/safe）
    "system_state": dict,       # 当前系统状态
    "recent_history": list,     # 最近历史
    "available_handlers": list  # 可用处理器列表
}
```

### 3.2 标准输出 - RouterOutput

```python
{
    "situation_type": str,           # 情况类型
    "candidates": list,              # 所有候选（CandidateHandler 列表）
    "chosen_handler": str | None,    # 选中的处理器
    "decision_reason": str,          # 决策原因
    "rejected_handlers": list,       # 被拒绝的处理器及原因
    "confidence": float,             # 决策置信度（0-100）
    "fallback_handlers": list,       # 备选处理器
    "routing_metadata": dict         # 路由元数据
}
```

---

## 4. 三层判定逻辑

### L0: 信号过滤

**作用：** 分类当前情况

**逻辑：**
- 根据 priority + task_type + risk_level 分类
- 输出 situation_type（如 `critical_backup`, `routine_monitor`）

### L1: 上下文匹配

**作用：** 找出所有候选处理器

**逻辑：**
1. 能力匹配 - 检查 task_type 是否在技能支持列表中
2. 上下文匹配 - 检查风险等级是否匹配
3. 历史表现 - 从技能注册表读取 success_rate
4. 计算匹配分数（0-100）
5. 按分数排序

**匹配分数计算：**
- 能力匹配：40分
- 上下文匹配：30分
- 历史表现：30分
- 关键任务加权：优先选择高成功率

### L2: 最终路由决策

**作用：** 选择最合适的处理器

**逻辑：**
1. 过滤掉匹配分数 < 40 的候选
2. 选择最高分
3. 生成决策原因
4. 记录被拒绝的处理器及原因
5. 选择最多 2 个备选处理器

---

## 5. 四句话解释

skill-router 必须能回答这 4 句话：

1. **现在发生了什么** → `situation_type`
2. **哪些 handler 入围了** → `candidates`（分数 >= 40）
3. **为什么选这个** → `decision_reason`
4. **为什么别的没选** → `rejected_handlers`

**实现方式：** `explain_decision()` 方法

---

## 6. 测试用例（8 个）

### 6.1 单候选清晰命中

**输入：** 健康检查任务，只有 aios-health-monitor 可用  
**期望：** 选中 aios-health-monitor，置信度 >= 80  
**结果：** ✅ 通过（置信度 99.4）

### 6.2 多候选冲突

**输入：** 分析任务，3 个候选（pattern-detector, agent-performance-analyzer, lesson-extractor）  
**期望：** 选中一个，至少 2 个候选，至少 1 个备选  
**结果：** ✅ 通过（选中 lesson-extractor，置信度 97.6）

### 6.3 高风险但仍可路由

**输入：** 紧急备份任务（critical + medium risk）  
**期望：** 选中 backup-restore-manager，置信度 >= 70  
**结果：** ✅ 通过（置信度 98.0）

### 6.4 无候选命中

**输入：** 未知任务类型 + 高风险  
**期望：** 无选中，置信度 0  
**结果：** ✅ 通过（所有候选分数过低）

### 6.5 学习任务

**输入：** GitHub 项目分析  
**期望：** 选中 github-repo-analyzer  
**结果：** ✅ 通过（置信度 98.5）

### 6.6 告警处理

**输入：** 系统健康告警  
**期望：** 选中 aios-health-monitor  
**结果：** ✅ 通过（置信度 99.4）

### 6.7 性能分析

**输入：** Agent 表现评估  
**期望：** 选中 agent-performance-analyzer  
**结果：** ✅ 通过（置信度 97.0）

### 6.8 模式检测

**输入：** 重复失败识别  
**期望：** 选中 pattern-detector  
**结果：** ✅ 通过（置信度 96.4）

---

## 7. 验收标准

### 7.1 核心能力

- ✅ 能输出候选，不是黑盒直选
- ✅ 能解释为什么选中
- ✅ 能解释为什么淘汰
- ✅ 决策结果可写日志供复盘

### 7.2 可回放

- ✅ 输入输出 schema 固定
- ✅ 决策过程可序列化为 JSON
- ✅ 支持 `route_and_log()` 记录决策历史

### 7.3 可解释

- ✅ `explain_decision()` 输出 4 句话
- ✅ 每个候选有 match_reasons 和 reject_reasons
- ✅ 决策原因包含分数和关键因素

### 7.4 可测试

- ✅ 8 个固定测试样本
- ✅ 所有测试通过
- ✅ 测试覆盖 4 类场景（单候选/多候选/高风险/无候选）

---

## 8. 防跑偏检查

### 8.1 不做的事（已遵守）

- ✅ 不接主链路 - 当前是离线路由器，不直接调用 Agent
- ✅ 不做复杂评分黑盒 - 评分逻辑清晰可见（40+30+30）
- ✅ 不提前揉进 policy 逻辑 - 只做路由，不做风险决策

### 8.2 边界清晰

- skill-router 只负责"选谁做"
- policy-decision 负责"能不能做"（下一步）
- decide-and-dispatch 负责"怎么做"（最后一步）

---

## 9. 下一步

**Step 2: policy-decision**

在 skill-router 稳定后，开始实现 policy-decision：
- 风险判断
- 降级策略
- fallback 机制

**不要并行开发，先把 router 用起来。**

---

## 10. 验收结论

**状态：** ✅ 验收通过

**理由：**
1. 所有交付物齐全
2. 输入输出 schema 已钉死
3. 三层判定逻辑清晰
4. 8 个测试用例全部通过
5. 可回放、可解释、可测试
6. 防跑偏检查通过

**skill-router v1.0 可以进入下一阶段。**

---

**验收人：** 小九  
**验收时间：** 2026-03-11 08:13
