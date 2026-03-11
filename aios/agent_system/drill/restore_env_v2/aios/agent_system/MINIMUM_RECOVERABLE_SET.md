# 最小可恢复集合（Minimum Recoverable Set）

**版本：** v1.0  
**创建时间：** 2026-03-11  
**维护者：** 小九 + 珊瑚海

---

## 定义

最小可恢复集合（MRS）是指：**从零重建 AIOS 系统所需的最小文件集合**。

缺少任何一项，系统无法判定为"可恢复"。

---

## 分层结构

### 第一层：运行时数据（必须）

这些文件记录系统的实时状态，缺少它们会导致状态丢失。

**必须备份：**
- `agents.json` - Agent 注册表和状态
- `lessons.json` - 经验教训库
- `task_queue.jsonl` - 任务队列
- `task_executions.jsonl` - 任务执行历史
- `spawn_pending.jsonl` - 待执行的 spawn 请求
- `spawn_results.jsonl` - spawn 执行结果
- `events.jsonl` - 系统事件日志
- `metrics.jsonl` - 系统指标
- `memory/selflearn-state.json` - 学习 Agent 状态
- `memory/heartbeat-state.json` - 心跳状态

**验收标准：**
- 恢复后能看到历史任务
- 恢复后能看到 Agent 状态
- 恢复后能看到经验教训

---

### 第二层：配置与代码（必须）

这些文件定义系统的行为逻辑，缺少它们会导致系统无法按原设计工作。

**必须备份：**
- `heartbeat_v5.py` - 当前生产心跳脚本
- `learning_agents.py` - 学习 Agent 配置和注册
- `aios.py` - AIOS 主入口
- `task_executor.py` - 任务执行器
- `scheduler.py` - 调度器
- `memory_server.py` - 记忆服务器
- `config/` - 配置文件目录（如果存在）

**验收标准：**
- 恢复后 heartbeat 能按原版本运行
- 恢复后学习 Agent 能正常注册
- 恢复后核心链路能按原逻辑执行

---

### 第三层：记忆与状态（必须）

这些文件记录系统的长期记忆和认知主索引，缺少它们会导致认知断层。

**必须备份：**
- `MEMORY.md` - 长期记忆主索引
- `memory/YYYY-MM-DD.md` - 每日记忆（最近 7 天）
- `memory/lessons.json` - 经验教训（与第一层重复，但归类不同）
- `memory/preferences.json` - 用户偏好（如果存在）

**验收标准：**
- 恢复后能看到长期记忆
- 恢复后能看到最近 7 天的日常记录
- 恢复后能看到用户偏好

---

### 第四层：恢复脚本/说明（必须）

这些文件指导如何恢复系统，缺少它们会导致恢复过程不可复现。

**必须备份：**
- `backup.py` - 备份脚本
- `restore.py` - 恢复脚本
- `MINIMUM_RECOVERABLE_SET.md` - 本文件
- `RESTORE_DRILL_REPORT.md` - 最近一次恢复演练报告

**验收标准：**
- 恢复后能看到备份/恢复脚本
- 恢复后能看到恢复指南
- 恢复后能看到最近一次演练结果

---

## 可选增强项

这些文件不影响系统基本恢复，但能提升恢复后的完整性。

**可选备份：**
- `docs/` - 文档目录
- `dashboard/` - Dashboard 代码
- `tests/` - 测试代码
- `memory/YYYY-MM-DD.md`（7 天以前的）
- `heartbeat_v*.py`（旧版本）
- `reports/` - 报表类文件

---

## 验收标准

### 数据恢复（通过）
- 所有 `.json` 和 `.jsonl` 文件存在
- 文件内容可解析
- 数据结构完整

### 状态恢复（通过）
- Agent 状态可读取
- 任务队列可读取
- 学习状态可读取

### 最小运行恢复（通过）
- 能启动 heartbeat
- 能执行一次心跳
- 能通过 smoke test

### 完整配置恢复（通过）
- 关键 Python 脚本存在
- 配置文件存在
- 恢复后链路与原配置一致

### 生产等价恢复（通过）
- 恢复后系统行为与原系统一致
- 恢复后能继续执行任务
- 恢复后能继续学习和改进

---

## 使用方式

### 备份时
```bash
python backup.py --check-mrs
```
备份脚本会检查 MRS 清单，确保所有必须项都被备份。

### 恢复时
```bash
python restore.py --verify-mrs
```
恢复脚本会验证 MRS 清单，确保所有必须项都被恢复。

### 演练时
```bash
python restore_drill.py --mrs-only
```
只验证 MRS 清单的完整性，不执行完整恢复。

---

## 维护规则

1. **每次新增核心脚本时，必须更新 MRS 清单**
2. **每次 Restore Drill 后，必须更新 MRS 清单**
3. **每次发现备份缺口时，必须更新 MRS 清单**
4. **MRS 清单本身必须被备份**

---

## 版本历史

- v1.0 (2026-03-11) - 初始版本，基于 Restore Drill v1.0 的发现
