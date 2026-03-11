# 太极OS (TaijiOS) - 快速参考

**版本：** v1.0  
**日期：** 2026-03-10

---

## 快速启动

### 一键启动所有服务

```powershell
.\start.ps1
```

### 单独启动服务

```powershell
# Memory Server
.\start.ps1 -Mode memory

# Dashboard
.\start.ps1 -Mode dashboard

# Heartbeat
.\start.ps1 -Mode heartbeat

# 验证环境
.\start.ps1 -Mode verify
```

---

## 常用命令

### Python 命令模板

```powershell
# 标准模板（推荐）
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 <script.py>

# 简化模板（如果环境变量已设置）
& "C:\Program Files\Python312\python.exe" -X utf8 <script.py>
```

### 核心服务

```powershell
# Memory Server（端口 7788）
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" memory_server.py

# Dashboard（端口 8888）
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4
& "C:\Program Files\Python312\python.exe" server.py

# Heartbeat
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py
```

### 开发工具

```powershell
# 验证开发环境
& "C:\Program Files\Python312\python.exe" verify_dev_env.py

# 运行测试
cd agent_system
& "C:\Program Files\Python312\python.exe" -m pytest tests/ -v

# 运行测试（带覆盖率）
& "C:\Program Files\Python312\python.exe" -m pytest tests/ --cov=. --cov-report=html -v

# 代码格式化
& "C:\Program Files\Python312\python.exe" -m black .

# 代码检查
& "C:\Program Files\Python312\python.exe" -m flake8 .
```

---

## VS Code 快捷键

### 调试

- `F5` - 启动调试
- `Shift+F5` - 停止调试
- `F9` - 切换断点
- `F10` - 单步跳过
- `F11` - 单步进入
- `Shift+F11` - 单步跳出

### 任务

- `Ctrl+Shift+B` - 运行构建任务
- `Ctrl+Shift+P` → "Tasks: Run Task" - 运行任务

### 常用任务

- `AIOS: Run Heartbeat` - 运行心跳
- `AIOS: Start Memory Server` - 启动 Memory Server
- `AIOS: Start Dashboard` - 启动 Dashboard
- `AIOS: Verify Dev Env` - 验证环境
- `Python: Run Tests` - 运行测试
- `Python: Format with Black` - 格式化代码

---

## 项目结构速查

```
aios/
├── agent_system/              # 核心 Agent 系统
│   ├── core/                  # 核心模块
│   │   ├── app_alias.py       # 应用别名解析
│   │   └── ...
│   ├── agents/                # Agent 定义
│   │   ├── learning_agents.py # 学习 Agent
│   │   └── ...
│   ├── memory/                # 记忆系统
│   │   ├── memory_server.py   # Memory Server
│   │   └── ...
│   ├── data/                  # 数据存储
│   │   ├── agents.json        # Agent 配置
│   │   ├── task_queue.jsonl   # 任务队列
│   │   └── ...
│   ├── docs/                  # 文档
│   ├── scripts/               # 脚本
│   ├── tests/                 # 测试
│   ├── aios.py                # AIOS 主程序
│   ├── heartbeat_v5.py        # Heartbeat v5
│   └── memory_server.py       # Memory Server
├── dashboard/                 # Dashboard
│   └── AIOS-Dashboard-v3.4/
│       └── server.py          # Dashboard 服务器
├── docs/                      # 项目文档
├── .vscode/                   # VS Code 配置
│   ├── launch.json            # 调试配置
│   ├── tasks.json             # 任务配置
│   └── settings.json          # 编辑器配置
├── requirements.txt           # 基础依赖
├── requirements-macos.txt     # macOS 依赖
├── DEV_SETUP.md               # 开发环境配置指南
├── QUICK_REFERENCE.md         # 快速参考（本文档）
├── verify_dev_env.py          # 环境验证脚本
├── start.ps1                  # 快速启动脚本
└── taijios.code-workspace     # VS Code 工作区
```

---

## 常见工作流

### 1. 每日启动

