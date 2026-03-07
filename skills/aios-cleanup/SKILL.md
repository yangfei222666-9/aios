---
name: aios-cleanup
version: 1.0.0
description: Clean up old AIOS data (events, logs, temp files). Use when disk space is low or during maintenance.
---

# AIOS Cleanup v1.0

智能清理 AIOS 旧数据，释放磁盘空间，保持系统高效运行。

## 核心功能

- ✅ **智能清理** - 自动识别可清理的数据
- ✅ **安全保护** - 保留最近 N 天的数据
- ✅ **归档压缩** - 旧数据归档而非删除
- ✅ **空间统计** - 显示清理前后的空间变化
- ✅ **干运行模式** - 预览清理效果，不实际删除

## 使用方法

### 1. 默认清理（保留 7 天）

```bash
python cleanup.py
```

### 2. 自定义保留天数

```bash
# 保留 30 天
python cleanup.py --days 30

# 保留 3 天（激进清理）
python cleanup.py --days 3
```

### 3. 干运行模式（预览）

```bash
python cleanup.py --dry-run
```

### 4. 深度清理（包括归档）

```bash
python cleanup.py --deep
```

## 输出格式

标准 Skill 格式：
```json
{
  "ok": true,
  "result": {
    "cleaned_count": 5,
    "cleaned_items": [
      "events.jsonl (1000 old entries)",
      "memory/2026-02-01.md (archived)",
      "__pycache__/ (removed)",
      "*.bak (3 files removed)",
      "temp/ (removed)"
    ],
    "space_freed": "15.2 MB",
    "space_before": "125.5 MB",
    "space_after": "110.3 MB"
  },
  "evidence": ["events.jsonl", "memory/", "__pycache__/"],
  "next": []
}
```

## 清理内容

### 1. 事件日志（events.jsonl）
- 保留最近 N 天的事件
- 旧事件归档到 `archives/events-YYYY-MM.jsonl.gz`

### 2. 每日日志（memory/*.md）
- 保留最近 N 天的日志
- 旧日志归档到 `archives/memory-YYYY-MM.tar.gz`

### 3. 临时文件
- `__pycache__/` - Python 缓存
- `*.bak` - 备份文件
- `*.tmp` - 临时文件
- `temp/` - 临时目录

### 4. 任务执行历史（可选）
- `task_executions.jsonl` - 保留最近 N 天
- 旧记录归档到 `archives/tasks-YYYY-MM.jsonl.gz`

### 5. Spawn 请求（可选）
- `spawn_requests.jsonl` - 保留最近 N 天
- 旧请求归档到 `archives/spawns-YYYY-MM.jsonl.gz`

## 清理策略

### 保守策略（默认）
- 保留天数：7 天
- 归档旧数据：是
- 删除临时文件：是
- 深度清理：否

### 激进策略
- 保留天数：3 天
- 归档旧数据：是
- 删除临时文件：是
- 深度清理：是

### 自定义策略

在 `cleanup_config.json` 中配置：
```json
{
  "keep_days": 7,
  "archive_old_data": true,
  "clean_temp_files": true,
  "deep_clean": false,
  "items_to_clean": [
    "events.jsonl",
    "memory/*.md",
    "__pycache__",
    "*.bak",
    "task_executions.jsonl"
  ]
}
```

## 自动化集成

### 1. 每日自动清理（Cron）

```bash
# 每天凌晨 3 点清理
0 3 * * * cd /path/to/aios && python cleanup.py --days 7
```

### 2. Heartbeat 集成

在 `heartbeat_v5.py` 中添加：
```python
# 每天凌晨 3 点清理
if current_hour == 3 and current_minute == 0:
    run_cleanup()
```

### 3. Maintenance Agent 集成

Maintenance Agent 在每日维护时自动调用。

## 归档位置

```
aios/archives/
├── events-2026-03.jsonl.gz      # 3月事件归档
├── memory-2026-03.tar.gz        # 3月日志归档
├── tasks-2026-03.jsonl.gz       # 3月任务归档
└── spawns-2026-03.jsonl.gz      # 3月spawn归档
```

## 恢复归档数据

### 1. 解压事件归档

```bash
gunzip -c archives/events-2026-03.jsonl.gz >> events.jsonl
```

### 2. 解压日志归档

```bash
tar -xzf archives/memory-2026-03.tar.gz -C memory/
```

## 最佳实践

1. **定期清理** - 每天自动清理，保持系统轻量
2. **保留策略** - 保留 7 天数据（平衡空间和可追溯性）
3. **归档优先** - 旧数据归档而非删除
4. **干运行测试** - 首次使用先 `--dry-run` 预览
5. **监控空间** - 定期检查磁盘使用率

## 故障排查

### 清理失败

```bash
# 检查磁盘空间
df -h

# 检查文件权限
ls -la aios/

# 查看清理日志
cat aios/cleanup.log
```

### 误删数据

```bash
# 从归档恢复
gunzip -c archives/events-2026-03.jsonl.gz >> events.jsonl

# 从备份恢复
python backup.py --restore 2026-03-04
```

## 未来改进（v1.1）

- [ ] 智能清理（基于使用频率）
- [ ] 压缩比优化（更高压缩率）
- [ ] 选择性恢复（只恢复特定数据）
- [ ] 清理报告（详细统计和建议）
- [ ] Webhook 通知（清理完成通知）

---

**版本：** v1.0.0  
**最后更新：** 2026-03-04  
**维护者：** 小九 + 珊瑚海
