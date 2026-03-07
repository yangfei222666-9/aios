# Token Monitor 使用指南

## 概述

Token Monitor 是 AIOS 的 Token 使用监控系统，帮助你：
- 实时监控 Token 使用量
- 自动告警（超过预算时）
- 自动优化（切换模型/减频率/批量处理）
- 生成可视化报告

**灵感来源：** 珊瑚海的 TOKEN 管理避免爆炸方案

## 核心功能

### 1. 实时监控

每次 Heartbeat 自动检查 Token 使用量：

```python
from token_monitor import check_and_alert

alert = check_and_alert()
if alert:
    print(f"⚠️ {alert['level']}: {alert['title']}")
```

### 2. 阈值告警

配置文件：`token_monitor_config.json`

```json
{
  "budget": {
    "daily_limit": 1000000,    // 每日上限（100万）
    "weekly_limit": 5000000,   // 每周上限（500万）
    "monthly_limit": 20000000  // 每月上限（2000万）
  },
  "thresholds": {
    "warning": 0.7,   // 70% 时警告
    "critical": 0.9   // 90% 时严重告警
  }
}
```

### 3. 自动优化

超过阈值时自动应用优化策略：

**策略 1: 切换到便宜模型（80%）**
- claude-opus-4-6 → claude-sonnet-4-6
- 成本降低 80%

**策略 2: 减少心跳频率（85%）**
- 30秒 → 60秒
- Token 使用减少 50%

**策略 3: 批量处理（90%）**
- 单个任务 → 批量处理（5个一批）
- 减少重复上下文

### 4. 可视化报告

每日/每周/每月自动生成报告：

```bash
python token_cli.py --report --period daily
```

输出：
```
╔══════════════════════════════════════════════════════════════╗
║  Token 使用报告 - DAILY  ║
╚══════════════════════════════════════════════════════════════╝

📊 总览:
   总使用量: 123,456 tokens
   预算上限: 1,000,000 tokens
   使用率: 12.3%
   剩余: 876,544 tokens
   总成本: $1.85

📈 按模型统计:
   claude-opus-4-6:
      Tokens: 50,000
      Cost: $1.00
   claude-sonnet-4-6:
      Tokens: 73,456
      Cost: $0.85

📋 按任务类型统计:
   code:
      Tokens: 80,000
      Cost: $1.20
   analysis:
      Tokens: 43,456
      Cost: $0.65
```

## 使用方式

### 方式 1: 集成到 Heartbeat（推荐）

已自动集成到 `heartbeat_v5.py`，每次心跳自动检查。

### 方式 2: 手动记录

```python
from token_monitor import log_usage

log_usage(
    model='claude-opus-4-6',
    input_tokens=1000,
    output_tokens=500,
    task_type='code',
    task_id='task-001'
)
```

### 方式 3: CLI 工具

```bash
# 查看每日使用量
python token_cli.py

# 查看每周使用量
python token_cli.py --period weekly

# 生成完整报告
python token_cli.py --report

# 手动记录使用
python token_cli.py --log claude-opus-4-6 1000 500 --type code --id task-001
```

## 集成到 AIOS

### Heartbeat 集成

`heartbeat_v5.py` 已自动集成：

```python
# 0. Token Monitor (每次心跳)
print("[TOKEN] Token Usage Check:")
alert = check_and_alert()
if alert:
    print(f"   ⚠️ {alert['level'].upper()}: {alert['title']}")
    
    # 自动优化
    strategies = auto_optimize()
    if strategies:
        print(f"   🔧 Auto-optimization applied:")
        for s in strategies:
            print(f"      - {s['name']}: {s['action']}")
```

### Task Executor 集成

在 `task_executor.py` 中记录每个任务的 Token 使用：

```python
from token_monitor import log_usage

def execute_task(task):
    # ... 执行任务 ...
    
    # 记录 Token 使用
    log_usage(
        model=task['model'],
        input_tokens=result['input_tokens'],
        output_tokens=result['output_tokens'],
        task_type=task['type'],
        task_id=task['id']
    )
```

## 配置说明

### 预算设置

根据你的实际预算调整：

```json
{
  "budget": {
    "daily_limit": 1000000,    // 每日上限
    "weekly_limit": 5000000,   // 每周上限
    "monthly_limit": 20000000  // 每月上限
  }
}
```

### 模型价格

根据最新价格更新：

```json
{
  "pricing": {
    "claude-opus-4-6": {
      "input": 15.0,   // 每1M tokens（美元）
      "output": 75.0
    },
    "claude-sonnet-4-6": {
      "input": 3.0,
      "output": 15.0
    }
  }
}
```

### 优化策略

自定义优化策略：

```json
{
  "optimization": {
    "enabled": true,
    "strategies": [
      {
        "name": "switch_to_cheaper_model",
        "trigger": 0.8,  // 80% 时触发
        "action": "switch_model",
        "params": {
          "from": "claude-opus-4-6",
          "to": "claude-sonnet-4-6"
        }
      }
    ]
  }
}
```

## 告警通知

告警自动写入 `alerts.jsonl`，由 `notifier.py` 发送到 Telegram。

告警格式：

```json
{
  "timestamp": "2026-03-04T12:00:00",
  "level": "warning",
  "title": "Token 使用量告警 (75.0%)",
  "body": "每日使用量: 750,000 / 1,000,000\n使用率: 75.0%\n剩余: 250,000 tokens\n成本: $11.25",
  "sent": false
}
```

## 最佳实践

### 1. 设置合理预算

根据你的实际使用情况设置预算：

- **开发阶段：** 每日 100万 tokens（~$15）
- **生产阶段：** 每日 500万 tokens（~$75）
- **高负载：** 每日 2000万 tokens（~$300）

### 2. 监控成本趋势

每周查看报告，分析成本趋势：

```bash
python token_cli.py --report --period weekly
```

### 3. 优化高成本任务

找出高成本任务类型，针对性优化：

- **代码生成：** 使用 claude-sonnet（便宜 80%）
- **简单分析：** 使用 claude-haiku（便宜 95%）
- **复杂推理：** 才用 claude-opus

### 4. 批量处理

相似任务批量处理，减少重复上下文：

```python
# 不好：单个处理
for task in tasks:
    execute_task(task)  # 每次都要加载上下文

# 好：批量处理
execute_batch(tasks)  # 共享上下文
```

## 故障排查

### 问题 1: 告警不发送

**原因：** `notifier.py` 未运行

**解决：** 检查 Heartbeat 是否正常运行

### 问题 2: 使用量统计不准

**原因：** 未记录所有任务的 Token 使用

**解决：** 在 `task_executor.py` 中添加 `log_usage()`

### 问题 3: 自动优化不生效

**原因：** 配置文件中 `optimization.enabled` 为 `false`

**解决：** 修改配置文件，设置为 `true`

## 文件说明

- `token_monitor.py` - 核心监控逻辑
- `token_cli.py` - 命令行工具
- `token_monitor_config.json` - 配置文件
- `token_usage.jsonl` - 使用记录
- `alerts.jsonl` - 告警记录

## 下一步

- [ ] 集成到 Dashboard（可视化图表）
- [ ] 支持多用户（按用户统计）
- [ ] 预测未来使用量（基于历史数据）
- [ ] 自动调整预算（根据使用趋势）

---

**版本：** v1.0  
**最后更新：** 2026-03-04  
**维护者：** 小九 + 珊瑚海