```powershell
# 1. 启动所有服务
.\start.ps1

# 2. 打开 VS Code
code taijios.code-workspace

# 3. 验证环境
.\start.ps1 -Mode verify
```

### 2. 开发新功能

```powershell
# 1. 创建新分支
git checkout -b feature/new-feature

# 2. 编写代码
# ...

# 3. 运行测试
cd agent_system
& "C:\Program Files\Python312\python.exe" -m pytest tests/ -v

# 4. 格式化代码
& "C:\Program Files\Python312\python.exe" -m black .

# 5. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 3. 调试问题

```powershell
# 1. 在 VS Code 中打开文件
# 2. 设置断点（F9）
# 3. 按 F5 启动调试
# 4. 单步执行（F10/F11）
```

### 4. 运行 Heartbeat

```powershell
# 方式 1：使用启动脚本
.\start.ps1 -Mode heartbeat

# 方式 2：直接运行
cd agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py

# 方式 3：在 VS Code 中调试
# 选择 "AIOS: Heartbeat v5" 配置，按 F5
```

---

## 常见问题速查

### 编码问题

**问题：** 中文乱码

**解决：**
```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING='utf-8'
```

### PowerShell 语法问题

**问题：** `&&` 报错

**解决：** 用 `;` 分隔命令
```powershell
# ❌ 错误
cd path && python script.py

# ✅ 正确
cd path; python script.py
```

### 路径问题

**问题：** `~\` 不识别

**解决：** 用绝对路径
```powershell
# ❌ 错误
cd ~\.openclaw\workspace

# ✅ 正确
cd C:\Users\A\.openclaw\workspace
```

### Memory Server 未运行

**问题：** Heartbeat 报错 Memory Server 未运行

**解决：**
```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" memory_server.py
```

### CUDA 不可用

**问题：** PyTorch 无法使用 GPU

**解决：**
```powershell
# 检查 CUDA
& "C:\Program Files\Python312\python.exe" -c "import torch; print(torch.cuda.is_available())"

# 重新安装 CUDA 版本
& "C:\Program Files\Python312\python.exe" -m pip uninstall torch
& "C:\Program Files\Python312\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cu128
```

---

## 环境变量

### 必需环境变量

```powershell
$env:PYTHONUTF8 = 1
$env:PYTHONIOENCODING = 'utf-8'
```

### 可选环境变量

```powershell
$env:PYTHON_PATH = "C:\Program Files\Python312\python.exe"
```

### 永久设置（可选）

```powershell
# 用户级别
[System.Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', 'User')
[System.Environment]::SetEnvironmentVariable('PYTHONIOENCODING', 'utf-8', 'User')

# 系统级别（需要管理员权限）
[System.Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', 'Machine')
[System.Environment]::SetEnvironmentVariable('PYTHONIOENCODING', 'utf-8', 'Machine')
```

---

## 端口占用

| 服务 | 端口 | 用途 |
|------|------|------|
| Memory Server | 7788 | 记忆检索服务 |
| Dashboard | 8888 | Web 界面 |

### 检查端口占用

```powershell
# 检查端口
netstat -ano | findstr :7788
netstat -ano | findstr :8888

# 杀死进程
taskkill /PID <pid> /F
```

---

## Git 工作流

### 常用命令

```powershell
# 查看状态
git status

# 查看差异
git diff

# 添加文件
git add .

# 提交
git commit -m "message"

# 推送
git push

# 拉取
git pull

# 创建分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature

# 查看日志
git log --oneline
```

### Commit 规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式化
refactor: 重构
test: 测试
chore: 构建/工具链
```

---

## 资源链接

- **项目路径：** `C:\Users\A\.openclaw\workspace\aios`
- **Memory Server：** http://127.0.0.1:7788
- **Dashboard：** http://127.0.0.1:8888
- **文档：** `docs/`
- **测试：** `agent_system/tests/`

---

## 联系方式

- **项目维护者：** 珊瑚海 (@shh7799)
- **AI 助手：** 小九 🐾

---

**最后更新：** 2026-03-10  
**文档版本：** v1.0
