# macOS 部署脚本

**太极OS (TaijiOS) - macOS 自动化脚本**

---

## 📦 脚本列表

### 1. deploy_macos.sh - 自动部署脚本
**用途：** 一键部署太极OS 到 macOS

**功能：**
- 检查系统要求
- 安装必需工具（Homebrew、Python、Node.js、Git）
- 安装 OpenClaw
- 创建工作目录
- 克隆/同步 AIOS
- 安装 Python 依赖
- 配置 OpenClaw Gateway
- 设置自启动服务

**使用方法：**
```bash
bash deploy_macos.sh
```

**预计时间：** 30-45 分钟（取决于网络速度）

---

### 2. sync_to_macos.sh - 数据同步脚本
**用途：** 从 Windows 同步数据到 macOS

**功能：**
- 3 种同步方式（Git、rsync SSH、手动复制）
- 验证同步结果
- 修复路径差异（Windows → macOS）
- 设置文件权限
- 提示更新配置

**使用方法：**
```bash
bash sync_to_macos.sh
```

**预计时间：** 10-20 分钟（取决于数据量和同步方式）

---

### 3. test_macos.sh - 系统测试脚本
**用途：** 验证 macOS 部署是否成功

**功能：**
- 10 个测试模块
  1. 系统环境
  2. 工作目录
  3. Python 依赖
  4. Memory Server
  5. AIOS 系统
  6. Heartbeat
  7. OpenClaw Gateway
  8. 自启动服务
  9. 文件权限
  10. 网络连接
- 彩色输出（通过/失败/警告）
- 详细测试报告
- 测试总结和建议

**使用方法：**
```bash
bash test_macos.sh
```

**预计时间：** 2-5 分钟

---

## 🚀 快速开始

### 全新安装
```bash
# 1. 下载脚本
curl -O https://your-repo/scripts/deploy_macos.sh

# 2. 赋予执行权限
chmod +x deploy_macos.sh

# 3. 运行部署
bash deploy_macos.sh

# 4. 测试系统
bash test_macos.sh
```

### 从 Windows 迁移
```bash
# 1. 在 Windows 上提交代码
git add . && git commit -m "Prepare for macOS" && git push

# 2. 在 macOS 上同步
bash sync_to_macos.sh

# 3. 安装依赖
cd ~/.openclaw/workspace/aios
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-macos.txt

# 4. 测试系统
bash test_macos.sh
```

---

## 📋 脚本特性

### 错误处理
所有脚本都使用 `set -e`，遇到错误立即退出。

### 彩色输出
- 🟢 绿色 - 成功/通过
- 🔴 红色 - 失败/错误
- 🟡 黄色 - 警告/提示

### 进度提示
每个步骤都有清晰的进度提示和说明。

### 幂等性
脚本可以多次运行，不会重复安装已存在的组件。

---

## 🔧 自定义配置

### 修改工作目录
默认工作目录：`~/.openclaw/workspace`

修改方法：编辑脚本中的 `WORKSPACE` 变量
```bash
WORKSPACE="$HOME/.openclaw/workspace"  # 改为你想要的路径
```

### 修改 Python 版本
默认 Python 版本：3.12

修改方法：全局替换 `python3.12` 为你的版本
```bash
sed -i '' 's/python3.12/python3.11/g' deploy_macos.sh
```

### 跳过某些步骤
注释掉不需要的步骤：
```bash
# 跳过自启动配置
# setup_autostart
```

---

## 🐛 故障排查

### 脚本无法执行
```bash
# 检查权限
ls -l deploy_macos.sh

# 添加执行权限
chmod +x deploy_macos.sh

# 使用 bash 显式执行
bash deploy_macos.sh
```

### 网络问题
```bash
# 使用代理
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port

# 或使用国内镜像
# Homebrew 镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"

# pip 镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-macos.txt
```

### 权限问题
```bash
# 某些操作可能需要 sudo
sudo bash deploy_macos.sh

# 或单独执行需要权限的命令
sudo brew install python@3.12
```

---

## 📊 脚本输出示例

### deploy_macos.sh
```
🚀 太极OS MacBook 部署脚本 v1.0
================================

📋 步骤 1/8: 检查系统要求
------------------------
✓ 操作系统: macOS
✓ 用户: username
✓ 主目录: /Users/username

🔧 步骤 2/8: 检查必需工具
------------------------
✓ brew 已安装
✓ python3.12 已安装
✓ node 已安装
✓ git 已安装

...

================================
🎉 部署完成！
================================
```

### test_macos.sh
```
🧪 太极OS macOS 系统测试
========================

📋 1. 系统环境
-------------
✓ 操作系统: macOS
✓ Python 3.12: Python 3.12.0
✓ Node.js: v18.0.0
✓ OpenClaw: 1.0.0

...

========================
📊 测试总结
========================

通过: 25
失败: 0

🎉 所有测试通过！系统部署成功！
```

---

## 📚 相关文档

- **完整指南：** `../docs/MACOS_DEPLOYMENT.md`
- **检查清单：** `../docs/MACOS_DEPLOYMENT_CHECKLIST.md`
- **快速参考：** `../docs/MACOS_QUICK_REFERENCE.md`
- **资源索引：** `../docs/MACOS_DEPLOYMENT_INDEX.md`

---

## 🔐 安全提示

### API Keys
脚本不会处理 API Keys，需要手动配置：
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### 文件权限
脚本会自动设置敏感文件权限：
- MEMORY.md: 600
- memory/*.md: 600
- agent_system/: 700

### 网络安全
Memory Server 默认只监听 127.0.0.1，不暴露到公网。

---

## 🆘 获取帮助

### 查看脚本源码
所有脚本都有详细注释，可以直接查看：
```bash
cat deploy_macos.sh
```

### 运行诊断
```bash
bash test_macos.sh
```

### 查看日志
```bash
# OpenClaw 日志
openclaw gateway logs

# Memory Server 日志
tail -f ~/.openclaw/workspace/aios/agent_system/memory_server.log

# AIOS 日志
tail -f ~/.openclaw/workspace/aios/agent_system/*.log
```

---

## 📝 贡献

如果你发现脚本有问题或有改进建议：
1. 记录问题和解决方案
2. 更新脚本
3. 更新文档
4. 提交 Pull Request

---

**版本：** v1.0  
**更新日期：** 2026-03-10  
**维护者：** 小九 + 珊瑚海

祝使用愉快！ 🐾
