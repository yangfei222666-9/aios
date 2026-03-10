# MacBook 部署指南 - 太极OS (TaijiOS)

**版本：** v1.0  
**日期：** 2026-03-10  
**目标：** 在 MacBook 上完整部署太极OS

---

## 📋 部署前检查清单

### 系统要求
- macOS 12.0+ (Monterey 或更高)
- Python 3.12+
- Node.js 18+
- 至少 20GB 可用空间
- 稳定的网络连接

### 必需工具
- Homebrew
- Git
- Docker Desktop (可选，用于 VM 功能)

---

## 🚀 快速部署（推荐）

### 1. 安装基础环境

```bash
# 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 3.12
brew install python@3.12

# 安装 Node.js
brew install node

# 验证版本
python3.12 --version
node --version
npm --version
```

### 2. 安装 OpenClaw

```bash
# 全局安装 OpenClaw
npm install -g openclaw-cn

# 验证安装
openclaw --version
```

### 3. 初始化工作区

```bash
# 创建工作目录
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 克隆 AIOS 项目（如果从 Windows 迁移）
# 方式 1: 从 GitHub 克隆
git clone <your-aios-repo-url> aios

# 方式 2: 从 Windows 同步（见下方"数据迁移"章节）
```

### 4. 安装 Python 依赖

```bash
cd ~/.openclaw/workspace/aios

# 创建虚拟环境（推荐）
python3.12 -m venv venv
source venv/bin/activate

# 安装核心依赖
pip install --upgrade pip
pip install -r requirements.txt

# 如果没有 requirements.txt，手动安装核心包
pip install anthropic openai requests pyyaml jsonlines sentence-transformers chromadb
```

### 5. 配置 OpenClaw

```bash
# 启动 Gateway
openclaw gateway start

# 首次运行会引导配置
# 需要配置：
# - Anthropic API Key
# - 默认模型
# - Telegram Bot Token（可选）
```

### 6. 部署核心文件

```bash
cd ~/.openclaw/workspace

# 从 Windows 复制或创建以下文件：
# - AGENTS.md
# - SOUL.md
# - USER.md
# - TOOLS.md
# - IDENTITY.md
# - HEARTBEAT.md
# - MEMORY.md
# - memory/ 目录
```

### 7. 启动 Memory Server

```bash
cd ~/.openclaw/workspace/aios/agent_system

# 后台启动 Memory Server
nohup python3.12 memory_server.py > memory_server.log 2>&1 &

# 验证启动
curl http://localhost:7788/status
```

### 8. 测试系统

```bash
# 测试 Heartbeat
cd ~/.openclaw/workspace/aios/agent_system
python3.12 heartbeat_v5.py

# 测试 Agent
python3.12 aios.py status

# 测试 Memory
python3.12 -c "from memory_engine import MemoryEngine; m = MemoryEngine(); print(m.query('test'))"
```

---

## 📦 数据迁移（从 Windows）

### 方式 1: Git 同步（推荐）

```bash
# 在 Windows 上提交所有更改
cd C:\Users\A\.openclaw\workspace
git add .
git commit -m "Prepare for macOS deployment"
git push

# 在 MacBook 上克隆
cd ~/.openclaw/workspace
git clone <your-repo-url> aios
```

### 方式 2: 直接复制

```bash
# 使用 rsync 或 scp 从 Windows 复制
# 需要在 Windows 上启用 SSH 或使用共享文件夹

# 关键目录：
# - aios/
# - memory/
# - AGENTS.md, SOUL.md, USER.md, TOOLS.md, IDENTITY.md, HEARTBEAT.md, MEMORY.md
```

### 方式 3: 云同步

```bash
# 使用 iCloud Drive / Dropbox / OneDrive
# 将 workspace 放入同步文件夹
# 在 MacBook 上等待同步完成
```

---

## 🔧 平台差异处理

### 路径差异

**Windows:**
```
C:\Users\A\.openclaw\workspace\aios\agent_system
```

**macOS:**
```
/Users/<username>/.openclaw/workspace/aios/agent_system
```

**解决方案：** 使用 `Path(__file__).resolve()` 自动适配

### 命令差异

| 功能 | Windows (PowerShell) | macOS (Bash/Zsh) |
|------|---------------------|------------------|
| 环境变量 | `$env:VAR=value` | `export VAR=value` |
| 命令分隔 | `;` | `;` 或 `&&` |
| Python 路径 | `C:\Program Files\Python312\python.exe` | `python3.12` 或 `/usr/local/bin/python3.12` |
| 后台运行 | `Start-Process` | `nohup ... &` |

### 编码差异

macOS 默认 UTF-8，无需特殊配置。

Windows 需要：
```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING='utf-8'
```

macOS 不需要这些。

---

## 🛠️ macOS 特有配置

### 1. 开机自启动 Memory Server

创建 LaunchAgent：

```bash
# 创建配置文件
cat > ~/Library/LaunchAgents/com.taijios.memory-server.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taijios.memory-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3.12</string>
        <string>/Users/<username>/.openclaw/workspace/aios/agent_system/memory_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/<username>/.openclaw/workspace/aios/agent_system/memory_server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/<username>/.openclaw/workspace/aios/agent_system/memory_server_error.log</string>
</dict>
</plist>
EOF

# 替换 <username> 为实际用户名
sed -i '' "s/<username>/$(whoami)/g" ~/Library/LaunchAgents/com.taijios.memory-server.plist

# 加载服务
launchctl load ~/Library/LaunchAgents/com.taijios.memory-server.plist

# 验证
launchctl list | grep memory-server
```

### 2. 开机自启动 OpenClaw Gateway

```bash
# OpenClaw 自带 launchd 配置
openclaw gateway install

# 验证
launchctl list | grep openclaw
```

