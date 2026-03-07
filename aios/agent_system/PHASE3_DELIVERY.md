# Phase 3 Adversarial Validation System - 完整交付

**交付时间：** 2026-03-06 17:20  
**版本：** v1.0  
**状态：** ✅ 测试通过（4/4）

---

## 📦 交付清单

### 1. 核心模块

| 文件 | 功能 | 状态 |
|------|------|------|
| `phase3_types.py` | 类型定义（TokenUsage/GenerateRequest/GenerateResponse/DecisionResult） | ✅ |
| `legacy_llm_adapter.py` | 兼容适配器（旧版 llm_generate_func → 新接口） | ✅ |
| `debate_pipeline.py` | Bull vs Bear 辩论 + 64卦调解 + 异常处理 | ✅ |
| `tests/test_phase3_exceptions.py` | 异常处理测试（4个测试用例） | ✅ |

### 2. 测试结果

```bash
tests/test_phase3_exceptions.py::test_model_timeout_fallback PASSED      [ 25%]
tests/test_phase3_exceptions.py::test_empty_response_fallback PASSED     [ 50%]
tests/test_phase3_exceptions.py::test_crisis_hard_gate_unskippable PASSED [ 75%]
tests/test_phase3_exceptions.py::test_conflicting_conclusion_escalation PASSED [100%]

============================== 4 passed in 0.10s ==============================
```

---

## 🎯 核心功能

### 1. Bull vs Bear 辩论

**流程：**
```
任务输入
    ↓
Bull 辩手（生成支持论据）
    ↓
Bear 辩手（识别风险点）
    ↓
检查冲突（Bull approve vs Bear reject）
    ↓
64卦调解（融合双方观点）
    ↓
最终决策（approve/reject/defer）
```

**特性：**
- 多轮辩论（max_rounds 可配置，默认3轮）
- 权重动态调整（基于 Evolution Score）
- 冲突自动升级（Bull vs Bear 冲突 → 人工门控）

### 2. 64卦智慧调解

**卦象策略：**
- **大过卦（28）** - 高风险任务强制人工审批（硬门控）
- **既济卦（63）** - 快速通道（3轮）
- **未济卦（64）** - 深度辩论（5轮）
- **坤卦（2）** - 稳健策略（默认）

**权重映射（Evolution Score）：**
- 90-100: Bull 0.7 / Bear 0.3（激进）
- 70-89:  Bull 0.6 / Bear 0.4（平衡偏激进）
- 50-69:  Bull 0.5 / Bear 0.5（中性）
- 30-49:  Bull 0.4 / Bear 0.6（保守）
- 0-29:   Bull 0.3 / Bear 0.7（极保守）

### 3. 异常处理

**降级策略：**
- LLM 超时 → defer + 人工门控
- 空响应 → defer + 人工门控
- Bull/Bear 冲突 → defer 或 reject
- 大过卦 + 高风险 → 强制人工审批（rounds_used=0）

**测试覆盖：**
- ✅ `test_model_timeout_fallback` - LLM 超时降级
- ✅ `test_empty_response_fallback` - 空响应降级
- ✅ `test_crisis_hard_gate_unskippable` - 大过卦硬门控
- ✅ `test_conflicting_conclusion_escalation` - 冲突升级

---

## 🚀 使用方式

### 方式 A：直接使用（推荐）

```python
from debate_pipeline import run_debate_pipeline
from legacy_llm_adapter import LegacyLLMAdapter

# 1. 创建 LLM Provider（适配旧版函数）
def my_llm_func(prompt: str) -> str:
    # 你的 LLM 调用逻辑
    return "这是 LLM 的响应"

adapter = LegacyLLMAdapter(my_llm_func, model_id="gpt-4")

# 2. 执行辩论
result = run_debate_pipeline(
    task_text="发布配置变更",
    risk_level="medium",
    provider=adapter,
    task_id="task-001"
)

# 3. 检查结果
print(f"决策：{result.verdict}")  # approve/reject/defer
print(f"原因：{result.reason}")
print(f"置信度：{result.confidence}")
print(f"需要人工：{result.requires_human_gate}")
```

### 方式 B：集成到现有系统

```python
from debate_pipeline import run_debate_pipeline

# 假设你已有 Provider 实现了 generate(GenerateRequest) -> GenerateResponse
result = run_debate_pipeline(
    task_text="删除生产旧表并迁移数据库",
    risk_level="high",
    provider=your_provider,
    task_id="task-002"
)

if result.requires_human_gate:
    # 升级到人工审批
    notify_human(result.reason)
else:
    # 自动执行
    execute_task(result.verdict)
```

---

## 📊 决策审计

**审计日志：** `decision_audit.jsonl`

**格式：**
```json
{
  "audit_id": "audit-20260306172000-a1b2c3d4",
  "timestamp": "2026-03-06T17:20:00",
  "task_id": "task-001",
  "system_state": {
    "evolution_score": 97.1,
    "hexagram": "坤卦",
    "hexagram_id": 2,
    "confidence": 0.995
  },
  "debate_policy": {
    "bull_weight": 0.7,
    "bear_weight": 0.3,
    "max_rounds": 3,
    "flags": [],
    "task_risk_level": "medium"
  },
  "debate_result": {
    "bull_args": ["支持论据1", "支持论据2"],
    "bear_args": ["风险点1", "风险点2"],
    "judge_decision": "approve - 风险可控"
  },
  "final_decision": "approve"
}
```

---

## 🔧 配置参数

### run_debate_pipeline 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `task_text` | str | 必填 | 任务描述 |
| `risk_level` | str | "medium" | 风险等级（low/medium/high） |
| `provider` | Provider | None | LLM Provider |
| `force_hexagram` | str | None | 强制卦象（测试用） |
| `force_evolution_score` | float | None | 强制 Evolution Score（测试用） |
| `task_id` | str | None | 任务 ID（可选） |

### DecisionResult 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `verdict` | str | 决策结果（approve/reject/defer） |
| `reason` | str | 决策原因 |
| `rounds_used` | int | 使用轮次 |
| `early_exit` | bool | 是否提前退出 |
| `confidence` | float | 置信度（0-1） |
| `requires_human_gate` | bool | 是否需要人工审批 |
| `audit_id` | str | 审计 ID |

---

## 🎯 下一步计划

### Phase 3.1: 真实 LLM 集成（2小时）
- 集成 OpenAI/Anthropic API
- 替换 mock provider
- 验证真实辩论效果

### Phase 3.2: Dashboard 可视化（3小时）
- 辩论统计（Bull vs Bear 胜率）
- 卦象分布（哪些卦象最常触发）
- 决策趋势（approve/reject/defer 比例）

### Phase 3.3: 自动优化（5小时）
- 根据历史决策调整权重
- 学习成功/失败模式
- 自动调整 max_rounds

---

## 📝 变更日志

**v1.0 (2026-03-06)**
- ✅ 完整的 Bull vs Bear 辩论系统
- ✅ 64卦智慧调解
- ✅ 异常处理（超时/空响应/冲突）
- ✅ 大过卦硬门控
- ✅ 决策审计链
- ✅ 4个测试用例全部通过

---

**维护者：** 小九 + 珊瑚海  
**最后更新：** 2026-03-06 17:20
