---
name: aios-health-check
version: 1.0.0
description: Check AIOS system health (Evolution Score, event log size, Agent status). Use when monitoring AIOS or troubleshooting issues.
---

# AIOS Health Check v1.0

全面的 AIOS 系统健康检查，实时监控系统状态，及时发现问题。

## 核心功能

- ✅ **多维度检查** - 覆盖 10+ 关键指标
- ✅ **智能诊断** - 自动分析问题根因
- ✅ **修复建议** - 提供可执行的修复方案
- ✅ **趋势分析** - 对比历史数据，发现异常
- ✅ **告警分级** - INFO/WARNING/CRITICAL 三级告警

## 使用方法

### 1. 快速检查

```bash
python check.py
```

### 2. 详细检查

```bash
python check.py --verbose
```

### 3. 只检查特定项

```bash
# 只检查 Evolution Score
python check.py --check evolution

# 只检查 Agent 状态
python check.py --check agents

# 只检查磁盘空间
python check.py --check disk
```

### 4. 生成报告

```bash
python check.py --report health-report.md
```

## 输出格式

标准 Skill 格式：
```json
{
  "ok": true,
  "result": {
    "health_score": 95,
    "status": "GOOD",
    "total_issues": 1,
    "issues": [
      {
        "level": "WARNING",
        "category": "disk",
        "message": "Event log size: 12.5 MB (threshold: 10 MB)",
        "suggestion": "Run cleanup.py to archive old events"
      }
    ],
    "checks": {
      "evolution_score": {"status": "OK", "value": 0.95},
      "event_log_size": {"status": "WARNING", "value": "12.5 MB"},
      "agent_status": {"status": "OK", "active": 37, "degraded": 0},
      "disk_space": {"status": "OK", "free": "45.2 GB"},
      "memory_usage": {"status": "OK", "used": "2.1 GB"},
      "task_success_rate": {"status": "OK", "rate": 0.85}
    }
  },
  "evidence": ["events.jsonl", "metrics_history.jsonl", "agents.json"],
  "next": ["cleanup.py"]
}
```

## 检查项目

### 1. Evolution Score（进化分数）
- **阈值：** < 0.4 → CRITICAL，< 0.6 → WARNING
- **检查：** 当前分数、7天趋势
- **建议：** 触发 Self-Improving Loop

### 2. Event Log Size（事件日志大小）
- **阈值：** > 10 MB → WARNING，> 50 MB → CRITICAL
- **检查：** events.jsonl 文件大小
- **建议：** 运行 cleanup.py 归档旧事件

### 3. Agent Status（Agent 状态）
- **阈值：** 任何 Agent degraded → WARNING
- **检查：** agents.json 中的状态
- **建议：** 重启 degraded Agent

### 4. Disk Space（磁盘空间）
- **阈值：** < 10 GB → WARNING，< 5 GB → CRITICAL
- **检查：** 工作目录可用空间
- **建议：** 清理旧数据或扩容

### 5. Memory Usage（内存使用）
- **阈值：** > 80% → WARNING，> 90% → CRITICAL
- **检查：** Python 进程内存占用
- **建议：** 重启进程或优化代码

### 6. Task Success Rate（任务成功率）
- **阈值：** < 70% → WARNING，< 50% → CRITICAL
- **检查：** task_executions.jsonl 统计
- **建议：** 分析失败原因，触发改进

### 7. API Health（API 健康度）
- **阈值：** 连续失败 > 5 次 → WARNING
- **检查：** api_monitor_state.json
- **建议：** 检查 API 配置或网络

### 8. Heartbeat Status（心跳状态）
- **阈值：** 超过 10 分钟未心跳 → WARNING
- **检查：** heartbeat.log 最后时间
- **建议：** 检查 Cron 任务或进程

### 9. Backup Status（备份状态）
- **阈值：** 超过 24 小时未备份 → WARNING
- **检查：** backups/ 最新备份时间
- **建议：** 运行 backup.py

