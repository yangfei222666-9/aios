# Manifest 兼容层文档

## 概述

`manifest_schema.py` 提供新旧 manifest 格式的归一化能力，确保下游只需处理统一结构。

## 字段优先级规则

### 顶层字段映射

| 归一化字段 | 优先来源 | 回退来源 | 默认值 | 目标段 |
|-----------|---------|---------|-------|--------|
| `selected_mode` | `selected_mode` | `mode` | `""` | `decision` |
| `mode_reason` | `mode_reason` | `reason` | `""` | `decision` |
| `uncertainty_score` | `uncertainty_score` | - | `None` | `risk` |
| `convergence_score` | `convergence_score` | - | `None` | `risk` |

### decision 段内映射

| 归一化字段 | 优先来源 | 回退来源 | 默认值 |
|-----------|---------|---------|-------|
| `confidence` | `confidence` | `confidence_score` | `None` |

### 优先级逻辑

1. **新字段优先**：如果 `selected_mode` 存在，忽略 `mode`
2. **回退机制**：如果新字段不存在，使用旧字段
3. **默认值兜底**：新旧字段都不存在时，使用默认值
4. **空字符串语义**：`selected_mode=""` 视为"已设置但为空"，**不会回退**到 `mode`

## 必需字段

顶层必须包含：
- `name` (string)
- `version` (string)

缺失任一字段将抛出 `ValueError`，错误消息格式：
```
MANIFEST_SCHEMA_ERROR: manifest missing required keys: name, version
```

## 归一化输出结构

```python
{
    "meta": {
        "name": str,
        "version": str,
        # ... 其他 meta 字段
    },
    "decision": {
        "confidence": float | None,
        "selected_mode": str,
        "mode_reason": str,
        # ... 其他 decision 字段
    },
    "risk": {
        "uncertainty_score": float | None,
        "convergence_score": float | None,
        # ... 其他 risk 字段
    },
    "runtime": {
        # 透传原始 runtime 段
    },
    "extras": {
        # 未识别的顶层字段（不丢弃）
    }
}
```

## 使用示例

### 新版 manifest（完整字段）

```python
from manifest_loader import load_manifest_compat

manifest = load_manifest_compat("agent_v2.json")
# {
#   "meta": {"name": "coder", "version": "2.0.0"},
#   "decision": {
#     "selected_mode": "fast",
#     "mode_reason": "低复杂度",
#     "confidence": 0.88
#   },
#   "risk": {
#     "uncertainty_score": 0.12,
#     "convergence_score": 0.95
#   },
#   ...
# }
```

### 旧版 manifest（回退字段）

```python
raw = {
    "name": "legacy-agent",
    "version": "1.0.0",
    "mode": "slow",
    "reason": "高风险",
    "decision": {"confidence_score": 0.75}
}

from manifest_schema import normalize_manifest
m = normalize_manifest(raw)
# decision.selected_mode = "slow" (从 mode 回退)
# decision.mode_reason = "高风险" (从 reason 回退)
# decision.confidence = 0.75 (从 confidence_score 回退)
```

### 混合字段（新字段优先）

```python
raw = {
    "name": "mixed",
    "version": "1.5.0",
    "mode": "slow",           # 被忽略
    "selected_mode": "fast",  # 优先
}
# 结果: decision.selected_mode = "fast"
```

### 空字符串不回退

```python
raw = {
    "name": "test",
    "version": "1.0.0",
    "selected_mode": "",  # 明确设置为空
    "mode": "vote"        # 不会被使用
}
# 结果: decision.selected_mode = "" (不回退到 "vote")
```

## Runtime Config 适配

`to_runtime_config()` 将归一化 manifest 转为执行器配置：

```python
from adapters.manifest_adapter import to_runtime_config

config = to_runtime_config(manifest)
# {
#   "name": "coder",
#   "version": "2.0.0",
#   "confidence": 0.88,
#   "selected_mode": "fast",        # 透传（观测用）
#   "mode_hint": "...",             # 透传（若存在）
#   "_obs_uncertainty_score": 0.12, # 观测字段（带前缀）
#   "_obs_convergence_score": 0.95,
#   # ... runtime 段字段
# }
```

### 观测字段命名规则

- 新增观测字段带 `_obs_` 前缀
- 旧调用路径不感知这些字段
- 仅用于日志/监控，不影响执行逻辑

## 错误处理

所有校验错误统一前缀 `MANIFEST_SCHEMA_ERROR:`，便于日志检索和告警聚合。

### 常见错误

```python
# 缺少必需字段
ValueError: MANIFEST_SCHEMA_ERROR: manifest missing required keys: name

# 类型错误
ValueError: MANIFEST_SCHEMA_ERROR: manifest must be a dict, got str

# 文件不存在
FileNotFoundError: manifest not found: /path/to/file.json

# JSON 解析失败
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

## 测试覆盖

完整测试套件见 `tests/test_manifest_compat.py`：

1. ✅ 新版 manifest（含 4 新字段）→ 正常加载
2. ✅ 旧版 manifest（无新字段）→ 默认值补齐
3. ✅ 混合字段（新旧共存）→ 新字段优先
4. ✅ 非法 manifest（缺必需键）→ 明确报错
5. ✅ 文件加载（JSON）→ 正常解析
6. ✅ 文件不存在 → FileNotFoundError
7. ✅ 空字符串不回退 → 明确语义

## 版本历史

- **v1.0** (2026-03-06) - 初始版本，支持 D1-D5 字段兼容
