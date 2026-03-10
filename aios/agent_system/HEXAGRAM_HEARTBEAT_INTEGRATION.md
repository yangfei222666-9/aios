# Hexagram Heartbeat Integration

**观察型集成：在 Heartbeat 中展示卦象智慧，不影响 Router 决策。**

---

## 1. 集成目标

在 Heartbeat 主流程中增加卦象智慧区块，提供：
- 全局系统健康卦象
- Active Agent 生命周期摘要
- 风险等级和建议动作
- 护栏触发状态

**当前阶段：观察型集成**
- 只展示卦象信息，不影响 Router 决策
- 不改变任务调度逻辑
- 为后续深度集成积累数据

---

## 2. 输入指标来源

### 系统指标（从现有数据文件）

| 指标 | 数据源 | 说明 |
|------|--------|------|
| `api_health` | `api_health.json` | API 健康度（0-1） |
| `execution_success_rate` | `task_executions.jsonl` | 执行成功率 |
| `timeout_rate` | `task_executions.jsonl` | 超时率 |
| `retry_rate` | `task_executions.jsonl` | 重试率 |
| `learning_hit_rate` | `recommendation_log.jsonl` | 学习命中率 |
| `queue_depth` | `task_queue.jsonl` | 队列深度 |
| `evolution_score` | `evolution_score.json` | 演化分数 |

### Agent 指标（从 agents.json）

| 指标 | 说明 |
|------|------|
| `tasks_completed` | 完成任务数 |
| `tasks_failed` | 失败任务数 |
| `last_active` | 最后活跃时间 |

---

## 3. 输出字段说明

### 全局卦象

```python
{
    "global_hexagram_name": "坤卦",           # 卦名
    "global_hexagram_bits": "000000",        # 卦象二进制
    "global_risk_level": "low",              # 风险等级（low/medium/high）
    "global_recommended_actions": [          # 建议动作（最多3条）
        "保持当前策略",
        "继续积累经验"
    ],
    "guardrail_triggered": false,            # 是否触发护栏
    "guardrail_reasons": []                  # 护栏原因
}
```

### Active Agent 生命周期

```python
[
    {
        "agent_name": "coder-dispatcher",    # Agent 名称
        "lifecycle_hexagram": "乾卦",        # 生命周期卦象
        "lifecycle_stage": "mature",         # 生命周期阶段
        "keep_active": true                  # 是否保持活跃
    }
]
```

---

## 4. 失败保护原则

### 核心原则：卦象引擎异常不影响 Heartbeat 主流程

**保护机制：**

1. **模块导入失败** → 使用 fallback 模式
   ```python
   try:
       from hexagram_engine import HexagramEngine
       HEXAGRAM_AVAILABLE = True
   except ImportError:
       HEXAGRAM_AVAILABLE = False
   ```

2. **卦象计算异常** → 返回 "unavailable"
   ```python
   try:
       hexagram_result = self.engine.consult(...)
   except Exception as e:
       result["global_hexagram_name"] = "unavailable"
   ```

3. **整体失败** → 返回简化版本
   ```python
   except Exception as e:
       return """
       [UNAVAILABLE]
         Hexagram engine encountered an error.
         Heartbeat continues normally.
       """
   ```

**验证标准：**
- ✅ 卦象引擎报错时，Heartbeat 正常完成
- ✅ 错误信息写入日志，不抛出异常
- ✅ 卦象区块显示 "unavailable"，不显示空白

---

## 5. 当前阶段：观察型集成

### 不影响 Router

**明确边界：**
- ✅ Heartbeat 展示卦象信息
- ✅ 记录卦象历史数据
- ❌ **不修改** Router 决策逻辑
- ❌ **不修改** 任务调度优先级
- ❌ **不修改** Agent 选择策略

### 观察期目标（2周）

**数据积累：**
- 收集 14 天卦象历史
- 统计卦象分布
- 分析卦象与成功率相关性
- 验证护栏触发准确性

**评估指标：**
- 卦象引擎稳定性（无崩溃）
- 卦象建议合理性（人工评估）
- 护栏触发准确性（误报率 <5%）

---

## 6. 集成到 Heartbeat

### 使用方式

```python
# 在 heartbeat_v5.py 中添加

from heartbeat_hexagram_integration_example import HeartbeatHexagramIntegration

def heartbeat():
    # ... 原有逻辑 ...
    
    # 卦象集成（观察型）
    try:
        integration = HeartbeatHexagramIntegration(workspace_root)
        hexagram_output = integration.run()
        print(hexagram_output)
    except Exception as e:
        print(f"[WARN] Hexagram integration skipped: {e}")
    
    # ... 原有逻辑 ...
```

### 输出示例

```
============================================================
🔮 HEXAGRAM WISDOM
============================================================

[GLOBAL HEXAGRAM]
  Hexagram: 坤卦 (000000)
  Risk Level: low
  Recommended Actions:
    • 保持当前策略
    • 继续积累经验
    • 稳步推进改进

[SYSTEM METRICS]
  API Health: 95.0%
  Success Rate: 92.5%
  Timeout Rate: 2.3%
  Queue Depth: 3
  Evolution Score: 99.5

[ACTIVE AGENTS LIFECYCLE]
  ✓ coder-dispatcher
      Hexagram: 乾卦
      Stage: mature
  ✓ analyst-dispatcher
      Hexagram: 坤卦
      Stage: stable
  ✓ monitor-dispatcher
      Hexagram: 既济卦
      Stage: optimal

============================================================
```

---

## 7. 验收标准

### 4 条核心标准

1. ✅ **Heartbeat 能稳定输出卦象区块**
   - 每次 Heartbeat 都有卦象输出
   - 格式清晰，信息完整

2. ✅ **卦象引擎异常不会拖垮主流程**
   - 卦象计算失败时，Heartbeat 正常完成
   - 错误信息写入日志，不抛出异常

3. ✅ **Active Agent 生命周期摘要可读**
   - 最多展示 5 个 Agent
   - 卦象、阶段、状态清晰

4. ✅ **输出结构后续能直接复用到 Dashboard**
   - 数据结构标准化
   - 可直接转换为 JSON API
   - 支持前端可视化

---

## 8. 下一步计划

### Phase 1: 观察期（2周）
- 集成到 Heartbeat v5.0
- 收集卦象历史数据
- 验证稳定性和准确性

### Phase 2: 深度集成（4周）
- Router 决策参考卦象
- Agent 生命周期管理
- 自动护栏触发

### Phase 3: 完整闭环（6周）
- 卦象驱动自动优化
- 64卦智慧全面应用
- Dashboard 可视化

---

**版本：** v1.0  
**最后更新：** 2026-03-07  
**维护者：** 小九 + 珊瑚海
