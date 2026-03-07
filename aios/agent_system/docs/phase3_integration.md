# Phase 3 集成文档 - Adversarial Validation 完整闭环

**版本：** v1.0  
**日期：** 2026-03-06  
**状态：** ✅ 已完成  
**负责人：** 小九 + 珊瑚海

---

## 目录

1. [目标与范围](#1-目标与范围)
2. [架构变更](#2-架构变更)
3. [类型与接口](#3-类型与接口)
4. [关键流程](#4-关键流程)
5. [配置项](#5-配置项)
6. [测试与验收](#6-测试与验收)
7. [运行与回滚](#7-运行与回滚)
8. [风险与后续](#8-风险与后续)
9. [变更记录](#9-变更记录)

---

## 1. 目标与范围

### 1.1 目标
- **统一辩论出口** - 所有 verdict 必须经 `execute_debate_round()` 路径汇总
- **异常降级** - 模型失败自动降级到保守策略
- **强制人工门控** - 高危场景（大过卦 + high risk）强制人工审核
- **审计可追溯** - 完整记录决策链路（policy_version、prompt_hash、alert_sent）

### 1.2 范围
- `execute_debate_round()` - 统一辩论执行入口
- `on_model_error_fallback()` - 异常降级处理
- Telegram 告警 - 同步直发，失败不阻塞
- 审计字段扩展 - 新增 policy_version、prompt_hash、alert_sent
- 异常测试 - 4个核心场景全覆盖

### 1.3 非目标
- ❌ 不改业务判分策略
- ❌ 不引入新模型路由策略
- ❌ 不改变现有 Agent 调用方式

---

## 2. 架构变更

### 2.1 统一出口
**变更前：**
```python
# 多处直接调用 llm_generate_func
verdict = llm_generate_func(prompt)
```

**变更后：**
```python
# 统一经过 execute_debate_round
result = execute_debate_round(
    task_desc=task_desc,
    bull_prompt=bull_prompt,
    bear_prompt=bear_prompt,
    llm_generate_func=llm_generate_func
)
```

### 2.2 降级链路
```
模型调用失败
    ↓
on_model_error_fallback()
    ↓
conservative_fallback()
    ↓
send_telegram_alert()（同步直发）
    ↓
返回保守结论（defer + requires_human_gate=True）
```

### 2.3 硬拦截规则
```python
# 大过卦(#28) + high risk → 强制人工
if hexagram_id == 28 and risk_level == "high":
    return DecisionResult(
        verdict="defer",
        confidence=0.0,
        requires_human_gate=True,
        rounds_used=0,  # 不进入辩论
        audit_trail={
            "reason": "大过卦硬拦截",
            "policy_version": POLICY_VERSION,
            "alert_sent": True
        }
    )
```

### 2.4 审计增强
**新增字段：**
- `policy_version` - 策略版本号（如 "v3.4"）
- `prompt_hash` - prompt 内容哈希（SHA256前8位）
- `alert_sent` - 是否成功发送 Telegram 告警

---

## 3. 类型与接口

### 3.1 类型文件
**文件：** `phase3_types.py`

**核心类型：**
```python
@dataclass
class GenerateRequest:
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.7

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class GenerateResponse:
    text: str
    usage: TokenUsage
    model: str = "unknown"

@dataclass
class DecisionResult:
    verdict: str  # "approve" | "defer" | "reject"
    confidence: float
    requires_human_gate: bool
    rounds_used: int
    audit_trail: Dict[str, Any]
```

### 3.2 兼容适配
**文件：** `legacy_llm_adapter.py`

**作用：** 将旧的 `llm_generate_func(prompt)` 适配为新的 `generate(GenerateRequest)`

```python
def adapt_legacy_llm(old_func):
    def generate(req: GenerateRequest) -> GenerateResponse:
        text = old_func(req.prompt)
        usage = TokenUsage(
            prompt_tokens=len(req.prompt) // 4,
            completion_tokens=len(text) // 4,
            total_tokens=(len(req.prompt) + len(text)) // 4
        )
        return GenerateResponse(text=text, usage=usage)
    return generate
```

---

## 4. 关键流程

### 4.1 正常流程
```
1. 构造 Bull/Bear prompt
    ↓
2. execute_debate_round()
    ↓
3. 聚合双方观点
    ↓
4. 产出 DecisionResult
    ↓
5. 审计落盘（policy_version + prompt_hash + alert_sent）
```

### 4.2 异常流程
```
1. 模型超时/空响应/异常
    ↓
2. on_model_error_fallback()
    ↓
3. conservative_fallback()
    ↓
4. 尝试 Telegram 告警（同步直发）
    ↓
5. 返回保守结论（defer + requires_human_gate=True）
```

### 4.3 高危硬拦截
```
1. 检测到大过卦(#28) + high risk
    ↓
2. 直接返回 DecisionResult（rounds_used=0）
    ↓
3. 不进入 fast-track
    ↓
4. 强制 requires_human_gate=True
```

---

## 5. 配置项

### 5.1 必需配置
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 5.2 可选配置
```bash
export POLICY_VERSION="v3.4"  # 未配置时使用默认版本号
```

---

## 6. 测试与验收

### 6.1 测试文件
**文件：** `tests/test_phase3_exceptions.py`

### 6.2 测试用例
| 用例 | 场景 | 预期结果 | 状态 |
|------|------|----------|------|
| test_timeout_fallback | 模型超时 | verdict=defer, requires_human_gate=True | ✅ |
| test_empty_response_fallback | 空响应 | verdict=defer, requires_human_gate=True | ✅ |
| test_dagua_hard_block | 大过卦硬拦截 | rounds_used=0, requires_human_gate=True | ✅ |
| test_conflict_conservative_upgrade | 结论冲突 | 保守升级到 defer | ✅ |

### 6.3 验收标准
- ✅ 异常场景必为 `defer`
- ✅ `requires_human_gate=True`
- ✅ 审计三要素齐全（policy_version、prompt_hash、alert_sent）

### 6.4 运行测试
```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
pytest -q tests/test_phase3_exceptions.py
```

**预期输出：**
```
....                                                                     [100%]
4 passed in 0.12s
```

---

## 7. 运行与回滚

### 7.1 运行
```bash
# 1. 设置环境变量
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 2. 运行测试
pytest -q tests/test_phase3_exceptions.py

# 3. 集成到生产
# 在 adversarial_validator.py 中调用 execute_debate_round()
```

### 7.2 回滚策略
**保留：**
- 类型定义（phase3_types.py）
- 适配器（legacy_llm_adapter.py）

**关闭：**
- 仅关闭新入口开关（若有 feature flag）

**恢复：**
- 恢复旧审计结构（不建议删除字段）

---

## 8. 风险与后续

### 8.1 风险
- ⚠️ **Token 统计偏差** - legacy 适配器使用估算（len(text) // 4），与真实 LLM token 统计有偏差

### 8.2 后续优化
1. **接入生产 LLM Client**
   - 替换 legacy 适配器为真实 `llm_client.generate(GenerateRequest)`
   - 获取准确的 token 统计

2. **告警增强**
   - 增加告警重试机制（失败后重试3次）
   - 增加告警限流（防止告警风暴）

3. **审计增强**
   - 增加审计落库索引（`trace_id`、`prompt_hash`）
   - 支持审计查询 API

---

## 9. 变更记录

| 日期 | 版本 | 变更内容 | 负责人 |
|------|------|----------|--------|
| 2026-03-06 | v1.0 | Phase 3 完整闭环上线 | 小九 + 珊瑚海 |
| 2026-03-06 | v1.0 | 新增类型定义（phase3_types.py） | 小九 |
| 2026-03-06 | v1.0 | 新增 legacy 适配器（legacy_llm_adapter.py） | 小九 |
| 2026-03-06 | v1.0 | 新增异常测试（test_phase3_exceptions.py） | 小九 |
| 2026-03-06 | v1.0 | 审计字段扩展（policy_version、prompt_hash、alert_sent） | 小九 |

---

**文档维护：** 小九  
**最后更新：** 2026-03-06 17:17  
**状态：** ✅ 已完成
