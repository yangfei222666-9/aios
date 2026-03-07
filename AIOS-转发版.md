# AIOS - AI 操作系统（朋友版）

> 一个让 AI Agent 能够自主运行、自我观测、自我进化的轻量级 AI 操作系统

---

## ⚙️ 配置要求

**必需：** 配置一个 LLM API（选择其中一个）

1. **OpenAI API** - 推荐，最稳定
   - 获取 API Key: https://platform.openai.com/api-keys
   - 设置环境变量: `OPENAI_API_KEY=your_key`

2. **Claude API** - 推荐，性能好
   - 获取 API Key: https://console.anthropic.com/
   - 设置环境变量: `ANTHROPIC_API_KEY=your_key`

3. **本地 Ollama** - 免费，但需要本地运行
   - 安装: https://ollama.com/
   - 启动: `ollama serve`

**配置方法：**
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your_key_here"

# Mac/Linux
export OPENAI_API_KEY="your_key_here"
```

或者编辑 `config.yaml` 文件：
```yaml
llm:
  provider: openai  # 或 anthropic / ollama
  api_key: your_key_here
  model: gpt-4  # 或 claude-3-sonnet / llama3
```

---

## 🚀 10 秒快速开始

### Windows 用户：
1. 解压 `AIOS-Friend-Edition-20260227.zip`
2. **配置 LLM API**（见上方）
3. 双击 `install.bat` 安装依赖（只需一次）
4. 双击 `run.bat` 运行演示

### Mac/Linux 用户：
```bash
# 1. 解压文件
unzip AIOS-Friend-Edition-20260227.zip
cd AIOS-Friend-Edition

# 2. 配置 LLM API
export OPENAI_API_KEY="your_key_here"

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行演示
python aios.py demo --scenario 1
```

---

## 💡 AIOS 是什么？

AIOS 是一个**轻量级的 AI 操作系统**，让你的 AI Agent 能够：

- 🤖 **自主运行** — 自动调度任务，无需人工干预
- 👁️ **自我观测** — 实时监控性能、成本、错误
- 🧬 **自我进化** — 从失败中学习，自动优化策略

---

## 🎯 3 个演示场景

### 场景 1：文件监控 + 自动分类
```bash
python aios.py demo --scenario 1
```
- 监控文件变化
- 自动分类文件（按扩展名）
- 生成分类报告

### 场景 2：API 健康检查 + 自动恢复
```bash
python aios.py demo --scenario 2
```
- 检查 API 健康状态
- 自动重试失败请求
- 记录恢复过程

### 场景 3：日志分析 + 自动生成 Playbook
```bash
python aios.py demo --scenario 3
```
- 分析错误日志
- 识别高频错误
- 自动生成修复 Playbook

---

## 📊 查看 Dashboard

```bash
python aios.py dashboard
```

然后打开浏览器访问：http://127.0.0.1:9091

---

## 🎯 提交任务

```bash
# 提交一个代码任务
python aios.py submit --desc "重构 scheduler.py" --type code --priority high

# 查看任务状态
python aios.py tasks

# 运行心跳（自动执行任务）
python aios.py heartbeat
```

---

## 📦 包含内容

- ✅ 完整 AIOS 代码（~3,000 行）
- ✅ 中文 README.txt（使用说明）
- ✅ run.bat（双击运行演示）
- ✅ install.bat（自动安装依赖）
- ✅ 3 个演示场景（文件监控、API 健康检查、日志分析）
- ✅ Dashboard 可视化界面

---

## 🐛 遇到问题？

1. **没有配置 LLM API** - 必须配置 OpenAI/Claude/Ollama 才能运行
2. **端口被占用** - 修改 `config.yaml` 中的 `dashboard.port`
3. **依赖缺失** - 运行 `pip install -r requirements.txt`
4. **API 调用失败** - 检查 API Key 是否正确，是否有余额
5. **其他问题** - 查看 `logs/` 目录的日志文件

---

## 📚 更多信息

- **版本：** v1.3
- **打包时间：** 2026-02-27 23:37:16
- **作者：** 珊瑚海 + 小九
- **GitHub：** https://github.com/yangfei222666-9/AIOS

---

**下载链接：** [AIOS-Friend-Edition-20260227.zip](文件已打包，1.55 MB)

**适合人群：**
- 对 AI Agent 感兴趣的开发者
- 想要搭建自己的 AI 系统的朋友
- 想要了解 AI 自我进化机制的研究者

**核心特点：**
- 零配置，开箱即用
- 完整的自我进化闭环
- 真实的 AI 决策系统
- 可视化 Dashboard

---

**试试看吧！有问题随时问我 🐾**
