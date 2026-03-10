# MacBook 部署资源索引

**快速导航 - 太极OS (TaijiOS) macOS 部署**

---

## 📚 文档（按阅读顺序）

### 1️⃣ 开始前必读
- **[MACOS_DEPLOYMENT_README.md](MACOS_DEPLOYMENT_README.md)** - 资源包总览
  - 了解有哪些资源
  - 选择部署方式
  - 查看部署流程图

### 2️⃣ 详细部署指南
- **[MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md)** - 完整部署指南
  - 系统要求
  - 安装步骤
  - 配置说明
  - 故障排查

### 3️⃣ 检查清单
- **[MACOS_DEPLOYMENT_CHECKLIST.md](MACOS_DEPLOYMENT_CHECKLIST.md)** - 部署检查清单
  - 逐项检查
  - 确保不遗漏

### 4️⃣ 快速参考
- **[MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md)** - 快速参考卡
  - 常用命令
  - 快速修复
  - 日常使用

### 5️⃣ 完成总结
- **[MACOS_DEPLOYMENT_SUMMARY.md](MACOS_DEPLOYMENT_SUMMARY.md)** - 资源包总结
  - 资源统计
  - 使用建议
  - 维护计划

---

## 🛠️ 脚本（按使用顺序）

### 1️⃣ 自动部署
```bash
bash scripts/deploy_macos.sh
```
- 一键安装所有依赖
- 配置工作目录
- 设置自启动服务

### 2️⃣ 数据同步
```bash
bash scripts/sync_to_macos.sh
```
- 从 Windows 同步数据
- 修复路径差异
- 验证同步结果

### 3️⃣ 系统测试
```bash
bash scripts/test_macos.sh
```
- 全面测试系统
- 验证部署成功
- 诊断问题

---

## 📋 配置文件

### Python 依赖
```bash
pip install -r aios/requirements-macos.txt
```
- macOS 特定依赖
- Apple Silicon / Intel 支持
- 可选依赖说明

---

## 🎯 使用场景导航

### 场景 1: 我是新用户，第一次部署
1. 阅读 [MACOS_DEPLOYMENT_README.md](MACOS_DEPLOYMENT_README.md)
2. 运行 `bash scripts/deploy_macos.sh`
3. 运行 `bash scripts/test_macos.sh`
4. 参考 [MACOS_DEPLOYMENT_CHECKLIST.md](MACOS_DEPLOYMENT_CHECKLIST.md) 检查

### 场景 2: 我从 Windows 迁移
1. 在 Windows 上提交代码到 Git
2. 运行 `bash scripts/sync_to_macos.sh`
3. 安装依赖 `pip install -r aios/requirements-macos.txt`
4. 运行 `bash scripts/test_macos.sh`

### 场景 3: 我遇到问题了
1. 查看 [MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md) 的"常见问题"章节
2. 查看 [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md) 的"快速修复"
3. 运行 `bash scripts/test_macos.sh` 诊断
4. 查看日志文件

### 场景 4: 我需要快速查命令
1. 打开 [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md)
2. 查找对应的命令
3. 复制粘贴执行

### 场景 5: 我想了解部署细节
1. 阅读 [MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md)
2. 查看脚本源码（`scripts/*.sh`）
3. 参考 [MACOS_DEPLOYMENT_SUMMARY.md](MACOS_DEPLOYMENT_SUMMARY.md)

---

## 🔍 快速查找

### 我想找...

#### 安装命令
→ [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md) - 核心命令 - 安装

#### 启动命令
→ [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md) - 核心命令 - 启动

#### 测试命令
→ [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md) - 核心命令 - 测试

#### 常见问题
→ [MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md) - 常见问题章节

#### 路径对照
→ [MACOS_DEPLOYMENT_README.md](MACOS_DEPLOYMENT_README.md) - 平台差异对照表

#### 部署步骤
→ [MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md) - 快速部署章节

