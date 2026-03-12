# 本地电脑保留清单

**电脑：** DESKTOP-7V5I2V2  
**日期：** 2026-03-12  
**状态：** ✅ 完整备份已完成

---

## 1. 核心系统文件

### 太极OS 主目录
- **路径：** `C:\Users\A\.openclaw\workspace\aios\`
- **状态：** ✅ 已备份（34 个文件）
- **最新备份：** `C:\Users\A\.openclaw\workspace\aios\backups\2026-03-12\`

### 关键配置
- `agents.json` - 30 个 Agent 配置
- `lessons.json` - 系统经验教训
- `learning_agents.py` - 学习 Agent 定义
- `heartbeat_v5.py` - 心跳主流程

### 运行时数据
- `task_queue.jsonl` - 任务队列
- `task_executions.jsonl` - 执行记录
- `spawn_pending.jsonl` - 待处理 spawn 请求
- `spawn_results.jsonl` - spawn 执行结果
- `alerts.jsonl` - 告警记录

---

## 2. 记忆文件

### 长期记忆
- **MEMORY.md** - 小九的长期记忆（20KB+）
- **USER.md** - 珊瑚海的个人信息
- **SOUL.md** - 系统人格定义
- **IDENTITY.md** - 小九的身份
- **TOOLS.md** - 本地工具配置

### 每日记忆
- `memory/2026-03-12.md` - 今日记录
- `memory/2026-03-11.md` - 昨日记录
- `memory/2026-03-10.md` - 前日记录
- 以及所有研究报告和专题笔记

---

## 3. 开发环境

### Python 环境
- **版本：** Python 3.12.10
- **路径：** `C:\Program Files\Python312\python.exe`
- **核心依赖：**
  - torch 2.6.0+cu128
  - sentence-transformers 3.4.1
  - lancedb 0.20.0
  - fastapi 0.115.6
  - uvicorn 0.34.0

### CUDA 环境
- **版本：** CUDA 12.8
- **GPU：** RTX 5070 Ti
- **状态：** ✅ 可用

---

## 4. 服务与进程

### Memory Server
- **端口：** 7788
- **脚本：** `memory_server.py`
- **启动命令：**
  ```powershell
  cd C:\Users\A\.openclaw\workspace\aios\agent_system
  & "C:\Program Files\Python312\python.exe" memory_server.py
  ```

### Dashboard v3.4
- **端口：** 8888
- **路径：** `C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4\`
- **启动命令：**
  ```powershell
  cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4
  & "C:\Program Files\Python312\python.exe" server.py
  ```

### Dashboard v4.0
- **端口：** 8889
- **路径：** `C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v4.0\`
- **启动命令：**
  ```powershell
  cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v4.0
  & "C:\Program Files\Python312\python.exe" server.py
  ```

---

## 5. 应用程序

### QQ音乐
- **路径：** `E:\QQMusic\QQMusic.exe`
- **状态：** ✅ 已配置

---

## 6. 备份策略

### 自动备份
- **频率：** 每日一次（通过 Heartbeat）
- **脚本：** `backup.py`
- **位置：** `C:\Users\A\.openclaw\workspace\aios\backups\`

### 恢复验证
- **脚本：** `restore.py`
- **最近演练：** 2026-03-11（Restore Drill v1.1）
- **结果：** ✅ 生产等价恢复验证通过

### MRS 标准
- **文档：** `MINIMUM_RECOVERABLE_SET.md`
- **状态：** ✅ 完整

---

## 7. 文档与知识库

### 核心文档
- `docs/TAIJIOS_PRINCIPLES.md` - 太极OS 五则
- `docs/SKILL_AUTO_CREATION_MVP.md` - Skill 自动创建设计
- `docs/STATUS_MODEL_MIGRATION_FINAL.md` - 状态模型迁移
- `DEV_SETUP.md` - 开发环境配置
- `QUICK_REFERENCE.md` - 快速参考

### 研究报告
- `memory/2026-03-09-hermes-skill-research.md`
- `memory/2026-03-10-rabbit-os-research.md`
- `memory/2026-03-10-memory-research.md`
- 以及所有其他研究笔记

---

## 8. VS Code 配置

### 工作区
- **文件：** `taijios.code-workspace`
- **调试配置：** `.vscode/launch.json`（8 个配置）
- **任务配置：** `.vscode/tasks.json`（8 个任务）
- **编辑器配置：** `.vscode/settings.json`

---

## 9. 快速启动脚本

### start.ps1
- **路径：** `C:\Users\A\.openclaw\workspace\aios\agent_system\start.ps1`
- **功能：**
  - 一键启动所有服务
  - 单独启动各个服务
  - 验证开发环境

---

## 10. 保留检查清单

在迁移或重装系统前，确保以下内容已备份：

- [ ] 运行最新的 `backup.py`
- [ ] 确认备份目录完整（34+ 文件）
- [ ] 导出 Python 环境（`pip freeze > requirements.txt`）
- [ ] 备份 VS Code 配置（`.vscode/` 目录）
- [ ] 备份所有 `memory/` 文件
- [ ] 备份 `MEMORY.md` 和其他核心 MD 文件
- [ ] 记录所有服务端口和启动命令
- [ ] 记录应用程序路径（QQ音乐等）
- [ ] 备份 OpenClaw 配置（如果有）

---

## 11. 恢复步骤（如需迁移）

1. **安装 Python 3.12.10**
2. **安装 CUDA 12.8**（如果有 GPU）
3. **恢复 workspace 目录**
   ```powershell
   cd C:\Users\A\.openclaw\workspace\aios\agent_system
   & "C:\Program Files\Python312\python.exe" restore.py
   ```
4. **安装 Python 依赖**
   ```powershell
   pip install -r requirements.txt
   ```
5. **验证恢复**
   ```powershell
   & "C:\Program Files\Python312\python.exe" verify_dev_env.py
   ```
6. **启动服务**
   ```powershell
   .\start.ps1 -Action all
   ```

---

**最后更新：** 2026-03-12  
**维护者：** 小九 + 珊瑚海
