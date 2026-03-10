# MacBook 部署资源包 - 太极OS (TaijiOS)

**版本：** v1.0  
**日期：** 2026-03-10  
**维护者：** 小九 + 珊瑚海

---

## 📦 资源清单

本目录包含 MacBook 部署所需的所有资源：

### 📄 文档

1. **MACOS_DEPLOYMENT.md** - 完整部署指南
   - 系统要求
   - 安装步骤
   - 配置说明
   - 故障排查
   - 性能优化

2. **MACOS_DEPLOYMENT_CHECKLIST.md** - 部署检查清单
   - 部署前检查
   - 部署步骤清单
   - 功能测试清单
   - 安全检查清单

### 🛠️ 脚本

1. **scripts/deploy_macos.sh** - 自动部署脚本
   ```bash
   bash scripts/deploy_macos.sh
   ```
   - 检查系统要求
   - 安装必需工具
   - 配置工作目录
   - 设置自启动服务

2. **scripts/sync_to_macos.sh** - 数据同步脚本
   ```bash
   bash scripts/sync_to_macos.sh
   ```
   - Git 同步
   - rsync SSH 同步
   - 手动复制
   - 路径修复

3. **scripts/test_macos.sh** - 系统测试脚本
   ```bash
   bash scripts/test_macos.sh
   ```
   - 环境测试
   - 依赖测试
   - 功能测试
   - 网络测试

### 📋 配置文件

1. **aios/requirements-macos.txt** - macOS Python 依赖
   ```bash
   pip install -r aios/requirements-macos.txt
   ```
   - 核心依赖
   - macOS 特定依赖
   - 可选依赖

---

## 🚀 快速开始

### 方式 1: 自动部署（推荐）

```bash
# 1. 下载部署脚本
curl -O https://your-repo/scripts/deploy_macos.sh

# 2. 赋予执行权限
chmod +x deploy_macos.sh

# 3. 运行部署
bash deploy_macos.sh
```

### 方式 2: 手动部署

```bash
# 1. 安装基础工具
brew install python@3.12 node git

# 2. 安装 OpenClaw
npm install -g openclaw-cn

# 3. 创建工作目录
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 4. 克隆/同步 AIOS
git clone <your-repo> aios

# 5. 安装依赖
cd aios
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-macos.txt

# 6. 启动服务
openclaw gateway start
python3.12 agent_system/memory_server.py &

# 7. 测试系统
bash ../scripts/test_macos.sh
```

---

## 📊 部署流程图

```
开始
  ↓
检查系统要求 ──✗──→ 安装缺失工具
  ↓ ✓
安装 OpenClaw
  ↓
创建工作目录
  ↓
同步 AIOS 代码 ←─┬─ Git 克隆
  ↓              ├─ rsync 同步
  ↓              └─ 手动复制
安装 Python 依赖
  ↓
配置核心文件
  ↓
启动服务 ──┬─ OpenClaw Gateway
  ↓        └─ Memory Server
  ↓
运行测试 ──✗──→ 修复问题
  ↓ ✓
部署完成
```

---

## 🔧 平台差异对照表

| 项目 | Windows | macOS |
|------|---------|-------|
| **工作目录** | `C:\Users\A\.openclaw\workspace` | `~/.openclaw/workspace` |
| **Python** | `C:\Program Files\Python312\python.exe` | `python3.12` |
| **命令分隔** | `;` (PowerShell) | `;` 或 `&&` (Bash/Zsh) |
| **环境变量** | `$env:VAR=value` | `export VAR=value` |
| **后台运行** | `Start-Process` | `nohup ... &` |
| **自启动** | Task Scheduler | LaunchAgent |
| **编码** | 需要 UTF-8 配置 | 默认 UTF-8 |

---

## 📝 部署步骤概览

### 阶段 1: 准备（10 分钟）
- [ ] 检查 macOS 版本
- [ ] 安装 Homebrew
- [ ] 安装 Python 3.12
- [ ] 安装 Node.js
- [ ] 安装 Git

### 阶段 2: 安装（15 分钟）
- [ ] 安装 OpenClaw
- [ ] 创建工作目录
- [ ] 克隆/同步 AIOS
- [ ] 安装 Python 依赖

### 阶段 3: 配置（20 分钟）
- [ ] 配置 OpenClaw Gateway
- [ ] 复制核心文件
- [ ] 修复路径差异
- [ ] 设置文件权限

### 阶段 4: 启动（10 分钟）
- [ ] 启动 Memory Server
- [ ] 启动 OpenClaw Gateway
- [ ] 配置自启动服务