### 3. 配置 Telegram（可选）

```bash
# 编辑 OpenClaw 配置
openclaw gateway config.get > config.json

# 添加 Telegram 配置
# 参考 Windows 上的配置

openclaw gateway config.apply config.json
```

---

## 🧪 验证部署

### 完整测试流程

```bash
# 1. 测试 Python 环境
python3.12 --version
python3.12 -c "import anthropic, openai, sentence_transformers; print('OK')"

# 2. 测试 Memory Server
curl http://localhost:7788/status

# 3. 测试 AIOS
cd ~/.openclaw/workspace/aios/agent_system
python3.12 aios.py status

# 4. 测试 Heartbeat
python3.12 heartbeat_v5.py

# 5. 测试 OpenClaw
openclaw status

# 6. 测试 Telegram（如果配置了）
# 发送消息到 Bot，看是否收到回复
```

### 预期输出

**Memory Server:**
```json
{"status": "ok", "model_loaded": true, "port": 7788}
```

**AIOS Status:**
```
AIOS Status:
  Evolution Score: 85.71
  Total Tasks: 7
  Completed: 6
  Failed: 1
  Pending: 0
  Health: GOOD
```

**Heartbeat:**
```
AIOS Heartbeat v5.0 Started
[QUEUE] No pending tasks
[HEALTH] Health Score: 85.71/100
HEARTBEAT_OK (no_tasks, health=86)
```

---

## 🐛 常见问题

### 1. Memory Server 启动失败

**症状：** `curl http://localhost:7788/status` 连接失败

**解决：**
```bash
# 检查日志
tail -f ~/.openclaw/workspace/aios/agent_system/memory_server.log

# 常见原因：
# - 端口被占用 → 修改 memory_server.py 中的端口
# - 模型下载失败 → 检查网络，手动下载模型
# - 依赖缺失 → pip install sentence-transformers chromadb
```

### 2. OpenClaw Gateway 无法启动

**症状：** `openclaw gateway start` 报错

**解决：**
```bash
# 查看日志
openclaw gateway logs

# 常见原因：
# - 配置文件错误 → openclaw gateway config.get 检查
# - 端口冲突 → 修改配置中的端口
# - 权限问题 → sudo openclaw gateway start
```

### 3. Python 依赖冲突

**症状：** `ModuleNotFoundError` 或版本冲突

**解决：**
```bash
# 使用虚拟环境隔离
cd ~/.openclaw/workspace/aios
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 或使用 conda
conda create -n taijios python=3.12
conda activate taijios
pip install -r requirements.txt
```

### 4. 路径问题

**症状：** 找不到文件或模块

**解决：**
```bash
# 检查所有脚本中的路径
# 确保使用 Path(__file__).resolve() 而不是硬编码路径

# 临时解决：设置 PYTHONPATH
export PYTHONPATH=~/.openclaw/workspace/aios:$PYTHONPATH
```

---

## 📊 性能优化

### 1. Memory Server 优化

```python
# memory_server.py 中调整
BATCH_SIZE = 32  # 根据 MacBook 内存调整
MAX_WORKERS = 4  # 根据 CPU 核心数调整
```

### 2. 模型缓存

```bash
# 预下载模型到本地
python3.12 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 3. 日志轮转

```bash
# 添加 logrotate 配置（macOS 使用 newsyslog）
sudo nano /etc/newsyslog.d/taijios.conf

# 内容：
# /Users/<username>/.openclaw/workspace/aios/agent_system/*.log 644 7 100 * J
```

---

## 🔐 安全建议

### 1. API Key 管理

```bash
# 使用环境变量而不是硬编码
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# 添加到 ~/.zshrc 或 ~/.bash_profile
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
```

### 2. 文件权限

```bash
# 限制敏感文件权限
chmod 600 ~/.openclaw/workspace/MEMORY.md
chmod 600 ~/.openclaw/workspace/memory/*.md
chmod 700 ~/.openclaw/workspace/aios/agent_system
```

### 3. 防火墙配置

```bash
# 限制 Memory Server 只监听本地
# memory_server.py 中：
# app.run(host='127.0.0.1', port=7788)  # 不要用 0.0.0.0
```

---

## 📚 下一步

部署完成后：

1. **阅读文档**
   - `AGENTS.md` - 了解系统规则
   - `SOUL.md` - 了解 AI 助手的性格
   - `HEARTBEAT.md` - 了解自动任务机制

2. **配置个性化**
   - 更新 `USER.md` - 你的信息
   - 更新 `TOOLS.md` - macOS 特有工具路径
   - 更新 `IDENTITY.md` - AI 助手的身份

3. **启用 Skills**
   ```bash
   # 安装常用 Skills
   clawdhub install apple-notes
   clawdhub install apple-reminders
   clawdhub install imsg
   ```

4. **配置 Telegram**
   - 创建 Bot（@BotFather）
   - 配置 Webhook 或 Polling
   - 测试消息收发

5. **设置定时任务**
   ```bash
   # 每天早上 9 点运行 Heartbeat
   # 使用 cron 或 OpenClaw 的 cron 功能
   ```

---

## 🆘 获取帮助

- **文档：** `~/.openclaw/workspace/docs/`
- **日志：** `~/.openclaw/workspace/aios/agent_system/*.log`
- **社区：** https://discord.com/invite/clawd
- **GitHub：** https://github.com/openclaw/openclaw

---

**部署完成！** 🎉

现在你的 MacBook 上已经有一个完整的太极OS 系统了。

记得定期：
- 备份 `memory/` 目录
- 更新 OpenClaw (`npm update -g openclaw-cn`)
- 同步 Windows 和 macOS 的数据
- 查看 Evolution Score 和系统健康度

祝使用愉快！ 🐾
