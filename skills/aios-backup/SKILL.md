---
name: aios-backup
version: 1.0.0
description: Backup critical AIOS data (events, metrics, agents, lessons). Use during maintenance or before major changes.
---

# AIOS Backup v1.0

自动备份 AIOS 核心数据，支持增量备份和自动清理。

## 核心功能

- ✅ **完整备份** - 备份所有核心数据文件
- ✅ **增量备份** - 只备份变化的文件
- ✅ **自动清理** - 保留最近 N 天的备份
- ✅ **压缩存储** - 自动压缩旧备份（节省空间）
- ✅ **恢复功能** - 从备份恢复数据

## 使用方法

### 1. 完整备份

```bash
python backup.py
```

### 2. 增量备份

```bash
python backup.py --incremental
```

### 3. 自动清理旧备份

```bash
python backup.py --cleanup --keep-days 7
```

### 4. 恢复备份

```bash
python backup.py --restore 2026-03-04
```

## 输出格式

标准 Skill 格式：
```json
{
  "ok": true,
  "result": {
    "backup_dir": "C:/Users/A/.openclaw/workspace/aios/backups/2026-03-04",
    "backed_up_count": 4,
    "backed_up_files": [
      "events.jsonl",
      "metrics_history.jsonl",
      "agents.json",
      "lessons.json"
    ],
    "backup_size": "2.5 MB",
    "compression": "gzip"
  },
  "evidence": ["backups/2026-03-04/"],
  "next": []
}
```

## 备份内容

### 核心数据（每次备份）
1. **events.jsonl** - 所有系统事件
2. **metrics_history.jsonl** - Evolution Score 历史
3. **agents.json** - Agent 状态
4. **lessons.json** - 学习到的教训

### 扩展数据（可选）
5. **task_queue.jsonl** - 任务队列
6. **task_executions.jsonl** - 任务执行历史
7. **spawn_requests.jsonl** - Spawn 请求
8. **experience_library.jsonl** - 经验库

## 备份位置

```
aios/backups/
├── 2026-03-04/          # 今天的备份
│   ├── events.jsonl
│   ├── metrics_history.jsonl
│   ├── agents.json
│   └── lessons.json
├── 2026-03-03/          # 昨天的备份
└── 2026-03-02.tar.gz    # 压缩的旧备份
```

## 自动化集成

### 1. 每日自动备份（Cron）

```bash
# 每天凌晨 2 点备份
0 2 * * * cd /path/to/aios && python backup.py --incremental --cleanup --keep-days 7
```

### 2. Heartbeat 集成

在 `heartbeat_v5.py` 中添加：
```python
# 每天凌晨 2 点备份
if current_hour == 2 and current_minute == 0:
    run_backup()
```

### 3. Maintenance Agent 集成

Maintenance Agent 在每日维护时自动调用。

## 恢复流程

### 1. 查看可用备份

```bash
python backup.py --list
```

输出：
```
[BACKUPS] Available backups:
  - 2026-03-04 (2.5 MB) - Latest
  - 2026-03-03 (2.4 MB)
  - 2026-03-02 (2.3 MB, compressed)
```

### 2. 恢复指定日期

```bash
python backup.py --restore 2026-03-04
```

### 3. 验证恢复

```bash
python backup.py --verify 2026-03-04
```

## 配置选项

在 `backup_config.json` 中配置：

```json
{
  "backup_dir": "aios/backups",
  "keep_days": 7,
  "compress_after_days": 3,
  "incremental": true,
  "files_to_backup": [
    "events.jsonl",
    "metrics_history.jsonl",
    "agents.json",
    "lessons.json",
    "task_queue.jsonl",
    "task_executions.jsonl"
  ]
}
```

## 最佳实践

1. **每日备份** - 设置 Cron 任务每天自动备份
2. **保留策略** - 保留最近 7 天的完整备份
3. **压缩旧备份** - 3 天后自动压缩（节省 70% 空间）
4. **定期验证** - 每周验证一次备份完整性
5. **重大变更前** - 手动执行完整备份

## 故障排查

### 备份失败

```bash
# 检查磁盘空间
df -h

# 检查文件权限
ls -la aios/backups/

# 查看备份日志
cat aios/backups/backup.log
```

### 恢复失败

```bash
# 验证备份完整性
python backup.py --verify 2026-03-04

# 手动恢复
cp aios/backups/2026-03-04/* aios/agent_system/
```

## 未来改进（v1.1）

- [ ] 远程备份（S3/云存储）
- [ ] 加密备份（敏感数据保护）
- [ ] 差异备份（只备份变化部分）
- [ ] 自动恢复测试（定期验证备份可用性）
- [ ] Webhook 通知（备份成功/失败通知）

---

**版本：** v1.0.0  
**最后更新：** 2026-03-04  
**维护者：** 小九 + 珊瑚海
