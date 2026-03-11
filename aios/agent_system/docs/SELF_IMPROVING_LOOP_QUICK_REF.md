# Self-Improving Loop - 快速参考

## 概述

Self-Improving Loop 是太极OS 的自我改进引擎，让 AI Agent 能够自动检测问题、生成改进方案、应用改进并验证效果。

## 核心特性

- ✅ **自动检测失败模式** - 分析任务执行记录，识别重复失败
- ✅ **自动生成改进方案** - 基于失败模式生成具体改进建议
- ✅ **自动应用低风险改进** - 只自动应用 `risk=low` 的改进
- ✅ **自动回滚失败改进** - 如果改进后效果变差，自动回滚
- ✅ **冷却期保护** - 防止频繁改进导致系统不稳定
- ✅ **完整的追踪和日志** - 所有改进都有记录可追溯

## 快速开始

### 1. 检查所有 Agent 健康状况（Dry-Run）

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 run_self_improving.py --dry-run
```

**输出示例：**
```
============================================================
Self-Improving Loop - 自动改进
============================================================
时间: 2026-03-12 00:09:10
模式: Dry-Run（只分析）

📊 检查 8 个 Agent...

✅ agent_coder_001
   任务数: 3 | 成功率: 100.0%

⚠️ coder-dispatcher
   任务数: 3 | 成功率: 0.0%
   🔧 需要改进

============================================================
汇总统计
============================================================
✅ 健康: 6
⚠️ 不健康: 2
🔧 需要改进: 2

📈 总改进次数: 3
📋 已改进 Agent: 3

⚠️ Dry-Run 模式，未应用改进
```

### 2. 检查单个 Agent（生产模式）

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 run_self_improving.py --agent-id coder-dispatcher
```

### 3. 在代码中使用

```python
from src.self_improving_loop import SelfImprovingLoop

loop = SelfImprovingLoop()

# 包装任务执行
result = loop.execute_with_improvement(
    agent_id="coder-001",
    task="修复登录 bug",
    execute_fn=lambda: agent.run_task(task)
)

print(f"任务结果: {result['success']}")
print(f"改进触发: {result['improvement_triggered']}")
print(f"改进应用: {result['improvement_applied']}")
```

## 改进触发条件

改进会在以下情况自动触发：

1. **成功率 < 70%** - Agent 的任务成功率低于 70%
2. **至少 3 次任务** - 有足够的数据支持分析
3. **不在冷却期** - 距离上次改进超过 6 小时

## 改进流程

```
1. 执行任务 → 记录结果
2. 检测失败模式 → 分析原因
3. 生成改进建议 → 评估风险
4. 应用低风险改进 → 备份配置
5. 验证改进效果 → 计算指标
6. 自动回滚（如果效果变差）
7. 更新配置 → 记录历史
```

## 风险等级

- **low** - 自动应用（如：调整超时时间、优化提示词）
- **medium** - 需要人工确认（如：修改核心逻辑）
- **high** - 需要人工审核（如：修改系统配置）

## 自动回滚条件

改进后如果出现以下情况，会自动回滚：

1. **连续失败 10 次** - 改进后连续失败
2. **成功率下降 > 20%** - 改进后成功率显著下降
3. **平均耗时增加 > 50%** - 改进后性能显著下降

## 数据文件

- `data/loop_state.json` - 改进状态（最后改进时间、备份信息）
- `data/loop.log` - 详细日志（所有改进操作）
- `data/agent_traces.jsonl` - 任务执行记录
- `data/agent_configs.json` - Agent 配置（包含统计信息）

## 查看统计

```python
from src.self_improving_loop import SelfImprovingLoop

loop = SelfImprovingLoop()

# 单个 Agent 统计
stats = loop.get_improvement_stats("coder-001")
print(f"最后改进: {stats['last_improvement']}")
print(f"冷却剩余: {stats['cooldown_remaining_hours']:.1f}h")

# 全局统计
global_stats = loop.get_improvement_stats()
print(f"总改进次数: {global_stats['total_improvements']}")
print(f"已改进 Agent: {global_stats['agents_improved']}")
```

## 集成到 Heartbeat

Self-Improving Loop 已集成到 `HEARTBEAT.md`，每次心跳自动执行：

```powershell
# 步骤 4：运行自动改进检查
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 run_self_improving.py --dry-run
```

## 常见问题

### Q: 为什么改进没有触发？

A: 检查以下条件：
1. 成功率是否 < 70%
2. 任务数是否 >= 3
3. 是否在冷却期（6 小时）

### Q: 如何手动触发改进？

A: 使用 `run_self_improving.py --agent-id <agent_id>`

### Q: 如何查看改进历史？

A: 查看 `data/loop.log` 和 `data/loop_state.json`

### Q: 如何禁用自动改进？

A: 在 Heartbeat 中注释掉自动改进步骤，或使用 `--dry-run` 模式

### Q: 改进失败了怎么办？

A: 系统会自动回滚。如果需要手动回滚，查看 `data/loop_state.json` 中的备份信息

## 最佳实践

1. **先用 Dry-Run 模式** - 了解系统会做什么改进
2. **定期查看日志** - 了解改进历史和效果
3. **监控成功率** - 确保改进真的有效
4. **保持冷却期** - 不要频繁改进，给系统稳定时间
5. **记录重要改进** - 在 MEMORY.md 中记录关键改进

## 下一步

- [ ] 增加更多改进策略（Prompt 优化、模型切换等）
- [ ] 支持 A/B 测试验证改进效果
- [ ] 增加改进效果可视化（Dashboard）
- [ ] 支持自定义改进规则
- [ ] 增加改进建议的人工审核流程

---

**版本：** v0.1.0  
**最后更新：** 2026-03-12  
**维护者：** 小九 + 珊瑚海
