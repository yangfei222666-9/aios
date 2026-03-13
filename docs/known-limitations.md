# 已知边界与限制

## 1. 手动 sessions_spawn 不自动回写

**现象：**
- 通过 `sessions_spawn` 手动触发的任务，执行成功但不会自动写入 `task_executions.jsonl`
- 只有通过 Task Queue 提交的任务才有自动回写机制

**影响范围：**
- Bug_Hunter 等手动触发的 Agent 任务
- 所有绕过 Task Queue 的直接 spawn

**解决方案（待实施）：**
1. 统一入口：所有任务都通过 Task Queue 提交
2. 或者：在 sessions_spawn 回调中增加手动回写逻辑

**当前状态：** 已知问题，不影响核心能力验证

---

## 2. Windows 文件关联弹窗

**现象：**
- 每次 spawn subagent 时，Windows 弹出 `.jsonl` 文件关联选择窗口
- 需要手动清理 `OpenWith` 进程

**根本原因：**
- `.jsonl` 文件没有默认打开程序关联

**临时方案：**
- 手动清理：`Get-Process OpenWith -ErrorAction SilentlyContinue | Stop-Process -Force`

**根本方案（需管理员权限）：**
- 设置 `.jsonl` 默认关联到记事本

**当前状态：** 已知问题，临时方案可用

---

**最后更新：** 2026-03-13  
**记录者：** 小九
