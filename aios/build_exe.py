#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS EXE 打包脚本
使用 PyInstaller 将 AIOS 打包成 Windows 可执行文件
打包完成后自动将 exe + 依赖目录一起打成 zip
"""
import subprocess
import sys
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).resolve().parent
BUILD_DIR = AIOS_ROOT / "build_output"
DIST_DIR = AIOS_ROOT / "dist_exe"
DATE_STR = datetime.now().strftime("%Y%m%d")
EXE_NAME = f"AIOS-{DATE_STR}"

# exe 同级需要的依赖目录
COPY_DIRS = ["core", "dashboard", "agents", "observability"]

# exe 同级需要的单文件
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
    for d in [BUILD_DIR, DIST_DIR, AIOS_ROOT / "build", AIOS_ROOT / "dist"]:
        if d.exists():
            shutil.rmtree(d)
            print(f"[CLEAN] 删除 {d.name}")


def build():
    print(f"\n{'='*60}")
    print(f"  Step 1: PyInstaller --onefile")
    print(f"{'='*60}")

    # 收集数据文件
    datas = [
        (str(AIOS_ROOT / "config.yaml"), "."),
        (str(AIOS_ROOT / "AIOS-Friend-Edition" / "config.yaml"), "AIOS-Friend-Edition"),
        (str(AIOS_ROOT / "AIOS-Friend-Edition" / "README.txt"), "AIOS-Friend-Edition"),
    ]

    # 过滤存在的文件
    datas = [(src, dst) for src, dst in datas if Path(src).exists()]

    # 构建 --add-data 参数
    add_data_args = []
    for src, dst in datas:
        add_data_args += ["--add-data", f"{src};{dst}"]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # 单文件
        "--console",                    # 控制台窗口
        "--name", EXE_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(AIOS_ROOT),
        "--hidden-import", "json",
        "--hidden-import", "pathlib",
        "--hidden-import", "subprocess",
        "--hidden-import", "datetime",
        "--hidden-import", "argparse",
        *add_data_args,
        str(AIOS_ROOT / "aios.py"),
    ]

    print(f"[CMD] PyInstaller --onefile --name {EXE_NAME}")
    result = subprocess.run(cmd, cwd=str(AIOS_ROOT))

    if result.returncode == 0:
        exe_path = DIST_DIR / f"{EXE_NAME}.exe"
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print(f"[OK] EXE: {exe_path.name} ({size_mb:.1f} MB)")
    else:
        print(f"[FAIL] PyInstaller 失败，返回码: {result.returncode}")
        sys.exit(1)


def copy_deps():
    """复制依赖目录和文件到 dist_exe，与 exe 同级"""
    print(f"\n{'='*60}")
    print(f"  Step 2: 复制依赖目录")
    print(f"{'='*60}")

    for dirname in COPY_DIRS:
        src = AIOS_ROOT / dirname
        dst = DIST_DIR / dirname
        if not src.exists():
            print(f"   [SKIP] {dirname}/ 不存在")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=IGNORE_PATTERNS)
        fc = sum(1 for _ in dst.rglob("*") if _.is_file())
        print(f"   [OK] {dirname}/ ({fc} files)")

    for fname in COPY_FILES:
        src = AIOS_ROOT / fname
        dst = DIST_DIR / fname
        if src.exists():
            shutil.copy2(src, dst)
            print(f"   [OK] {fname}")


def make_zip():
    """将 exe + 依赖目录打成 zip"""
    print(f"\n{'='*60}")
    print(f"  Step 3: 打包 ZIP")
    print(f"{'='*60}")

    zip_path = AIOS_ROOT / f"{EXE_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()

    file_count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in DIST_DIR.rglob("*"):
            if fp.is_file():
                # zip 内路径: AIOS-YYYYMMDD/xxx
                arcname = f"{EXE_NAME}/{fp.relative_to(DIST_DIR)}"
                zf.write(fp, arcname)
                file_count += 1
                if file_count % 100 == 0:
                    print(f"   已打包 {file_count} 个文件...")

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] {zip_path.name} ({size_mb:.1f} MB, {file_count} files)")
    return zip_path


def main():
    print("=" * 60)
    print(f"  AIOS 打包 - {EXE_NAME} (exe + 依赖)")
    print("=" * 60)

    clean()
    build()
    copy_deps()
    zip_path = make_zip()

    print(f"\n{'='*60}")
    print(f"  ✅ 打包完成！")
    print(f"  ZIP: {zip_path}")
    print(f"  解压后运行:")
    print(f"    {EXE_NAME}\\{EXE_NAME}.exe version")
    print(f"    {EXE_NAME}\\{EXE_NAME}.exe status")
    print(f"    {EXE_NAME}\\{EXE_NAME}.exe demo")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
