# Token Budget Modes - 完整设计方案

**版本：** v1.0  
**日期：** 2026-03-07  
**作者：** 小九 + 珊瑚海

---

## 1. 背景与目标

### 问题
- AIOS 当前无 token 预算控制，容易超支
- 开发调试时需要高质量输出，日常使用时需要节省成本
- 缺少自动降级机制，预算耗尽后无保护

### 目标
- 提供 **Dev** 和 **Economy** 两种模式
- 实现多层级预算控制（per-call / per-task / per-agent / daily / monthly）
- 自动降级保护，避免预算爆炸
- 完整可观测性，知道钱花在哪里

---

## 2. 模式定义

### Dev 模式（开发者模式）

**适用场景：** 开发、测试、复杂任务、紧急问题

| 维度 | 配置 |
|------|------|
| Token 限制 | ❌ 无限制 |
| 默认模型 | Claude Opus 4 / Sonnet 4 |
| 自动降级 | ❌ 禁用 |
| 详细日志 | ✅ 完整保留 |
| 多轮重试 | ✅ 允许（最多 3 次） |
| 长上下文 | ✅ 允许（最大 200k tokens） |
| 预算检查 | ⚠️ 仅告警，不阻断 |

### Economy 模式（经济模式）

**适用场景：** 日常使用、简单任务、批量处理

| 维度 | 配置 |
|------|------|
| Token 限制 | ✅ 严格限制 |
| 默认模型 | Claude Haiku 4 / 本地模型 |
| 自动降级 | ✅ 启用 |
| 详细日志 | ⚠️ 精简（仅关键信息） |
| 多轮重试 | ⚠️ 限制（最多 1 次） |
| 长上下文 | ⚠️ 限制（最大 32k tokens） |
| 预算检查 | ✅ 超限阻断 |

---

## 3. 预算层级

### 层级定义

```
per-call limit (单次调用)
    ↓
per-task limit (单个任务)
    ↓
per-agent limit (单个 Agent)
    ↓
daily limit (每日总额)
    ↓
monthly limit (每月总额)
```

### 默认配置

#### Dev 模式
```json
{
  "per_call_limit": null,        // 无限制
  "per_task_limit": null,        // 无限制
  "per_agent_limit": null,       // 无限制
  "daily_limit": 1000000,        // 1M tokens/day（仅告警）
  "monthly_limit": 30000000      // 30M tokens/month（仅告警）
}
```

#### Economy 模式
```json
{
  "per_call_limit": 10000,       // 10k tokens/call
  "per_task_limit": 50000,       // 50k tokens/task
  "per_agent_limit": 200000,     // 200k tokens/agent/day
  "daily_limit": 500000,         // 500k tokens/day（硬限制）
  "monthly_limit": 15000000      // 15M tokens/month（硬限制）
}
```

### 超限行为

| 层级 | Dev 模式 | Economy 模式 |
|------|----------|--------------|
| per-call | 告警 | 阻断 + 压缩 prompt |
| per-task | 告警 | 阻断 + 禁止重试 |
| per-agent | 告警 | 降级模型 |
| daily | 告警 | 自动切换到 Economy |
| monthly | 告警 | 人工确认 |

---

## 4. 模型路由策略

### Dev 模式路由规则

```python
def route_dev_mode(task_type, complexity):
    """Dev 模式：优先质量"""
    if complexity == "high":
        return "claude-opus-4"
    elif complexity == "medium":
        return "claude-sonnet-4"
    else:
        return "claude-haiku-4"  # 简单任务也可以省点
```

### Economy 模式路由规则

```python
def route_economy_mode(task_type, complexity, budget_remaining):
    """Economy 模式：优先成本"""
    
    # 预算不足 20%，强制降级
    if budget_remaining < 0.2:
        return "local-model"  # 本地模型（免费）
    
    # 预算不足 50%，限制高级模型
    if budget_remaining < 0.5:
        if complexity == "high":
            return "claude-haiku-4"  # 降级
        else:
            return "local-model"
    
    # 预算充足，按复杂度选择
    if complexity == "high":
        return "claude-sonnet-4"  # 最高只到 Sonnet
    elif complexity == "medium":
        return "claude-haiku-4"
    else:
        return "local-model"
```

### 核心任务保护

