---
name: backup-restore-manager
version: 1.0.0
description: 把"备份 + 恢复演练 + MRS 检查"统一成连续性主骨。一键备份、MRS 检查、隔离恢复、自动生成 drill report。
---

# Backup Restore Manager

## 目标

把"备份 + 恢复演练 + MRS 检查"统一成连续性主骨。

## 使用方式

### 一键备份

```bash
cd C:\Users\A\.openclaw\workspace\skills\backup-restore-manager
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 manager.py backup
```

### MRS 检查

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 manager.py check-mrs
```

### 隔离恢复 + Drill

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 manager.py drill
```

### 完整流程（备份 → MRS检查 → 隔离恢复 → Drill报告）

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 manager.py full
```

## 输出

| 文件 | 说明 |
|------|------|
| backup_metadata.json | 备份元数据 |
| mrs_check_report.md | MRS 检查报告 |
| restore_drill_report.md | 恢复演练报告 |

## 固定判定句式

```
最终结论：[可恢复 / 部分可恢复 / 不可恢复]
是否具备立即用于故障恢复的条件：[是 / 否]
缺失项：[列表]
下一步补项：[列表]
```

## 验收标准

1. 备份必须通过 --check-mrs
2. 恢复必须在隔离环境进行
3. 恢复后 agents / memory / heartbeat 可用
4. 报告能明确判定恢复等级
5. 可输出"是否具备立即故障恢复条件"

---

**版本：** 1.0.0
**最后更新：** 2026-03-11
