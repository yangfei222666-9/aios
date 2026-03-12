# Mac 独立部署太极OS 指南

## 前置要求

### 1. 系统要求
- macOS 10.15+ (Catalina 或更高)
- Python 3.12+
- Git
- 至少 10GB 可用空间

### 2. 安装 Homebrew（如果没有）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. 安装 Python 3.12
```bash
brew install python@3.12
python3.12 --version
```

---

## 部署步骤

### 1. 创建工作目录
```bash
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace
```

### 2. 从 Windows 同步代码

**方案 A：使用 Git（推荐）**
```bash
# 在 Windows 上先提交代码
cd C:\Users\A\.openclaw\workspace
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main

# 在 Mac 上克隆
cd ~/.openclaw/workspace
git clone <your-repo-url> aios
```

**方案 B：手动复制**
```bash
# 使用 scp 或其他文件传输工具
# 从 Windows 复制整个 aios 目录到 Mac
```

### 3. 安装依赖

```bash
cd ~/.openclaw/workspace/aios/agent_system

# 创建虚拟环境（推荐）
python3.12 -m venv venv
source venv/bin/activate

# 安装核心依赖
pip install torch sentence-transformers lancedb
pip install psutil fastapi uvicorn prometheus-client
pip install numpy pandas matplotlib

# 验证安装
python -c "import torch; print(torch.__version__)"
python -c "import sentence_transformers; print('OK')"
```

### 4. 配置环境

**创建配置文件：**
```bash
cat > ~/.openclaw/workspace/aios/agent_system/.env << 'EOF'
# 太极OS Mac 环境配置
PYTHONIOENCODING=utf-8
PYTHONUTF8=1

# 路径配置
AIOS_ROOT=~/.openclaw/workspace/aios
WORKSPACE_ROOT=~/.openclaw/workspace

# Memory Server
MEMORY_SERVER_PORT=7788

# Dashboard
DASHBOARD_PORT=8889
EOF
```

### 5. 启动 Memory Server

```bash
cd ~/.openclaw/workspace/aios/agent_system

# 启动 Memory Server
python memory_server.py &

# 验证
curl http://localhost:7788/status
```

### 6. 配置自动启动（可选）

**使用 launchd：**

```bash
# 创建 plist 文件
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
        <string>-X</string>
        <string>utf8</string>
        <string>/Users/YOUR_USERNAME/.openclaw/workspace/aios/agent_system/memory_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/.openclaw/workspace/aios/logs/memory-server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/.openclaw/workspace/aios/logs/memory-server-error.log</string>
</dict>
</plist>
EOF

# 替换 YOUR_USERNAME
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.taijios.memory-server.plist

# 加载服务
launchctl load ~/Library/LaunchAgents/com.taijios.memory-server.plist

# 验证
launchctl list | grep taijios
```

### 7. 配置 Heartbeat 定时任务

**使用 cron：**

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每 6 小时执行一次）
0 */6 * * * cd ~/.openclaw/workspace/aios/agent_system && /usr/local/bin/python3.12 -X utf8 heartbeat_v5.py >> ~/.openclaw/workspace/aios/logs/heartbeat.log 2>&1
```

---

## 验证部署

### 1. 检查 Memory Server
```bash
curl http://localhost:7788/status
# 应该返回：{"status": "ok", "model": "all-MiniLM-L6-v2", "port": 7788}
```

### 2. 运行健康检查
```bash
cd ~/.openclaw/workspace/aios/agent_system
python health_check_v2.py
```

### 3. 启动 Dashboard
```bash
cd ~/.openclaw/workspace/aios/dashboard/AIOS-Dashboard-v4.0
python server.py &

# 访问
open http://localhost:8889
```

---

## 数据同步策略

### 方案 A：Git 同步（推荐）

**Windows → Mac：**
```bash
# Windows
cd C:\Users\A\.openclaw\workspace\aios
git add .
git commit -m "Update from Windows"
git push

# Mac
cd ~/.openclaw/workspace/aios
git pull
```

**注意：** 不要同步以下文件（添加到 .gitignore）：
```
data/*.jsonl
data/*.json
logs/
*.log
__pycache__/
venv/
.env
```

### 方案 B：定期备份同步

**使用 rsync：**
```bash
# 从 Windows 同步到 Mac（需要 SSH 访问）
rsync -avz --exclude='*.log' --exclude='__pycache__' \
  user@windows-machine:/c/Users/A/.openclaw/workspace/aios/ \
  ~/.openclaw/workspace/aios/
```

---

## 双环境运行策略

### 策略 1：开发 + 生产分离
- **Mac：** 开发环境，快速迭代，测试新功能
- **Windows：** 生产环境，稳定运行，定时任务

### 策略 2：主备模式
- **Windows：** 主环境，日常运行
- **Mac：** 备份环境，定期同步，故障切换

### 策略 3：功能分离
- **Mac：** 学习 Agent（GitHub_Researcher 等）
- **Windows：** 执行 Agent（Coder、Analyst 等）

---

## 常见问题

### 1. 端口冲突
如果两台机器同时运行，修改端口：
```bash
# Mac 使用不同端口
MEMORY_SERVER_PORT=7789
DASHBOARD_PORT=8890
```

### 2. 路径差异
Mac 使用 `/`，Windows 使用 `\`。确保代码中使用 `Path` 对象：
```python
from pathlib import Path
data_dir = Path("data")  # 自动适配平台
```

### 3. 编码问题
Mac 默认 UTF-8，不需要特殊配置。但为了一致性，仍然设置：
```bash
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
```

---

## 快速启动脚本

**创建 `start.sh`：**
```bash
#!/bin/bash
cd ~/.openclaw/workspace/aios/agent_system

# 启动 Memory Server
python memory_server.py &
echo "Memory Server started on port 7788"

# 启动 Dashboard
cd ../dashboard/AIOS-Dashboard-v4.0
python server.py &
echo "Dashboard started on port 8889"

echo "太极OS started on Mac"
echo "Memory Server: http://localhost:7788"
echo "Dashboard: http://localhost:8889"
```

**使用：**
```bash
chmod +x start.sh
./start.sh
```

---

## 下一步

1. ✅ 完成基础部署
2. ⏳ 配置自动启动
3. ⏳ 设置数据同步
4. ⏳ 验证双环境运行

---

**版本：** v1.0  
**最后更新：** 2026-03-12  
**维护者：** 小九 + 珊瑚海
