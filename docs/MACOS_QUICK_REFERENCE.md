# MacBook 部署快速参考卡

**太极OS (TaijiOS) - macOS 版本**

---

## 🚀 一键部署

```bash
bash <(curl -s https://your-repo/scripts/deploy_macos.sh)
```

---

## 📋 核心命令

### 安装
```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装工具
brew install python@3.12 node git

# 安装 OpenClaw
npm install -g openclaw-cn
```

### 启动
```bash
# 启动 Gateway
openclaw gateway start

# 启动 Memory Server
cd ~/.openclaw/workspace/aios/agent_system
python3.12 memory_server.py &
```

### 测试
```bash
# 系统测试
bash scripts/test_macos.sh

# Memory Server
curl http://localhost:7788/status

# AIOS 状态
cd ~/.openclaw/workspace/aios/agent_system
python3.12 aios.py status

# Heartbeat
python3.12 heartbeat_v5.py
```

---

## 🔧 常用路径

| 项目 | 路径 |
|------|------|
| 工作目录 | `~/.openclaw/workspace` |
| AIOS | `~/.openclaw/workspace/aios` |
| Agent System | `~/.openclaw/workspace/aios/agent_system` |
| Memory | `~/.openclaw/workspace/memory` |
| 日志 | `~/.openclaw/workspace/aios/agent_system/*.log` |

---

## 🐛 快速修复

### Memory Server 无法启动
```bash
tail -f ~/.openclaw/workspace/aios/agent_system/memory_server.log
lsof -i :7788
pkill -f memory_server.py
python3.12 memory_server.py &
```

### OpenClaw Gateway 问题
```bash
openclaw gateway logs
openclaw gateway restart
openclaw gateway config.get
```

### Python 依赖问题
```bash
cd ~/.openclaw/workspace/aios
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-macos.txt
```

---

## 📊 健康检查

```bash
# 完整测试
bash scripts/test_macos.sh

# 快速检查
curl http://localhost:7788/status  # Memory Server
openclaw gateway status             # Gateway
python3.12 aios.py status           # AIOS
```

---

## 🔐 安全设置

```bash
# API Keys
export ANTHROPIC_API_KEY="sk-ant-..."
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc

# 文件权限
chmod 600 ~/.openclaw/workspace/MEMORY.md
chmod 600 ~/.openclaw/workspace/memory/*.md
chmod 700 ~/.openclaw/workspace/aios/agent_system
```

---

## 📚 文档

- 完整指南：`docs/MACOS_DEPLOYMENT.md`
- 检查清单：`docs/MACOS_DEPLOYMENT_CHECKLIST.md`
- 快速开始：`docs/MACOS_DEPLOYMENT_README.md`

---

## 🆘 获取帮助

- 本地日志：`~/.openclaw/workspace/aios/agent_system/*.log`
- OpenClaw 日志：`openclaw gateway logs`
- 社区：https://discord.com/invite/clawd

---

**版本：** v1.0 | **日期：** 2026-03-10 | **维护者：** 小九 + 珊瑚海
