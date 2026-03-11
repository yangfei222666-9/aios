"""
回归测试：Code_Reviewer 默认排除 _deprecated/ 目录

背景（2026-03-11）：
Code_Reviewer 扫描 core/ 时把 _deprecated/ 中的旧文件当成"丢失的核心模块"，
导致误报 HIGH 问题。修复方式是让 read_target_files 默认排除 _deprecated/。

这条测试确保这个误报不会再回来。
"""

import sys
from pathlib import Path

# 让 import 能找到 run_code_reviewer
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_code_reviewer import read_target_files, EXCLUDED_DIRS, AIOS_ROOT


def test_deprecated_dir_excluded_from_root_scan():
    """扫描 agent_system 根目录时，_deprecated/ 中的文件不应出现"""
    deprecated_dir = AIOS_ROOT / "_deprecated"
    if not deprecated_dir.exists():
        print("  ⚠️  _deprecated/ 目录不存在，跳过")
        return

    # 扫描整个 agent_system 根目录
    files = read_target_files(".", exclude_dirs=EXCLUDED_DIRS)
    filenames = list(files.keys())

    deprecated_files = [f for f in filenames if "_deprecated" in f]
    assert len(deprecated_files) == 0, \
        f"_deprecated/ 中的文件不应被扫描到，但发现: {deprecated_files}"


def test_deprecated_files_exist_but_hidden():
    """_deprecated/ 中确实有文件（unified_router.py 等），但扫描不到"""
    deprecated_dir = AIOS_ROOT / "_deprecated"
    if not deprecated_dir.exists():
        print("  ⚠️  _deprecated/ 目录不存在，跳过")
        return

    # 确认 _deprecated/ 中有 .py 文件
    deprecated_py_files = list(deprecated_dir.glob("*.py"))
    assert len(deprecated_py_files) > 0, \
        f"_deprecated/ 中应该有 .py 文件，但没有找到"

    # 扫描根目录，不应包含 _deprecated/ 路径下的文件
    files = read_target_files(".", exclude_dirs=EXCLUDED_DIRS)
    deprecated_in_results = [f for f in files.keys() if "_deprecated" in f]
    assert len(deprecated_in_results) == 0, \
        f"_deprecated/ 中的文件不应出现在扫描结果中: {deprecated_in_results}"


def test_core_dir_excludes_deprecated():
    """如果 core/ 下有 _deprecated/ 子目录，也应被排除"""
    core_deprecated = AIOS_ROOT / "core" / "_deprecated"
    if not core_deprecated.exists():
        # core/ 下没有 _deprecated/，这也是正确的
        print("  ⚠️  core/_deprecated/ 不存在，跳过（正常）")
        return

    files = read_target_files("core", exclude_dirs=EXCLUDED_DIRS)
    deprecated_files = [f for f in files.keys() if "_deprecated" in f]
    assert len(deprecated_files) == 0, \
        f"core/_deprecated/ 中的文件不应被扫描到: {deprecated_files}"


def test_excluded_dirs_constant():
    """EXCLUDED_DIRS 常量必须包含 _deprecated 和 __pycache__"""
    assert "_deprecated" in EXCLUDED_DIRS, \
        f"EXCLUDED_DIRS 必须包含 '_deprecated'，实际: {EXCLUDED_DIRS}"
    assert "__pycache__" in EXCLUDED_DIRS, \
        f"EXCLUDED_DIRS 必须包含 '__pycache__'，实际: {EXCLUDED_DIRS}"


def test_pycache_excluded():
    """__pycache__/ 中的文件不应出现在扫描结果中"""
    files = read_target_files(".", exclude_dirs=EXCLUDED_DIRS)
    pycache_files = [f for f in files.keys() if "__pycache__" in f]
    assert len(pycache_files) == 0, \
        f"__pycache__/ 中的文件不应被扫描到: {pycache_files}"


def test_explicit_empty_exclude_includes_deprecated():
    """传入空 exclude_dirs 时，_deprecated/ 中的文件应该被扫描到"""
    deprecated_dir = AIOS_ROOT / "_deprecated"
    if not deprecated_dir.exists():
        print("  ⚠️  _deprecated/ 目录不存在，跳过")
        return

    files = read_target_files("_deprecated", exclude_dirs=set())
    assert len(files) > 0, \
        f"传入空 exclude_dirs 时，_deprecated/ 中的文件应该被扫描到"


if __name__ == "__main__":
    tests = [
        test_deprecated_dir_excluded_from_root_scan,
        test_deprecated_files_exist_but_hidden,
        test_core_dir_excludes_deprecated,
        test_excluded_dirs_constant,
        test_pycache_excluded,
        test_explicit_empty_exclude_includes_deprecated,
    ]

    passed = 0
    failed = 0
    skipped = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ⚠️  {test.__name__}: {e}")
            skipped += 1

    print(f"\n结果: {passed} passed, {failed} failed, {skipped} skipped")
    sys.exit(1 if failed else 0)