### 10. Learning Agent Activity（学习 Agent 活跃度）
- **阈值：** 超过 7 天未运行 → WARNING
- **检查：** learning_agents.py 状态
- **建议：** 激活休眠 Agent

## 健康分数计算

```
健康分数 = Σ (检查项权重 × 检查项得分)

权重分配：
- Evolution Score: 25%
- Task Success Rate: 20%
- Agent Status: 15%
- Event Log Size: 10%
- Disk Space: 10%
- Memory Usage: 10%
- API Health: 5%
- Heartbeat Status: 5%
```

**分数等级：**
- 90-100: EXCELLENT（优秀）
- 80-89: GOOD（良好）
- 70-79: FAIR（一般）
- 60-69: POOR（较差）
- < 60: CRITICAL（危急）

## 自动化集成

### 1. 每小时自动检查（Cron）

```bash
# 每小时检查一次
0 * * * * cd /path/to/aios && python check.py
```

### 2. Heartbeat 集成

在 `heartbeat_v5.py` 中添加：
```python
# 每小时检查健康度
if current_minute == 0:
    run_health_check()
```

### 3. Dashboard 集成

Dashboard 实时显示健康分数和告警。

## 告警通知

### 1. Telegram 通知

```bash
# 健康分数 < 70 时发送通知
python check.py --notify-telegram
```

### 2. 邮件通知

```bash
# 健康分数 < 60 时发送邮件
python check.py --notify-email
```

### 3. Webhook 通知

```bash
# 自定义 Webhook
python check.py --webhook https://your-webhook-url
```

## 报告示例

```markdown
# AIOS 健康检查报告

**检查时间：** 2026-03-04 15:35:00  
**健康分数：** 95/100 (GOOD)  
**总问题数：** 1

## 检查结果

### ✅ 正常项目（9）
- Evolution Score: 0.95
- Agent Status: 37 active, 0 degraded
- Disk Space: 45.2 GB free
- Memory Usage: 2.1 GB (15%)
- Task Success Rate: 85%
- API Health: OK (247 consecutive)
- Heartbeat Status: OK (last: 2 min ago)
- Backup Status: OK (last: 3 hours ago)
- Learning Agents: OK (all active)

### ⚠️  警告项目（1）
- **Event Log Size:** 12.5 MB (threshold: 10 MB)
  - **建议：** Run cleanup.py to archive old events

## 趋势分析

- Evolution Score: 稳定（7天平均: 0.94）
- Task Success Rate: 上升（+5% vs 昨天）
- Disk Space: 下降（-2 GB vs 昨天）

## 建议操作

1. 运行 cleanup.py 清理旧事件
2. 继续观察 Evolution Score 趋势
```

## 最佳实践

1. **定期检查** - 每小时自动检查，及时发现问题
2. **告警分级** - 根据严重程度设置不同通知方式
3. **趋势分析** - 对比历史数据，发现异常趋势
4. **自动修复** - 低风险问题自动修复（如清理日志）
5. **人工介入** - 高风险问题人工确认后修复

## 故障排查

### 检查失败

```bash
# 查看详细日志
python check.py --verbose

# 检查文件权限
ls -la aios/

# 手动检查各项
python check.py --check evolution
python check.py --check agents
```

### 误报告警

```bash
# 调整阈值
python check.py --threshold evolution=0.5

# 忽略特定检查
python check.py --ignore event_log_size
```

## 未来改进（v1.1）

- [ ] 机器学习异常检测（基于历史数据）
- [ ] 自动修复（低风险问题自动处理）
- [ ] 预测性维护（提前预警潜在问题）
- [ ] 多维度对比（与其他 AIOS 实例对比）
- [ ] 可视化报告（图表展示趋势）

---

**版本：** v1.0.0  
**最后更新：** 2026-03-04  
**维护者：** 小九 + 珊瑚海