**核心任务定义：**
- Self-Improving Loop
- LowSuccess Regeneration
- Adversarial Validation
- 用户明确指定的任务

**保护规则：**
- 核心任务在 Economy 模式下也可以使用 Sonnet
- 非核心任务优先降级
- 预算不足 10% 时，只允许核心任务

---

## 5. 降级与保护机制

### 降级策略（按优先级）

#### Level 1: Prompt 优化（最轻）
- 移除冗余 system prompt
- 压缩历史上下文
- 限制输出长度（max_tokens）

#### Level 2: 模型降级
- Opus → Sonnet
- Sonnet → Haiku
- Haiku → 本地模型

#### Level 3: 功能限制
- 禁止多轮重试
- 禁止详细 reasoning
- 禁止长上下文

#### Level 4: 任务延迟
- 非核心任务进入队列
- 等待预算恢复后执行
- 人工确认后执行

### 自动降级触发条件

| 预算剩余 | 动作 |
|----------|------|
| 80%+ | 正常运行 |
| 50-80% | Level 1 降级（Prompt 优化） |
| 20-50% | Level 2 降级（模型降级） |
| 10-20% | Level 3 降级（功能限制） |
| <10% | Level 4 降级（任务延迟） |

---

## 6. 监控指标

### 基础指标

```json
{
  "prompt_tokens": 12450,
  "completion_tokens": 3820,
  "total_tokens": 16270,
  "estimated_cost": 0.048,
  "model": "claude-sonnet-4",
  "mode": "economy",
  "timestamp": "2026-03-07T18:51:00Z"
}
```

### 聚合指标

#### 按 Agent 统计
```json
{
  "agent_id": "coder-dispatcher",
  "total_tokens": 245000,
  "total_cost": 0.735,
  "call_count": 18,
  "avg_tokens_per_call": 13611,
  "top_consumer_rank": 1
}
```

#### 按任务类型统计
```json
{
  "task_type": "code_generation",
  "total_tokens": 180000,
  "total_cost": 0.540,
  "call_count": 12,
  "success_rate": 0.917
}
```

#### 每日统计
```json
{
  "date": "2026-03-07",
  "mode": "economy",
  "total_tokens": 487000,
  "total_cost": 1.461,
  "daily_limit": 500000,
  "usage_rate": 0.974,
  "downgrade_count": 3,
  "blocked_count": 0
}
```

### Dashboard 展示指标

- **当前模式：** Dev / Economy
- **今日预算使用率：** 97.4% (487k / 500k)
- **本月预算使用率：** 32.5% (4.87M / 15M)
- **Top 3 消费 Agent：** coder (245k), analyst (180k), monitor (62k)
- **降级次数：** 3 次
- **节省效果：** Economy 模式节省 $2.34 (vs Dev 模式预估)

---

## 7. 配置示例

### 配置文件：`token_budget_config.json`

```json
{
  "mode": "economy",
  "auto_switch": {
    "enabled": true,
    "trigger_threshold": 0.8,
    "recovery_threshold": 0.5
  },
  "budgets": {
    "dev": {
      "per_call_limit": null,
      "per_task_limit": null,
      "per_agent_limit": null,
      "daily_limit": 1000000,
      "monthly_limit": 30000000,
      "enforce": false
    },
    "economy": {
      "per_call_limit": 10000,
      "per_task_limit": 50000,
      "per_agent_limit": 200000,
      "daily_limit": 500000,
      "monthly_limit": 15000000,
      "enforce": true
    }
  },
  "models": {
    "dev": {
      "high_complexity": "claude-opus-4",
      "medium_complexity": "claude-sonnet-4",
      "low_complexity": "claude-haiku-4"
    },
    "economy": {
      "high_complexity": "claude-sonnet-4",
      "medium_complexity": "claude-haiku-4",
      "low_complexity": "local-model"
    }
  },
  "core_tasks": [
    "self_improving_loop",
    "low_success_regeneration",
    "adversarial_validation",
    "user_explicit"
  ],
  "downgrade_strategy": {
    "level_1_threshold": 0.5,
    "level_2_threshold": 0.2,
    "level_3_threshold": 0.1,
    "level_4_threshold": 0.05
  },
  "pricing": {
    "claude-opus-4": {
      "input": 15.0,
      "output": 75.0
    },
    "claude-sonnet-4": {
      "input": 3.0,
      "output": 15.0
    },
    "claude-haiku-4": {
      "input": 0.25,
      "output": 1.25
    },
    "local-model": {
      "input": 0.0,
      "output": 0.0
    }
  }
}
```

