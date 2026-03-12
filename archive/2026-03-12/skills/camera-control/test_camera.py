#!/usr/bin/env python3
"""
测试 Camera Control Skill
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def test_snap():
    """测试拍照功能"""
    print("\n=== 测试拍照功能 ===")
    
    cmd = [sys.executable, "camera.py", "snap", "--output", "./test_snapshots"]
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ 拍照测试通过")
        print(stdout)
        return True
    else:
        print("❌ 拍照测试失败")
        print(stderr)
        return False


def test_watch():
    """测试监控模式"""
    print("\n=== 测试监控模式 ===")
    
    # 只监控10秒，拍2张照片
    cmd = [
        sys.executable, "camera.py", "watch",
        "--output", "./test_snapshots",
        "--interval", "5",
        "--duration", "10"
    ]
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ 监控模式测试通过")
        print(stdout)
        return True
    else:
        print("❌ 监控模式测试失败")
        print(stderr)
        return False


def test_analyze():
    """测试分析功能"""
    print("\n=== 测试分析功能 ===")
    
    cmd = [
        sys.executable, "camera.py", "analyze",
        "--output", "./test_snapshots",
        "--prompt", "测试画面分析"
    ]
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ 分析功能测试通过")
        print(stdout)
        return True
    else:
        print("❌ 分析功能测试失败")
        print(stderr)
        return False


def main():
    print("Camera Control Skill - 测试套件")
    print("=" * 50)
    
    # 检查依赖
    try:
        import cv2
        print("✅ opencv-python 已安装")
    except ImportError:
        print("❌ opencv-python 未安装，请运行: pip install opencv-python")
        return 1
    
    # 运行测试
    results = []
    results.append(("拍照", test_snap()))
    results.append(("监控", test_watch()))
    results.append(("分析", test_analyze()))
    
    # 统计结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
