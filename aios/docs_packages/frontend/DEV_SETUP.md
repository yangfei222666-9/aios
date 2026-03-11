# 太极OS (TaijiOS) - 开发环境配置指南

**版本：** v1.0  
**日期：** 2026-03-10  
**平台：** Windows 11 专业版

---

## 系统要求

### 硬件
- CPU: Ryzen 7 9800X3D (或同等性能)
- GPU: RTX 5070 Ti (或同等性能，用于 torch)
- RAM: 32GB+
- 存储: 2TB NVMe SSD

### 软件
- 操作系统: Windows 11 专业版
- Python: 3.12.10 (已安装在 `C:\Program Files\Python312\`)
- Git: 最新版本
- PowerShell: 5.1+ (Windows 自带)

---

## 快速开始

### 1. 克隆项目（如果还没有）

```powershell
cd C:\Users\A\.openclaw\workspace
git clone <repository-url> aios
cd aios
```

### 2. 检查 Python 版本

```powershell
& "C:\Program Files\Python312\python.exe" --version
# 应该输出: Python 3.12.10
```

### 3. 安装依赖

**基础依赖（必需）：**
```powershell
& "C:\Program Files\Python312\python.exe" -m pip install -r requirements.txt
```

**完整依赖（推荐）：**
```powershell
& "C:\Program Files\Python312\python.exe" -m pip install -r requirements.txt
& "C:\Program Files\Python312\python.exe" -m pip install fastapi uvicorn prometheus-client python-multipart
```

### 4. 验证安装

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" -c "import torch; import sentence_transformers; import lancedb; print('✅ 核心依赖已安装')"
```

---

## 核心依赖说明

### 必需依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `torch` | 2.10.0+cu128 | PyTorch (CUDA 12.8) |
| `sentence-transformers` | 5.2.3 | 嵌入模型 |
| `lancedb` | 0.29.2 | 向量数据库 |
| `pydantic` | 2.9.2 | 数据验证 |
| `portalocker` | 3.2.0 | 文件锁 |
| `psutil` | 7.2.2 | 系统监控 |
| `requests` | 2.32.5 | HTTP 请求 |
| `pyyaml` | 6.0.3 | YAML 解析 |

### 可选依赖（Dashboard）

| 包名 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.133.1 | Web 框架 |
| `uvicorn` | 0.41.0 | ASGI 服务器 |
| `prometheus-client` | 0.24.1 | 监控指标 |
| `python-multipart` | 0.0.20 | 文件上传 |

### 开发依赖（可选）

| 包名 | 版本 | 用途 |
|------|------|------|
| `pytest` | 9.0.2 | 测试框架 |
| `pytest-asyncio` | 1.3.0 | 异步测试 |
| `pytest-cov` | 7.0.0 | 覆盖率 |
| `black` | 26.1.0 | 代码格式化 |

---

## 项目结构

```
aios/
├── agent_system/          # 核心 Agent 系统
│   ├── core/              # 核心模块
│   ├── agents/            # Agent 定义
│   ├── memory/            # 记忆系统
│   ├── data/              # 数据存储
│   ├── docs/              # 文档
│   ├── scripts/           # 脚本
│   └── tests/             # 测试
├── aios/                  # AIOS 框架
├── dashboard/             # Dashboard (可选)
├── docs/                  # 项目文档
├── requirements.txt       # 基础依赖
└── requirements-macos.txt # macOS 依赖（参考）
```

---

## 常用命令

### 运行 AIOS

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" aios.py
```

### 运行 Heartbeat

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py
```

### 运行 Memory Server

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" memory_server.py
```

### 运行 Dashboard

```powershell
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4
& "C:\Program Files\Python312\python.exe" server.py
```

### 运行测试

```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" -m pytest tests/
```

---

## 编码配置（重要）

为避免 Windows/PowerShell 编码问题，所有 Python 命令统一使用：

**环境变量（推荐）：**
```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING='utf-8'
```

**命令行参数：**
```powershell
& "C:\Program Files\Python312\python.exe" -X utf8 <script.py>
```

**完整命令模板：**
```powershell
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 <script.py>
```

---

## 常见问题

### 1. torch 安装失败

**问题：** `torch` 安装失败或版本不匹配

**解决：**
```powershell
# 卸载旧版本
& "C:\Program Files\Python312\python.exe" -m pip uninstall torch torchvision torchaudio

# 安装 CUDA 版本（推荐）
& "C:\Program Files\Python312\python.exe" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 或安装 CPU 版本
& "C:\Program Files\Python312\python.exe" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 2. sentence-transformers 首次运行慢

**问题：** 首次运行时下载模型很慢

**解决：**
```powershell
# 预下载模型
& "C:\Program Files\Python312\python.exe" -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 3. lancedb 安装失败

**问题：** `lancedb` 安装失败

**解决：**
```powershell
# 确保安装了 Visual C++ Build Tools
# 下载地址: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 或使用预编译版本
& "C:\Program Files\Python312\python.exe" -m pip install lancedb --prefer-binary
```

### 4. PowerShell 编码问题

**问题：** 中文乱码或 `&&` 报错

**解决：**
- 不要使用 `&&`，用 `;` 分隔命令
- 不要使用 `~\`，用绝对路径
- 设置环境变量：`$env:PYTHONUTF8=1`

---

## 开发工作流

### 1. 每日启动

```powershell
# 1. 启动 Memory Server（常驻进程）
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" memory_server.py

# 2. 启动 Dashboard（可选）
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4
& "C:\Program Files\Python312\python.exe" server.py

# 3. 运行 Heartbeat（自动任务）
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py
```

### 2. 开发新功能

```powershell
# 1. 创建新分支
git checkout -b feature/new-feature

# 2. 编写代码
# ...

# 3. 运行测试
& "C:\Program Files\Python312\python.exe" -m pytest tests/

# 4. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 3. 调试

```powershell
# 使用 Python 调试器
& "C:\Program Files\Python312\python.exe" -m pdb <script.py>

# 或使用 VS Code 调试器（推荐）
# 在 VS Code 中打开项目，按 F5 启动调试
```

---

## IDE 配置

### VS Code（推荐）

**安装扩展：**
- Python (Microsoft)
- Pylance (Microsoft)
- Python Debugger (Microsoft)
- GitLens (Eric Amodio)

**配置文件（`.vscode/settings.json`）：**
```json
{
  "python.defaultInterpreterPath": "C:\\Program Files\\Python312\\python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.encoding": "utf8",
  "files.autoGuessEncoding": false
}
```

**调试配置（`.vscode/launch.json`）：**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    },
    {
      "name": "AIOS: Heartbeat",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/agent_system/heartbeat_v5.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/agent_system",
      "env": {
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  ]
}
```

### PyCharm（备选）

**配置 Python 解释器：**
1. File → Settings → Project → Python Interpreter
2. 选择 `C:\Program Files\Python312\python.exe`

**配置编码：**
1. File → Settings → Editor → File Encodings
2. 设置 Project Encoding 为 UTF-8

---

## 性能优化

### 1. 使用虚拟环境（可选）

```powershell
# 创建虚拟环境
& "C:\Program Files\Python312\python.exe" -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 2. 使用 GPU 加速

确保安装了 CUDA 版本的 torch：
```powershell
& "C:\Program Files\Python312\python.exe" -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 3. 预加载模型

在 `memory_server.py` 中预加载常用模型，避免每次启动时重新加载。

---

## 下一步

1. **阅读核心文档：**
   - `ARCHITECTURE.md` - 系统架构
   - `HEARTBEAT.md` - 心跳机制
   - `MEMORY.md` - 记忆系统

2. **运行示例：**
   - `demo.py` - 基础示例
   - `demo_full_cycle_v2.py` - 完整流程

3. **探索 Agent 系统：**
   - `agent_system/agents/` - Agent 定义
   - `agent_system/core/` - 核心模块

4. **参与开发：**
   - 阅读 `CONTRIBUTING.md`
   - 查看 GitHub Issues
   - 提交 Pull Request

---

## 联系方式

- **项目维护者：** 珊瑚海 (@shh7799)
- **AI 助手：** 小九 🐾
- **项目地址：** C:\Users\A\.openclaw\workspace\aios

---

**最后更新：** 2026-03-10  
**文档版本：** v1.0
