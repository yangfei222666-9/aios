# AIOS 事件分析报告

**分析时间**: 2025-12-24  
**数据源**: `aios/data/events.jsonl`  
**分析范围**: 最近 100 条事件（总计 335 条）

---

## 1. 层级事件统计

| 层级 | 事件数量 | 占比 |
|------|---------|------|
| **KERNEL** | 64 | 64.0% |
| **SEC** | 23 | 23.0% |
| **TOOL** | 13 | 13.0% |
| **COMMS** | 0 | 0.0% |
| **MEM** | 0 | 0.0% |

### 分析
- **KERNEL 层**占主导（64%），包含核心系统组件（pipeline、scheduler、agent_system、score_engine）
- **SEC 层**（安全层）占 23%，主要是 reactor 和 circuit_breaker 事件
- **TOOL 层**（工具监控）占 13%，包括资源监控器
- **COMMS 和 MEM 层**在此样本中无事件

---

## 2. 最频繁的 3 种错误类型

| 排名 | 错误类型 | 出现次数 |
|------|---------|---------|
| 1 | `agent.error` | 3 |
| 2 | `reactor.failed` | 3 |

### 错误详情
- **agent.error**: Agent 执行任务失败（如 "Task failed"）
- **reactor.failed**: Reactor 执行失败（如 "Execution failed"）

### 建议
- 检查 Agent 任务失败的根本原因（超时、资源不足、逻辑错误）
- 审查 Reactor playbook 配置，确保执行逻辑健壮

---

## 3. 工具调用平均耗时

- **平均耗时**: 681.68 ms
- **样本数**: 37 次调用
- **耗时范围**: 50 ms ~ 5000 ms（估算）

### 分析
- 平均耗时较高（681 ms），可能受以下因素影响：
  - Pipeline 完整执行（5000 ms）
  - Agent 任务执行（300-1000 ms）
  - Reactor 处理（100-1500 ms）
- 建议优化长耗时操作，考虑异步处理或缓存机制

---

## 4. 事件来源分布（Top 5）

| 来源 | 事件数 |
|------|--------|
| reactor | 23 |
| pipeline | 16 |
| agent_demo_agent | 14 |
| score_engine | 10 |
| agent_test_agent | 10 |

---

## 总结

1. **系统健康度**: 整体运行正常，错误率低（6%）
2. **性能瓶颈**: 平均耗时 681 ms，建议优化 pipeline 和 agent 执行
3. **安全机制**: SEC 层活跃，circuit_breaker 和 reactor 正常工作
4. **监控覆盖**: TOOL 层监控到位，资源告警及时触发

---

**报告生成**: 自动化分析脚本  
**数据文件**: `report_data.json`
