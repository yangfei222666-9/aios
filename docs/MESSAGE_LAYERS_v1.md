# 消息分层规则 v1

**生效日期：** 2026-03-14

---

## 三层分类

### Layer 1：主线消息（发给珊瑚海）

**触发条件：**
- 任务交付（pending_review）
- 需要决策的问题
- 审查意见回复
- 主动汇报（珊瑚海要求时）

**约束：** 主线消息不应被后台任务占用。

**格式：** 正常对话

---

### Layer 2：后台消息（静默执行，不通知）

**触发条件：**
- 定时任务正常完成（MONITOR_OK / HEALING_OK / ANOMALY_OK / BACKUP_OK）
- 日常维护（清理、备份、优化）
- 学习 Agent 输出
- 系统健康度 ≥ 80

**处理方式：** 
- cron delivery mode = none
- 结果写入日志文件，不发 Telegram

---

### Layer 3：告警消息（条件触发，必须通知）

**触发条件：**
- 连续失败 ≥ 3 次
- 系统健康度 < 60（CRITICAL）
- 安全事件
- 任务执行失败需人工介入
- 重要 GitHub 更新（OpenClaw 新版本等）

**格式：** 带 ⚠️ 或 🚨 前缀，一句话说清问题。必要时说明是否需要人工介入。

---

## 已落地措施

- 2026-03-14：26 个 cron 任务 delivery mode 从 announce 改为 none
- 保留 announce 的 9 个任务均属于 Layer 1 或 Layer 3

---

## 免打扰时段

- 23:00 - 08:00：只发 Layer 3（CRITICAL）
- 其他时间：Layer 1 + Layer 3

---

**版本：** v1
