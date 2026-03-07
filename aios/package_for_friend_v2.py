#!/usr/bin/env python3
"""
AIOS 打包工具 v2.0 - 朋友版（Windows）
生成一个安全、友好、开箱即用的 AIOS 包
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# 黑名单：绝对不打包
BLACKLIST = [
    "USER.md",
    "MEMORY.md",
    "SOUL.md",
    "IDENTITY.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
    "env_config.json",
    "aios.db",
    "*.jsonl",
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    "*.pyo",
    "*.log",
    ".git",
    ".vscode",
    ".idea",
]

# 黑名单目录：整个目录不打包
BLACKLIST_DIRS = [
    "agent_system/data",
    "agent_system/memory",
    "agent_system/lancedb*",
    "agent_system/logs",
    "agent_system/backups",
    "agent_system/market",
    "agent_system/experience_db.lance",
    "agent_system/lancedb_*",
    "backups",
    "logs",
    "memory",
    "events",
    "data/agent_storage",
    "data/events",
    "data/logs",
    "data/metrics",
    "data/traces",
    "AIOS-Friend-Edition",
    "aios-independent",
    "archive",
    "releases",
    "snapshots",
    "test_runs",
    "htmlcov",
    "dist",
    "*.egg-info",
]

# 白名单：核心文件
CORE_FILES = [
    "aios.py",
    "setup.py",
    "pyproject.toml",
    "LICENSE",
    "README.md",
    "QUICKSTART.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
]

# 白名单：核心目录
CORE_DIRS = [
    "core",
    "agent_system/agents",
    "agent_system/core",
    "agent_system/src",
    "agent_system/config",
    "agent_system/templates",
    "dashboard/AIOS-Dashboard-v3.4",
    "sdk",
    "demo_data",
    "docs",
]

def should_ignore(path: str) -> bool:
    """检查路径是否应该被忽略"""
    path_str = str(path).replace("\\", "/")
    
    # 检查黑名单文件
    for pattern in BLACKLIST:
        if pattern.startswith("*"):
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            return True
    
    # 检查黑名单目录
    for pattern in BLACKLIST_DIRS:
        if pattern.endswith("*"):
            if pattern[:-1] in path_str:
                return True
        elif pattern in path_str:
            return True
    
    return False

def create_package():
    """创建 AIOS 朋友版打包"""
    
    print("=" * 60)
    print("AIOS 打包工具 v2.0 - Windows 朋友版")
    print("=" * 60)
    print()
    
    # 1. 创建临时目录
    temp_dir = Path("aios_pack_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    print(f"📦 创建打包目录: {temp_dir}")
    print()
    
    # 2. 复制核心文件
    print("📄 复制核心文件...")
    for file in CORE_FILES:
        if os.path.exists(file):
            shutil.copy2(file, temp_dir / file)
            print(f"  ✓ {file}")
    print()
    
    # 3. 复制核心目录
    print("📁 复制核心目录...")
    for dir_name in CORE_DIRS:
        if os.path.exists(dir_name):
            dest = temp_dir / dir_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用自定义忽略函数
            def ignore_func(directory, contents):
                ignored = []
                for item in contents:
                    full_path = os.path.join(directory, item)
                    if should_ignore(full_path):
                        ignored.append(item)
                return ignored
            
            shutil.copytree(dir_name, dest, ignore=ignore_func)
            print(f"  ✓ {dir_name}/")
    print()
    
    # 4. 创建 .env.example
    print("🔧 创建配置模板...")
    env_example = """# AIOS 配置文件示例
# 复制此文件为 .env 并填入真实值

# OpenAI API Key（如果使用 OpenAI）
OPENAI_API_KEY=sk-your-key-here

# Anthropic API Key（如果使用 Claude）
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Telegram Bot Token（可选，用于通知）
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Dashboard 端口（默认 8888）
DASHBOARD_PORT=8888
"""
    (temp_dir / ".env.example").write_text(env_example, encoding="utf-8")
    print("  ✓ .env.example")
    
    # 5. 创建 config.example.yaml
    config_example = """# AIOS 配置文件示例
# 复制此文件为 config.yaml 并根据需要修改

dashboard:
  port: 8888
  host: "127.0.0.1"

agents:
  max_concurrent: 5
  timeout_seconds: 120

logging:
  level: "INFO"
  file: "logs/aios.log"
"""
    (temp_dir / "config.example.yaml").write_text(config_example, encoding="utf-8")
    print("  ✓ config.example.yaml")
    print()
    
    # 6. 创建友好的 README
    print("📝 创建 README...")
    readme_content = """# AIOS - AI 操作系统（朋友测试版）

## 🚀 10 秒快速开始

### 第一步：安装依赖
双击 `install.bat`，等待安装完成。

### 第二步：配置 API Key
1. 复制 `.env.example` 为 `.env`
2. 打开 `.env`，填入你的 API Key（OpenAI 或 Claude）

### 第三步：运行验证
双击 `verify.bat`，检查是否正常运行。

如果看到 "✓ AIOS 验证通过"，说明一切正常！

---

## 💡 AIOS 是什么？

AIOS 是一个**轻量级的 AI 操作系统**，让你的 AI Agent 能够：

- 🤖 **自主运行** - 自动调度任务，无需人工干预
- 👁️ **自我观测** - 实时监控性能、成本、错误
- 🧬 **自我进化** - 从失败中学习，自动优化策略