---

## 8. 状态切换规则

### 手动切换

```python
# 用户指定模式
set_mode("dev")      # 切换到 Dev 模式
set_mode("economy")  # 切换到 Economy 模式
```

### 自动切换

#### 触发条件
- 达到 80% 日预算 → 自动切换到 Economy
- 达到 90% 月预算 → 自动切换到 Economy + 告警

#### 恢复条件
- 第二天 00:00 重置日预算
- 预算恢复到 50% 以下 → 可手动切回 Dev
- 每月 1 号重置月预算

#### 状态机

```
Dev Mode
    ↓ (daily budget > 80%)
Economy Mode (auto)
    ↓ (next day reset)
Dev Mode (if manually enabled)
    ↓ (monthly budget > 90%)
Economy Mode (locked until next month)
```

---

## 9. 实现落地顺序

### Phase 1: 配置文件 + Router 集成（1-2 天）

**目标：** 最小闭环，能根据模式选模型

**交付物：**
- `token_budget_config.json` - 配置文件
- `model_router_v2.py` 升级 - 集成 budget mode
- `token_budget_manager.py` - 预算管理器（最简版）

**验证标准：**
- Dev 模式能使用 Opus/Sonnet
- Economy 模式能使用 Haiku/本地模型
- 配置文件能控制模式切换

---

### Phase 2: Token 记录 + 预算检查（2-3 天）

**目标：** 记录每次调用，累积统计，超限告警

**交付物：**
- `token_usage_recorder.py` - 记录器
- `token_usage.jsonl` - 使用记录
- `token_stats.json` - 聚合统计
- 预算检查逻辑（per-call / per-task / per-agent / daily / monthly）

**验证标准：**
- 每次调用自动记录 token
- 超限能触发告警
- Economy 模式超限能阻断

---

### Phase 3: 降级策略 + 自动切换（2-3 天）

**目标：** 预算不足时自动降级，保护系统

**交付物：**
- `downgrade_strategy.py` - 降级策略
- 自动切换逻辑（Dev ↔ Economy）
- Prompt 压缩工具

**验证标准：**
- 预算不足 50% 能自动降级模型
- 预算不足 20% 能限制功能
- 预算不足 10% 能延迟任务

---

### Phase 4: Dashboard 可视化（1-2 天）

**目标：** 展示预算使用情况，节省效果

**交付物：**
- Dashboard 新增 Token Budget 卡片
- 实时预算使用率
- Top 消费 Agent/Task
- 降级次数统计

**验证标准：**
- Dashboard 能显示当前模式
- 能显示预算使用率
- 能显示节省效果

---

## 10. 成功标准

### 功能完整性
- ✅ Dev 和 Economy 模式能正常切换
- ✅ 多层级预算控制生效
- ✅ 自动降级保护生效
- ✅ Token 使用可追溯

### 成本效果
- Economy 模式比 Dev 模式节省 **60%+ 成本**
- 预算超限率 < 5%
- 核心任务不受影响

### 可观测性
- 每日自动生成预算报告
- Dashboard 实时展示使用情况
- 超限告警及时触发

---

## 11. 风险与缓解

### 风险 1: Economy 模式影响质量
**缓解：** 核心任务保护，允许使用 Sonnet

### 风险 2: 自动降级过于激进
**缓解：** 分级降级，逐步限制，不一刀切

### 风险 3: 预算计算不准确
**缓解：** 使用官方定价，定期校准

### 风险 4: 本地模型质量不稳定
**缓解：** 仅用于简单任务，复杂任务仍用云端模型

---

## 12. 未来扩展

### 短期（1 个月）
- 支持更多模型（Gemini, GPT-4）
- 支持自定义预算层级
- 支持预算共享（多用户）

### 中期（3 个月）
- 智能预算预测（基于历史使用）
- 动态定价（根据 API 实时价格）
- 成本优化建议（自动识别浪费）

### 长期（6 个月）
- 多租户预算隔离
- 预算市场（用户间交易）
- AI 驱动的成本优化

---

**版本：** v1.0  
**状态：** 设计完成，待实现  
**下一步：** Phase 1 - 配置文件 + Router 集成
