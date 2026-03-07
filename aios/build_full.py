#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 完整版打包脚本
1. PyInstaller --onedir 打包 aios_exe.py
2. 复制 core/dashboard/demo 等到输出目录
3. 打成 zip
"""
import subprocess
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent
DATE_STR = datetime.now().strftime("%Y%m%d")
EXE_NAME = f"AIOS-Full-{DATE_STR}"
BUILD_DIR = AIOS_ROOT / "build_full_tmp"
DIST_DIR = AIOS_ROOT / "dist_full"
OUTPUT_DIR = DIST_DIR / EXE_NAME

# 需要复制到 exe 同级目录的源码目录
COPY_DIRS = ["core", "dashboard", "agents", "observability"]

# 需要复制的单文件
COPY_FILES = [
    "config.yaml",
    "demo_file_monitor.py",
    "demo_api_health.py",
    "demo_log_analysis.py",
    "demo_simple.py",
    "warmup.py",
    "README.md",
    "LICENSE",
]

IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache",
    "htmlcov", ".coverage", ".git", "node_modules",
    "*.egg-info", "test_*.py", "*.log", "*.bak",
)


def clean():
    for d in [BUILD_DIR, DIST_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"[CLEAN] {d.name}")


def build_exe():
    print(f"\n{'='*60}")
    print(f"  Step 1: PyInstaller --onedir")
    print(f"{'='*60}")

    # 收集 hidden imports（demo 脚本依赖的模块）
    hidden = [
        "json", "pathlib", "subprocess", "datetime", "argparse",
        "uuid", "dataclasses", "typing", "shutil",
    ]

    # 收集 --add-data：把 demo 脚本和 core/ 打进 PyInstaller 包
    add_data = []
    
    # core 目录
    core_dir = AIOS_ROOT / "core"
    if core_dir.exists():
        add_data.append(f"{core_dir};core")
    
    # demo 脚本
    for f in COPY_FILES:
        fp = AIOS_ROOT / f
        if fp.exists():
            add_data.append(f"{fp};.")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--console",
        "--name", EXE_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(AIOS_ROOT),
    ]
    
    for h in hidden:
        cmd += ["--hidden-import", h]
    
    for d in add_data:
        cmd += ["--add-data", d]
    
    cmd.append(str(AIOS_ROOT / "aios_exe.py"))

    print(f"[CMD] PyInstaller --onedir --name {EXE_NAME}")
    result = subprocess.run(cmd, cwd=str(AIOS_ROOT))
    
    if result.returncode != 0:
        print("[FAIL] PyInstaller 失败")
        sys.exit(1)

    exe_path = OUTPUT_DIR / f"{EXE_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print(f"[OK] EXE: {exe_path.name} ({size_mb:.1f} MB)")
    else:
        print("[FAIL] EXE 未生成")
        sys.exit(1)


def copy_extra():
    """复制额外的目录到 exe 同级"""
    print(f"\n{'='*60}")
    print(f"  Step 2: 复制依赖目录")
    print(f"{'='*60}")

    for dirname in COPY_DIRS:
        src = AIOS_ROOT / dirname
        dst = OUTPUT_DIR / dirname
        if not src.exists():
            print(f"   [SKIP] {dirname}/ 不存在")
            continue
        if dst.exists():
            # PyInstaller 可能已经通过 --add-data 复制了
            print(f"   [EXISTS] {dirname}/ 已存在，跳过")
            continue
        shutil.copytree(src, dst, ignore=IGNORE_PATTERNS)
        fc = sum(1 for _ in dst.rglob("*") if _.is_file())
        print(f"   [OK] {dirname}/ ({fc} files)")

    # 复制单文件（如果 PyInstaller 没带进去）
    for fname in COPY_FILES:
        src = AIOS_ROOT / fname
        dst = OUTPUT_DIR / fname
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def make_zip():
    """打成 zip"""
    print(f"\n{'='*60}")
    print(f"  Step 3: 打包 ZIP")
    print(f"{'='*60}")

    zip_path = AIOS_ROOT / f"{EXE_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()

    file_count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in OUTPUT_DIR.rglob("*"):
            if fp.is_file():
                arcname = str(fp.relative_to(DIST_DIR))
                zf.write(fp, arcname)
                file_count += 1
                if file_count % 200 == 0:
                    print(f"   已打包 {file_count} 个文件...")

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] {zip_path.name} ({size_mb:.1f} MB, {file_count} files)")
    return zip_path


def main():
    print("=" * 60)
    print(f"  AIOS 完整版打包 - {EXE_NAME}")
    print("=" * 60)

    clean()
    build_exe()
    copy_extra()
    zip_path = make_zip()

    print(f"\n{'='*60}")
    print(f"  ✅ 打包完成！")
    print(f"  ZIP: {zip_path}")
    print(f"  验证: 解压后运行")
    print(f"    {EXE_NAME}\\{EXE_NAME}.exe version")
    print(f"    {EXE_NAME}\\{EXE_NAME}.exe status")
    print(f"    {EXE_NAME}\\{EXE_NAME}.exe demo")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
