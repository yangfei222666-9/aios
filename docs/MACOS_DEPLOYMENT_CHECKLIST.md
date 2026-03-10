# macOS 部署检查清单

**日期：** 2026-03-10  
**版本：** v1.0

---

## ✅ 部署前检查

### 系统环境
- [ ] macOS 版本 >= 12.0 (Monterey)
- [ ] 可用磁盘空间 >= 20GB
- [ ] 网络连接稳定
- [ ] 管理员权限

### 必需工具
- [ ] Homebrew 已安装
- [ ] Python 3.12 已安装
- [ ] Node.js 18+ 已安装
- [ ] Git 已安装
- [ ] OpenClaw 已安装

### API Keys
- [ ] Anthropic API Key 已准备
- [ ] OpenAI API Key 已准备（可选）
- [ ] Telegram Bot Token 已准备（可选）

---

## ✅ 部署步骤

### 1. 基础环境
- [ ] Homebrew 安装完成
- [ ] Python 3.12 安装完成
- [ ] Node.js 安装完成
- [ ] OpenClaw 全局安装完成

### 2. 工作目录
- [ ] `~/.openclaw/workspace` 已创建
- [ ] 目录权限正确 (700)

### 3. AIOS 代码
- [ ] AIOS 代码已同步
- [ ] Git 仓库已克隆/更新
- [ ] 所有文件完整

### 4. Python 环境
- [ ] 虚拟环境已创建
- [ ] 依赖已安装 (requirements.txt)
- [ ] 核心包可导入 (anthropic, openai, etc.)

### 5. 核心文件
- [ ] AGENTS.md 已复制/创建
- [ ] SOUL.md 已复制/创建
- [ ] USER.md 已复制/创建
- [ ] TOOLS.md 已复制/创建
- [ ] IDENTITY.md 已复制/创建
- [ ] HEARTBEAT.md 已复制/创建
- [ ] MEMORY.md 已复制/创建
- [ ] memory/ 目录已同步

### 6. OpenClaw 配置
- [ ] Gateway 已启动
- [ ] API Keys 已配置
- [ ] 默认模型已设置
- [ ] Telegram 已配置（可选）

### 7. Memory Server
- [ ] memory_server.py 可运行
- [ ] 端口 7788 可访问
- [ ] 模型已加载
- [ ] 自启动已配置（可选）

### 8. 路径修复
- [ ] Python 路径已更新 (Windows → macOS)
- [ ] 所有硬编码路径已修复
- [ ] 使用 Path(__file__) 自动适配

---

## ✅ 功能测试

### Memory Server
```bash
# 启动测试
cd ~/.openclaw/workspace/aios/agent_system
python3.12 memory_server.py &

# 状态检查
curl http://localhost:7788/status

# 预期输出
{"status": "ok", "model_loaded": true, "port": 7788}
```
- [ ] Memory Server 启动成功
- [ ] 状态检查通过
- [ ] 模型加载成功

### AIOS 系统
```bash
# 状态检查
cd ~/.openclaw/workspace/aios/agent_system
python3.12 aios.py status

# 预期输出
AIOS Status:
  Evolution Score: XX.XX
  Total Tasks: X
  Completed: X
  Failed: X
  Pending: X
  Health: GOOD/WARNING/CRITICAL
```
- [ ] AIOS 状态正常
- [ ] Evolution Score 可读取
- [ ] 任务统计正确

### Heartbeat
```bash
# 心跳测试
cd ~/.openclaw/workspace/aios/agent_system
python3.12 heartbeat_v5.py

# 预期输出
AIOS Heartbeat v5.0 Started
[QUEUE] No pending tasks
[HEALTH] Health Score: XX.XX/100
HEARTBEAT_OK (no_tasks, health=XX)
```
- [ ] Heartbeat 运行成功
- [ ] 队列检查正常
- [ ] 健康度计算正确

### OpenClaw Gateway
```bash
# 状态检查
openclaw status

# 预期输出
Gateway: running
Model: claude-sonnet-4-6
Sessions: X active
```
- [ ] Gateway 运行中
- [ ] 模型配置正确
- [ ] 会话管理正常

### Telegram（可选）
- [ ] Bot 可接收消息
- [ ] Bot 可发送回复
- [ ] 语音消息转写正常
- [ ] 命令执行正常