#### 检查清单
→ [MACOS_DEPLOYMENT_CHECKLIST.md](MACOS_DEPLOYMENT_CHECKLIST.md)

#### 自动化脚本
→ `scripts/deploy_macos.sh` - 自动部署  
→ `scripts/sync_to_macos.sh` - 数据同步  
→ `scripts/test_macos.sh` - 系统测试

---

## 📊 文件结构

```
workspace/
├── docs/
│   ├── MACOS_DEPLOYMENT_INDEX.md          ← 你在这里
│   ├── MACOS_DEPLOYMENT_README.md         ← 开始前必读
│   ├── MACOS_DEPLOYMENT.md                ← 详细指南
│   ├── MACOS_DEPLOYMENT_CHECKLIST.md      ← 检查清单
│   ├── MACOS_QUICK_REFERENCE.md           ← 快速参考
│   └── MACOS_DEPLOYMENT_SUMMARY.md        ← 完成总结
├── scripts/
│   ├── deploy_macos.sh                    ← 自动部署
│   ├── sync_to_macos.sh                   ← 数据同步
│   └── test_macos.sh                      ← 系统测试
└── aios/
    └── requirements-macos.txt             ← Python 依赖
```

---

## 🎯 推荐阅读路径

### 路径 A: 快速部署（30 分钟）
1. [MACOS_DEPLOYMENT_README.md](MACOS_DEPLOYMENT_README.md) - 5 分钟
2. 运行 `deploy_macos.sh` - 15 分钟
3. 运行 `test_macos.sh` - 5 分钟
4. [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md) - 5 分钟

### 路径 B: 详细了解（60 分钟）
1. [MACOS_DEPLOYMENT_README.md](MACOS_DEPLOYMENT_README.md) - 10 分钟
2. [MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md) - 30 分钟
3. [MACOS_DEPLOYMENT_CHECKLIST.md](MACOS_DEPLOYMENT_CHECKLIST.md) - 10 分钟
4. [MACOS_DEPLOYMENT_SUMMARY.md](MACOS_DEPLOYMENT_SUMMARY.md) - 10 分钟

### 路径 C: 故障排查（15 分钟）
1. [MACOS_QUICK_REFERENCE.md](MACOS_QUICK_REFERENCE.md) - 快速修复 - 5 分钟
2. [MACOS_DEPLOYMENT.md](MACOS_DEPLOYMENT.md) - 常见问题 - 10 分钟
3. 运行 `test_macos.sh` 诊断

---

## 🆘 紧急情况

### 系统无法启动
```bash
# 1. 查看日志
tail -f ~/.openclaw/workspace/aios/agent_system/*.log

# 2. 运行诊断
bash scripts/test_macos.sh

# 3. 查看快速修复
cat docs/MACOS_QUICK_REFERENCE.md
```

### 数据丢失
```bash
# 1. 检查备份
ls -la ~/.openclaw/workspace/memory/

# 2. 从 Windows 重新同步
bash scripts/sync_to_macos.sh

# 3. 从 Git 恢复
cd ~/.openclaw/workspace/aios
git pull
```

### 依赖问题
```bash
# 1. 重建虚拟环境
cd ~/.openclaw/workspace/aios
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate

# 2. 重新安装依赖
pip install -r requirements-macos.txt

# 3. 验证安装
python3.12 -c "import anthropic, openai, sentence_transformers; print('OK')"
```

---

## 📞 获取帮助

### 文档内帮助
- 每个文档都有详细的故障排查章节
- 脚本都有详细注释
- 配置文件有使用说明

### 外部帮助
- Discord: https://discord.com/invite/clawd
- GitHub: https://github.com/openclaw/openclaw
- 文档: https://docs.openclaw.ai

---

**版本：** v1.0  
**更新日期：** 2026-03-10  
**维护者：** 小九 + 珊瑚海

**提示：** 建议将此文件加入书签，方便快速查找资源。