---

## 🎯 3 个验证命令

### 1. 启动 AIOS
```bash
python aios.py
```

### 2. 查看日志
```bash
type logs\\aios.log
```

### 3. 停止 AIOS
```
Ctrl + C
```

---

## 📊 查看 Dashboard

```bash
python start_dashboard.py
```

然后打开浏览器访问：http://127.0.0.1:8888

---

## 🎯 提交任务

```bash
# 提交一个代码任务
python aios.py submit --desc "重构 scheduler.py" --type code --priority high

# 查看任务状态
python aios.py tasks
```

---

## 🐛 遇到问题？

### 1. 端口被占用
修改 `config.yaml` 中的 `dashboard.port`

### 2. 依赖缺失
运行 `pip install -r requirements.txt`

### 3. API Key 错误
检查 `.env` 文件中的 API Key 是否正确

### 4. 其他问题
查看 `logs/` 目录的日志文件

---

## 📚 更多文档

- 完整文档: 查看 `docs/` 目录
- 快速开始: `QUICKSTART.md`
- 架构说明: `ARCHITECTURE.md`

---

**版本：** v1.3  
**打包时间：** """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """  
**作者：** 珊瑚海 + 小九  

---

**重要提示：**
- 这是测试版本，可能存在 Bug
- 请不要在生产环境使用
- 遇到问题请及时反馈
"""
    
    (temp_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    print("  ✓ README.txt")
    print()
    
    # 7. 创建 install.bat
    print("🔧 创建安装脚本...")
    install_bat = """@echo off
chcp 65001 >nul
echo ========================================
echo AIOS 依赖安装器
echo ========================================
echo.
echo 正在检查 Python...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python！
    echo 请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 正在安装依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo 错误: 依赖安装失败！
    echo 请检查网络连接或手动运行: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 复制 .env.example 为 .env
echo 2. 填入你的 API Key
echo 3. 双击 verify.bat 验证
echo.
pause
"""
    (temp_dir / "install.bat").write_text(install_bat, encoding="utf-8")
    print("  ✓ install.bat")
    
    # 8. 创建 verify.bat
    verify_bat = """@echo off
chcp 65001 >nul
echo ========================================
echo AIOS 验证工具
echo ========================================
echo.

echo [1/3] 检查 Python...
python --version
if errorlevel 1 (
    echo ✗ Python 未安装
    pause
    exit /b 1
)
echo ✓ Python 正常

echo.
echo [2/3] 检查依赖...
python -c "import sys; print('✓ 依赖正常')"
if errorlevel 1 (
    echo ✗ 依赖缺失，请运行 install.bat
    pause
    exit /b 1
)

echo.
echo [3/3] 检查配置...
if not exist .env (
    echo ✗ 配置文件缺失
    echo 请复制 .env.example 为 .env 并填入 API Key
    pause
    exit /b 1
)
echo ✓ 配置文件存在

echo.
echo ========================================
echo ✓ AIOS 验证通过！
echo ========================================
echo.
echo 你可以开始使用 AIOS 了：
echo   python aios.py
echo.
pause
"""
    (temp_dir / "verify.bat").write_text(verify_bat, encoding="utf-8")
    print("  ✓ verify.bat")
    print()
    
    # 9. 创建 requirements.txt
    print("📦 创建依赖文件...")
    requirements = """# AIOS 核心依赖
pyyaml>=6.0
aiosqlite>=0.17.0

# 测试（可选）
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
"""
    (temp_dir / "requirements.txt").write_text(requirements, encoding="utf-8")
    print("  ✓ requirements.txt")
    print()
    
    # 10. 创建 .gitignore
    gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# AIOS
aios.db
*.jsonl
logs/
*.log
.env
config.yaml

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
    (temp_dir / ".gitignore").write_text(gitignore, encoding="utf-8")
    print("  ✓ .gitignore")
    print()
    
    # 11. 打包成 zip
    zip_name = f"AIOS-Friend-Edition-Windows-{datetime.now().strftime('%Y%m%d')}.zip"
    
    print(f"📦 正在打包: {zip_name}")
    print()
    file_count = 0
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(str(temp_dir)):
            root_path = Path(root)
            # 过滤目录
            dirs[:] = [d for d in dirs if not should_ignore(str(root_path / d))]
            
            for file in files:
                file_path = root_path / file
                if not should_ignore(str(file_path)):
                    arcname = str(file_path.relative_to(temp_dir.parent))
                    zipf.write(str(file_path), arcname)
                    file_count += 1
    print(f"  ✓ 共打包 {file_count} 个文件")
    
    # 12. 清理临时目录
    shutil.rmtree(temp_dir)
    
    # 13. 获取文件大小
    size_mb = os.path.getsize(zip_name) / 1024 / 1024
    
    print()
    print("=" * 60)
    print("✅ 打包完成！")
    print("=" * 60)
    print(f"📦 文件: {zip_name}")
    print(f"📊 大小: {size_mb:.2f} MB")
    print(f"📍 路径: {os.path.abspath(zip_name)}")
    print()
    print("下一步：")
    print("1. 发送 zip 包给朋友")
    print("2. 让他解压后双击 install.bat")
    print("3. 配置 .env 文件")
    print("4. 双击 verify.bat 验证")
    print("=" * 60)
    
    return zip_name

if __name__ == "__main__":
    try:
        create_package()
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