---

## ✅ 性能优化

### Memory Server
- [ ] BATCH_SIZE 已调整（根据内存）
- [ ] MAX_WORKERS 已调整（根据 CPU）
- [ ] 模型已预下载到本地

### 日志管理
- [ ] 日志轮转已配置
- [ ] 旧日志自动清理
- [ ] 日志大小限制已设置

### 自启动服务
- [ ] Memory Server LaunchAgent 已配置
- [ ] OpenClaw Gateway 自启动已启用
- [ ] 服务状态可查询

---

## ✅ 安全检查

### API Keys
- [ ] 使用环境变量存储
- [ ] 不在代码中硬编码
- [ ] 不提交到 Git

### 文件权限
- [ ] MEMORY.md 权限 600
- [ ] memory/*.md 权限 600
- [ ] agent_system/ 权限 700

### 网络安全
- [ ] Memory Server 只监听 127.0.0.1
- [ ] 不暴露到公网
- [ ] 防火墙规则正确

---

## ✅ 数据同步

### Windows → macOS
- [ ] AIOS 代码已同步
- [ ] 核心文件已同步
- [ ] memory/ 目录已同步
- [ ] 配置文件已同步

### 路径差异处理
- [ ] Python 路径已修复
- [ ] 工作目录路径已更新
- [ ] 所有硬编码路径已替换

### 平台特定配置
- [ ] TOOLS.md 已更新（macOS 路径）
- [ ] 应用路径已更新
- [ ] SSH 配置已更新

---

## ✅ 文档和备份

### 文档
- [ ] MACOS_DEPLOYMENT.md 已阅读
- [ ] AGENTS.md 已理解
- [ ] SOUL.md 已理解
- [ ] HEARTBEAT.md 已理解

### 备份
- [ ] 首次部署快照已创建
- [ ] 备份策略已制定
- [ ] 恢复流程已测试

---

## ✅ 下一步行动

### 立即执行
- [ ] 更新 USER.md（macOS 特定信息）
- [ ] 更新 TOOLS.md（macOS 应用路径）
- [ ] 配置 Telegram（如需要）
- [ ] 设置定时任务

### 短期计划
- [ ] 安装常用 Skills (apple-notes, apple-reminders, imsg)
- [ ] 配置 Heartbeat 定时运行
- [ ] 测试所有核心功能
- [ ] 建立 Windows ↔ macOS 同步流程

### 长期维护
- [ ] 定期备份 memory/ 目录
- [ ] 定期更新 OpenClaw
- [ ] 定期同步 Windows 和 macOS 数据
- [ ] 监控系统健康度

---

## 🐛 常见问题快速参考

### Memory Server 无法启动
```bash
# 检查日志
tail -f ~/.openclaw/workspace/aios/agent_system/memory_server.log

# 检查端口
lsof -i :7788

# 重启
pkill -f memory_server.py
python3.12 memory_server.py &
```

### OpenClaw Gateway 无法启动
```bash
# 查看日志
openclaw gateway logs

# 重启
openclaw gateway restart

# 检查配置
openclaw gateway config.get
```

### Python 依赖问题
```bash
# 重建虚拟环境
cd ~/.openclaw/workspace/aios
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 路径问题
```bash
# 检查 PYTHONPATH
echo $PYTHONPATH

# 临时设置
export PYTHONPATH=~/.openclaw/workspace/aios:$PYTHONPATH

# 永久设置（添加到 ~/.zshrc）
echo 'export PYTHONPATH=~/.openclaw/workspace/aios:$PYTHONPATH' >> ~/.zshrc
```

---

## 📊 部署完成度

**总进度：** _____ / 100

- 基础环境: _____ / 15
- AIOS 代码: _____ / 15
- 核心文件: _____ / 15
- 功能测试: _____ / 20
- 性能优化: _____ / 10
- 安全检查: _____ / 10
- 数据同步: _____ / 10
- 文档备份: _____ / 5

---

**部署人员：** _____________  
**部署日期：** _____________  
**验收日期：** _____________  
**备注：** _____________

---

**完成标志：** 所有核心功能测试通过，系统稳定运行 24 小时以上。

🎉 祝部署顺利！
