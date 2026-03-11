# Skill 自动创建 MVP v1.1 详细规格书

**版本：** v1.1  
**状态：** spec_finalized  
**最后更新：** 2026-03-09  
**存档 ID：** i2p1l9

---

## 目标

从真实重复模式中自动生成 1 个 Skill 草案，经过验证后进入隔离注册区，并留下使用后反馈。

---

## 最小闭环

```
发现 → 生成 → 验证 → 隔离注册 → 试运行反馈
```

---

## 核心模块

### 1. skill_candidate_detector
**功能：** 发现重复模式

**输入：**
- 历史执行日志
- Agent 行为记录
- 用户交互记录

**输出：**
- 候选模式列表
- 重复频率
- 模式描述

**实现：**
- 扫描最近 N 天的日志
- 识别重复的命令序列
- 计算重复频率和稳定性

### 2. skill_drafter
**功能：** 生成 Skill 草案包

**输入：**
- 候选模式
- 历史执行记录
- 上下文信息

**输出：**
- SKILL.md（完整草案）
- skill_trigger.py（触发条件）
- 示例脚本（如需要）

**实现：**
- 提取模式的核心步骤
- 生成 SKILL.md 模板
- 生成触发条件代码
- 生成示例脚本

### 3. skill_validator
**功能：** 三层验证（语法/行为/风险）

**输入：**
- Skill 草案包

**输出：**
- 验证结果（通过/失败）
- 错误详情
- 风险评估

**实现：**
- **L0 语法验证** - 检查 SKILL.md 格式、YAML frontmatter、必需字段
- **L1 行为验证** - 模拟执行，检查输入输出、错误处理
- **L2 风险验证** - 安全扫描，检查数据泄露、提示注入、恶意命令

### 4. skill_draft_registry
**功能：** 管理隔离注册状态

**输入：**
- 验证通过的 Skill 草案

**输出：**
- 注册记录
- 状态跟踪

**实现：**
- 写入 `skills/drafts/` 目录
- 记录到 `skill_draft_registry.jsonl`
- 状态：draft → testing → approved → production

### 5. skill_feedback_loop
**功能：** 记录试运行反馈

**输入：**
- Skill 执行结果
- 用户反馈

**输出：**
- 反馈记录
- 改进建议

**实现：**
- 记录每次执行的成功/失败
- 收集用户反馈
- 生成改进建议

---

## 太极OS 特色

### Reality Ledger
记录完整生命周期：
- 发现时间
- 生成时间
- 验证结果
- 注册状态
- 执行记录
- 反馈记录

### Evolution Score
衡量真实收益：
- 使用频率
- 成功率
- 节省时间
- 用户满意度

### 易经状态引擎
决定当前是否允许生成/验证/推广：
- **稳态** - 允许生成和验证
- **变态** - 暂停生成，观察现有 Skill
- **守势** - 只验证，不生成
- **进势** - 加速生成和推广

---

## 验收标准

1. ✅ 识别 1 个真实候选
2. ✅ 生成 1 个草案包
3. ✅ 完成三层验证
4. ✅ 进入 draft registry（不直接上生产）
5. ✅ 留下反馈记录

---

## 第一批推荐类型

**适合自动创建：**
- 日志分析类
- 报告整理类
- 规则检查类
- GitHub 项目摘要类
- 配置一致性检查类

**不做高风险类型：**
- 文件修改
- 自动修复
- 外部写入
- 高权限执行

---

## 当前状态

- ✅ 设计阶段完成
- ✅ 第一批候选清单已确认（存档 ID: 0z6vul）
- ✅ 首个 MVP 目标：`heartbeat_alert_deduper`
- ✅ MVP v1.1 详细规格书已完成
- 🚧 观察期内不改生产主链路

---

## Skill Trigger 设计

### 核心概念

每个 Skill 都应该有一个触发条件，决定何时激活。

### 最小字段

```python
class SkillTrigger:
    activation_signals: List[str]  # 激活信号
    negative_conditions: List[str]  # 排除条件
    priority_score: int  # 优先级（0-100）
    required_context_keys: List[str]  # 必需的上下文字段
```

### 示例

```python
# heartbeat_alert_deduper 的触发条件
activation_signals = [
    "heartbeat",
    "alert",
    "告警",
    "重复告警"
]

negative_conditions = [
    "首次告警",
    "新错误类型"
]

priority_score = 80

required_context_keys = [
    "alert_history",
    "current_alert"
]
```

### 为什么重要

1. **防止 Skill 爆炸** - 随着 Skill 增加，不会所有 Skill 都塞进上下文
2. **提高准确性** - 只有真正相关的 Skill 才会被考虑
3. **降低成本** - 减少无效的 Skill 加载和 token 消耗
4. **为未来铺路** - 这是走向动态上下文匹配的第一步

---

## 实施路径

### Phase 1：最小 MVP
- 自动检测 + 草案生成 + 验证 + 隔离注册 + 反馈

### Phase 2：融合 Agent 主动创建
- system prompt + skill_manage 工具

### Phase 3：渐进式加载 + 自动改进
- Level 0/1/2 + 自动生成 patch

---

## 关键约束

### 观察期原则
- **不碰主链路** - 不改 heartbeat、不改 Agent System
- **先观察，再决策** - 先看证据，再动手
- **可回滚** - 所有改动都可以回滚

### 最小改动原则
- **不引入复杂的规则引擎** - MVP 原则
- **不做全局重构** - 最小改动原则
- **不改现有 Skill 的加载逻辑** - 观察期原则

---

## 核心定义

**Skill 自动创建 = 自动生成能力包 + 触发条件 + 验证方式**

没有触发条件的 Skill 不能规模化。

---

## 分阶段路径

- **Phase 1** - 先让每个新 Skill 带一个最小 trigger
- **Phase 2** - 再让多个 Skill 之间有简单优先级
- **Phase 3** - 最后才考虑规则依赖、排斥、上下文压缩

---

**版本：** v1.1  
**状态：** spec_finalized  
**最后更新：** 2026-03-09
