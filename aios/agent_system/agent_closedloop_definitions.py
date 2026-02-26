"""
批量更新所有 Agent 为完整闭环模式
"""

# 所有 Agent 的完整闭环定义
AGENT_CLOSEDLOOP_DEFINITIONS = {
    "Monitor": """
**Phase 1: 检测（Detection）**
- 检查系统资源（CPU/内存/磁盘/GPU）
- 检查关键进程状态
- 检查 AIOS Evolution Score
- 检查最近 1h 的 CRIT 事件

**Phase 2: 分析（Analysis）**
- 识别资源异常（CPU >80%, 内存 >85%）
- 识别进程异常（崩溃、未响应）
- 评估系统健康等级

**Phase 3: 决策（Decision）**
- 正常 → 静默
- 警告 → 通知 + 触发 Self-Healing
- 严重 → 立即通知 + 触发紧急修复

**Phase 4: 验证（Verification）**
- 如果触发了修复 → 等待 30s 后再次检查
- 确认问题是否解决

**Phase 5: 学习（Learning）**
- 记录监控历史到 `monitor_history.jsonl`
- 更新正常基线（CPU/内存正常范围）
- 如果频繁告警 → 调整阈值

**输出：**
- MONITOR_OK → 系统正常（静默）
- MONITOR_WARNING:N → N 个警告
- MONITOR_CRITICAL:N → N 个严重问题
""",

    "Reviewer": """
**Phase 1: 收集（Collect）**
- 运行 `git log --since="7 days ago" --oneline`
- 运行 `git diff HEAD~7..HEAD --stat`
- 读取变更的文件列表

**Phase 2: 审查（Review）**
- 代码质量：可读性、复杂度、重复代码
- 安全性：硬编码密钥、潜在风险
- 性能：慢查询、内存泄漏
- 文档：注释、README 更新

**Phase 3: 评分（Score）**
- Critical 问题（必须修复）
- Major 问题（建议修复）
- Minor 问题（可选优化）
- 优点（值得表扬）

**Phase 4: 建议（Suggest）**
- 生成修复建议
- 如果有 Critical → 触发 Coder Agent 修复
- 如果有安全问题 → 触发 Security Agent

**Phase 5: 追踪（Track）**
- 记录审查历史到 `review_history.jsonl`
- 追踪问题修复状态
- 更新代码质量趋势

**输出：**
- REVIEW_OK → 无变更或无问题（静默）
- REVIEW_ISSUES:N → 发现 N 个问题
""",

    "Security": """
**Phase 1: 扫描（Scan）**
- 运行 `security_auditor.py`
- 检查文件访问权限
- 检查工具使用权限
- 扫描敏感操作日志

**Phase 2: 分析（Analyze）**
- 识别异常访问模式
- 识别权限提升尝试
- 评估安全风险评分（0-10）

**Phase 3: 响应（Response）**
- 风险 <5 → 记录
- 风险 5-7 → 警告
- 风险 >7 → 自动熔断 + 立即通知

**Phase 4: 修复（Remediate）**
- 撤销异常权限
- 锁定可疑操作
- 触发 Backup Agent（预防数据丢失）

**Phase 5: 强化（Harden）**
- 更新安全规则
- 记录到 `security_incidents.jsonl`
- 更新 Playbook 防御规则

**输出：**
- SECURITY_AUDIT_OK → 无问题（静默）
- SECURITY_AUDIT_WARNINGS:N → N 个警告
- SECURITY_AUDIT_CRITICAL:N → N 个严重问题
""",

    "Optimizer": """
**Phase 1: 监控（Monitor）**
- 运行 `resource_optimizer.py`
- 检测内存泄漏（>500MB 增长）
- 检测闲置进程（>1h）
- 分析缓存命中率

**Phase 2: 识别（Identify）**
- 识别性能瓶颈
- 识别资源浪费
- 识别优化机会

**Phase 3: 优化（Optimize）**
- 清理闲置进程
- 调整缓存策略
- 优化资源分配
- 应用低风险优化

**Phase 4: 验证（Verify）**
- 优化后测量效果
- 对比优化前后指标
- 确认改进幅度

**Phase 5: 学习（Learn）**
- 记录优化效果到 `optimization_history.jsonl`
- 更新优化策略库
- 如果效果好 → 推广到其他场景

**输出：**
- RESOURCE_OPTIMIZER_OK → 无需优化（静默）
- RESOURCE_OPTIMIZER_APPLIED:N → 应用了 N 个优化
- RESOURCE_OPTIMIZER_SUGGESTIONS:N → 生成了 N 个建议
""",

    "Anomaly Detector": """
**Phase 1: 检测（Detection）**
- 运行 `anomaly_detector.py`
- 时间异常：非工作时间大量活动
- 资源异常：CPU/内存峰值
- 模式异常：快速重复调用
- 行为异常：偏离正常模式

**Phase 2: 分类（Classification）**
- 正常波动 vs 真实异常
- 异常严重程度（low/medium/high/critical）
- 异常类型（资源/行为/模式/时间）

**Phase 3: 响应（Response）**
- Low → 记录
- Medium → 警告
- High → 触发 Debugger Agent
- Critical → 自动熔断 + 立即通知

**Phase 4: 隔离（Isolation）**
- 熔断异常 Agent
- 保护系统稳定性
- 记录熔断原因

**Phase 5: 恢复（Recovery）**
- 5 分钟后尝试恢复
- 验证异常是否消失
- 记录到 `anomaly_history.jsonl`

**输出：**
- ANOMALY_OK → 无异常（静默）
- ANOMALY_DETECTED:N → 检测到 N 个异常
- ANOMALY_CRITICAL:N → N 个严重异常（自动熔断）
""",

    "Learning": """
**Phase 1: 收集（Collect）**
- 运行 `learning_orchestrator_simple.py`
- 收集 Provider 性能数据
- 收集 Playbook 效果数据
- 收集 Agent 行为数据
- 收集错误模式数据
- 收集优化效果数据

**Phase 2: 分析（Analyze）**
- Provider Learner：哪个模型最好
- Playbook Learner：哪些规则有效
- Agent Behavior Learner：哪些行为成功
- Error Pattern Learner：哪些错误重复
- Optimization Learner：哪些优化有效

**Phase 3: 提取（Extract）**
- 提取最佳实践
- 提取失败教训
- 提取优化策略

**Phase 4: 应用（Apply）**
- 更新 Agent 配置
- 更新 Playbook 规则
- 更新优化策略

**Phase 5: 验证（Verify）**
- 追踪应用效果
- 对比应用前后指标
- 记录到 `learning_history.jsonl`

**输出：**
- LEARNING_ORCHESTRATOR_OK → 无重要发现（静默）
- LEARNING_ORCHESTRATOR_SUGGESTIONS:N → 生成了 N 条改进建议
"""
}

print("Agent 完整闭环定义已准备")
print(f"总计 {len(AGENT_CLOSEDLOOP_DEFINITIONS)} 个 Agent")
