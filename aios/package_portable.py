#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS Portable 打包工具 v1.0
生成一个开箱即用的 AIOS 一键启动包
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 强制 UTF-8 输出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 源目录
SOURCE_DIR = Path(__file__).parent
PORTABLE_DIR = SOURCE_DIR / "AIOS-Portable"

# 核心文件（必须包含）
CORE_FILES = [
    "requirements.txt",
    "LICENSE",
    "setup.py",
    "pyproject.toml",
]

# 核心目录（必须包含）
CORE_DIRS = [
    "agent_system/agents",
    "agent_system/core",
    "agent_system/config",
    "agent_system/templates",
    "agent_system/src",
    "dashboard/AIOS-Dashboard-v3.4",
    "core",
    "sdk",
]

# 核心脚本（必须包含）
CORE_SCRIPTS = [
    "agent_system/agents.json",
    "agent_system/heartbeat_v5.py",
    "agent_system/memory_server.py",
    "agent_system/task_queue.py",
    "agent_system/task_executor.py",
    "agent_system/low_success_regeneration.py",
    "agent_system/experience_learner_v3.py",
    "agent_system/evolution_fusion.py",
    "agent_system/kun_strategy.py",
]

# 黑名单（不打包）
BLACKLIST = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.jsonl",
    ".pytest_cache",
    ".git",
    ".vscode",
    ".idea",
    "*.db",
    "lancedb*",
    "experience_db.lance",
]

def should_ignore(path: Path) -> bool:
    """检查路径是否应该被忽略"""
    path_str = str(path)
    for pattern in BLACKLIST:
        if pattern.startswith("*"):
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            return True
    return False

def copy_file(src: Path, dst: Path):
    """复制文件"""
    if should_ignore(src):
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  ✅ {src.relative_to(SOURCE_DIR)}")

def copy_dir(src: Path, dst: Path):
    """递归复制目录"""
    if should_ignore(src):
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_file():
            copy_file(item, dst / item.name)
        elif item.is_dir() and not should_ignore(item):
            copy_dir(item, dst / item.name)

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  AIOS Portable 打包工具 v1.0                                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # 清理旧包
    if PORTABLE_DIR.exists():
        print("[1/4] 清理旧包...")
        shutil.rmtree(PORTABLE_DIR)
        print("  ✅ 旧包已删除")
    
    # 创建目录
    print()
    print("[2/4] 创建目录结构...")
    PORTABLE_DIR.mkdir(parents=True, exist_ok=True)
    (PORTABLE_DIR / "agent_system" / "config").mkdir(parents=True, exist_ok=True)
    (PORTABLE_DIR / "agent_system" / "data").mkdir(parents=True, exist_ok=True)
    (PORTABLE_DIR / "agent_system" / "logs").mkdir(parents=True, exist_ok=True)
    (PORTABLE_DIR / "agent_system" / "memory").mkdir(parents=True, exist_ok=True)
    print("  ✅ 目录结构已创建")

    # 复制核心文件
    print()
    print("[3/4] 复制核心文件...")
    for file in CORE_FILES:
        src = SOURCE_DIR / file
        if src.exists():
            copy_file(src, PORTABLE_DIR / file)

    # 复制核心脚本
    for script in CORE_SCRIPTS:
        src = SOURCE_DIR / script
        if src.exists():
            copy_file(src, PORTABLE_DIR / script)

    # 复制核心目录
    for dir_path in CORE_DIRS:
        src = SOURCE_DIR / dir_path
        if src.exists():
            print(f"  📁 {dir_path}")
            copy_dir(src, PORTABLE_DIR / dir_path)

    # 复制启动脚本（已经在 AIOS-Portable 里了）
    print()
    print("[4/4] 验证启动脚本...")
    required_scripts = ["install.bat", "start.bat", "stop.bat", "README.md"]
    for script in required_scripts:
        if (PORTABLE_DIR / script).exists():
            print(f"  ✅ {script}")
        else:
            print(f"  ❌ {script} 缺失！")

    # 打包成 ZIP
    print()
    print("[5/5] 打包成 ZIP...")
    timestamp = datetime.now().strftime("%Y%m%d")
    zip_name = f"AIOS-Portable-Windows-{timestamp}.zip"
    zip_path = SOURCE_DIR / zip_name
    
    shutil.make_archive(
        str(zip_path.with_suffix("")),
        "zip",
        PORTABLE_DIR
    )
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ {zip_name} ({size_mb:.1f} MB)")

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ✅ 打包完成！                                               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"输出文件：{zip_path}")
    print(f"文件夹：{PORTABLE_DIR}")
    print()
    print("下一步：")
    print("1. 解压 ZIP 到任意目录")
    print("2. 双击 install.bat 安装")
    print("3. 双击 start.bat 启动")

if __name__ == "__main__":
    main()
