"""
AIOS 完整系统打包脚本
打包整个 AIOS 系统（包括 Dashboard、Agent System、Learning 等）
"""
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

VERSION = "v1.0"
PACKAGE_NAME = f"AIOS-System-{VERSION}"

# 源目录
AIOS_ROOT = Path(__file__).parent.parent / "aios"
WORKSPACE = Path(__file__).parent.parent

# 打包目录
OUTPUT_DIR = WORKSPACE / "releases"
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 60)
print(f"📦 开始打包 AIOS 系统 {VERSION}...")
print("=" * 60)
print()

# 要打包的目录和文件
items_to_pack = [
    # 核心目录
    ("aios/dashboard", "dashboard"),
    ("aios/agent_system", "agent_system"),
    ("aios/learning", "learning"),
    ("aios/observability", "observability"),
    ("aios/core", "core"),
    
    # 脚本
    ("scripts/memory_upgrade.py", "scripts/memory_upgrade.py"),
    
    # 配置和文档
    ("AGENTS.md", "AGENTS.md"),
    ("SOUL.md", "SOUL.md"),
    ("USER.md", "USER.md"),
    ("TOOLS.md", "TOOLS.md"),
    ("HEARTBEAT.md", "HEARTBEAT.md"),
    ("MEMORY.md", "MEMORY.md"),
]

# 创建 ZIP 包
zip_path = OUTPUT_DIR / f"{PACKAGE_NAME}.zip"
print(f"📦 创建压缩包: {zip_path.name}")
print()

file_count = 0
total_size = 0

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for src, dst in items_to_pack:
        src_path = WORKSPACE / src
        
        if not src_path.exists():
            print(f"  ⚠️  跳过（不存在）: {src}")
            continue
        
        if src_path.is_file():
            # 单个文件
            arcname = f"{PACKAGE_NAME}/{dst}"
            zipf.write(src_path, arcname)
            file_count += 1
            total_size += src_path.stat().st_size
            print(f"  ✓ {dst}")
        
        elif src_path.is_dir():
            # 目录（递归）
            for file in src_path.rglob('*'):
                if file.is_file():
                    # 跳过不需要的文件
                    if any(skip in str(file) for skip in ['__pycache__', '.pyc', '.git', 'node_modules', '.DS_Store']):
                        continue
                    
                    rel_path = file.relative_to(src_path)
                    arcname = f"{PACKAGE_NAME}/{dst}/{rel_path}"
                    zipf.write(file, arcname)
                    file_count += 1
                    total_size += file.stat().st_size
            
            print(f"  ✓ {dst}/ ({len(list(src_path.rglob('*')))} 文件)")

    # 创建 README（在 ZIP 关闭前写入）
    readme_content = f"""# AIOS System {VERSION}

AIOS (AI Operating System) - 自主进化的 AI 系统

## 快速开始

1. 启动 Dashboard:
   cd dashboard
   python server.py

2. 访问: http://localhost:8888

## 系统要求
- Python 3.8+
- pip install psutil (可选)

## 版本: {VERSION} | 日期: {datetime.now().strftime('%Y-%m-%d')}
## 作者: 珊瑚海 & 小九
"""
    zipf.writestr(f"{PACKAGE_NAME}/README.md", readme_content.encode('utf-8'))
    file_count += 1

print()
print("=" * 60)
print("✅ 打包完成！")
print("=" * 60)
print(f"📦 包名：{zip_path.name}")
print(f"📁 文件数：{file_count}")
print(f"💾 原始大小：{total_size / 1024 / 1024:.2f} MB")
print(f"🗜️  压缩后：{zip_path.stat().st_size / 1024 / 1024:.2f} MB")
print(f"📍 位置：{zip_path}")
print("=" * 60)
print()
print("分享给朋友：")
print(f"1. 发送 {zip_path.name}")
print("2. 解压后运行 dashboard/server.py")
print("3. 访问 http://localhost:8888")
