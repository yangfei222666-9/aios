"""
AIOS v1.2 打包脚本
"""
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# 配置
AIOS_DIR = Path(r"C:\Users\A\.openclaw\workspace\aios")
OUTPUT_DIR = Path(r"C:\Users\A\.openclaw\workspace")
VERSION = "v1.2"
DATE = datetime.now().strftime("%Y%m%d")

# 打包文件名
PACKAGE_NAME = f"AIOS-{VERSION}-{DATE}.zip"
PACKAGE_PATH = OUTPUT_DIR / PACKAGE_NAME

print(f"📦 开始打包 AIOS {VERSION}...")
print(f"源目录: {AIOS_DIR}")
print(f"输出: {PACKAGE_PATH}\n")

# 需要打包的文件
include_patterns = [
    "*.py",
    "*.md",
    "*.json",
    "*.txt",
    "*.html",
    "*.css",
    "*.js"
]

# 排除的目录
exclude_dirs = [
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    "plans",  # 临时计划文件
    "memory/long_term.json"  # 个人记忆数据
]

# 统计
total_files = 0
total_size = 0

# 创建 ZIP
with zipfile.ZipFile(PACKAGE_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(AIOS_DIR):
        # 过滤目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            # 检查文件扩展名
            if any(file.endswith(ext.replace("*", "")) for ext in include_patterns):
                file_path = Path(root) / file
                arcname = file_path.relative_to(AIOS_DIR.parent)
                
                zipf.write(file_path, arcname)
                total_files += 1
                total_size += file_path.stat().st_size
                
                print(f"  ✓ {arcname}")

print(f"\n✅ 打包完成！")
print(f"文件数: {total_files}")
print(f"大小: {total_size / 1024 / 1024:.2f} MB")
print(f"输出: {PACKAGE_PATH}")