### 阶段 5: 测试（15 分钟）
- [ ] 运行系统测试
- [ ] 测试 Memory Server
- [ ] 测试 AIOS
- [ ] 测试 Heartbeat

**总计：约 70 分钟**

---

## 🐛 常见问题

### Q1: Memory Server 启动失败

**症状：** `curl http://localhost:7788/status` 连接失败

**解决：**
```bash
# 检查日志
tail -f ~/.openclaw/workspace/aios/agent_system/memory_server.log

# 检查端口
lsof -i :7788

# 重启
pkill -f memory_server.py
cd ~/.openclaw/workspace/aios/agent_system
python3.12 memory_server.py &
```

### Q2: torch 安装失败（Apple Silicon）

**症状：** `pip install torch` 报错

**解决：**
```bash
# Apple Silicon 优化版本
pip install torch torchvision torchaudio

# 或使用 CPU 版本
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Q3: OpenClaw Gateway 无法启动

**症状：** `openclaw gateway start` 报错

**解决：**
```bash
# 查看日志
openclaw gateway logs

# 检查配置
openclaw gateway config.get

# 重启
openclaw gateway restart
```

### Q4: 路径问题

**症状：** 找不到文件或模块

**解决：**
```bash
# 设置 PYTHONPATH
export PYTHONPATH=~/.openclaw/workspace/aios:$PYTHONPATH

# 永久设置（添加到 ~/.zshrc）
echo 'export PYTHONPATH=~/.openclaw/workspace/aios:$PYTHONPATH' >> ~/.zshrc
source ~/.zshrc
```

---

## 📚 相关文档

### 核心文档
- `AGENTS.md` - 系统规则和工作流程
- `SOUL.md` - AI 助手性格和行为准则
- `HEARTBEAT.md` - 自动任务和心跳机制
- `MEMORY.md` - 长期记忆和学习目标

### 技术文档
- `docs/AIOS_ARCHITECTURE.md` - 系统架构
- `docs/AGENT_SYSTEM.md` - Agent 系统设计
- `docs/MEMORY_ENGINE.md` - Memory Engine 原理

### 用户文档
- `USER.md` - 用户信息和偏好
- `TOOLS.md` - 工具配置和路径
- `IDENTITY.md` - AI 助手身份

---

## 🔐 安全建议

### API Keys
```bash
# 使用环境变量
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# 添加到 ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
```

### 文件权限
```bash
# 限制敏感文件权限
chmod 600 ~/.openclaw/workspace/MEMORY.md
chmod 600 ~/.openclaw/workspace/memory/*.md
chmod 700 ~/.openclaw/workspace/aios/agent_system
```

### 网络安全
```bash
# Memory Server 只监听本地
# memory_server.py 中：
# app.run(host='127.0.0.1', port=7788)
```

---

## 🆘 获取帮助

### 文档
- 本地文档：`~/.openclaw/workspace/docs/`
- 在线文档：https://docs.openclaw.ai

### 日志
- OpenClaw：`openclaw gateway logs`
- Memory Server：`~/.openclaw/workspace/aios/agent_system/memory_server.log`
- AIOS：`~/.openclaw/workspace/aios/agent_system/*.log`

### 社区
- Discord：https://discord.com/invite/clawd
- GitHub：https://github.com/openclaw/openclaw

---

## 📊 部署验收标准

部署成功的标志：

- [ ] 所有核心文件存在
- [ ] Python 依赖安装完成
- [ ] Memory Server 运行正常
- [ ] OpenClaw Gateway 运行正常
- [ ] AIOS 状态检查通过
- [ ] Heartbeat 运行成功
- [ ] 系统测试全部通过
- [ ] 稳定运行 24 小时以上

---

## 🎉 部署完成后

### 立即执行
1. 更新 `USER.md` - 添加 macOS 特定信息
2. 更新 `TOOLS.md` - 配置 macOS 应用路径
3. 配置 Telegram（如需要）
4. 运行首次 Heartbeat

### 短期计划
1. 安装常用 Skills
   ```bash
   clawdhub install apple-notes
   clawdhub install apple-reminders
   clawdhub install imsg
   ```

2. 配置定时任务
3. 测试所有核心功能
4. 建立 Windows ↔ macOS 同步流程

### 长期维护
1. 定期备份 `memory/` 目录
2. 定期更新 OpenClaw
3. 定期同步数据
4. 监控系统健康度

---

**祝部署顺利！** 🐾

如有问题，请查看 `MACOS_DEPLOYMENT.md` 或运行 `bash scripts/test_macos.sh` 诊断。
