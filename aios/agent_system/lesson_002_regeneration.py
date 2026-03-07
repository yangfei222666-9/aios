#!/usr/bin/env python3
"""
Lesson-002 Regeneration: Dependency Error Recovery
任务：安装pandas，但pip因网络问题失败

改进策略：
1. 在任务开始前验证所有依赖
2. 使用虚拟环境隔离依赖
3. 明确指定依赖版本
4. 添加网络检查和重试机制
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import time

# 配置
WORKSPACE = Path(r"C:\Users\A\.openclaw\workspace")
AIOS_DIR = WORKSPACE / "aios" / "agent_system"
EXPERIENCE_LIB = AIOS_DIR / "experience_library.jsonl"

def check_network_connectivity():
    """检查网络连接"""
    print("[CHECK] 检查网络连接...")
    try:
        # 尝试ping PyPI
        result = subprocess.run(
            ["ping", "-n", "1", "pypi.org"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("  [OK] 网络连接正常")
            return True
        else:
            print("  [WARN] 无法连接到 pypi.org")
            return False
    except Exception as e:
        print(f"  [ERROR] 网络检查失败: {e}")
        return False

def check_pip_available():
    """检查pip是否可用"""
    print("[CHECK] 检查pip是否可用...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  [OK] pip版本: {result.stdout.strip()}")
            return True
        else:
            print(f"  [ERROR] pip不可用: {result.stderr}")
            return False
    except Exception as e:
        print(f"  [ERROR] pip检查失败: {e}")
        return False

def check_package_installed(package_name):
    """检查包是否已安装"""
    print(f"[CHECK] 检查 {package_name} 是否已安装...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # 提取版本信息
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    print(f"  [OK] {package_name} 已安装，版本: {version}")
                    return True, version
        print(f"  [INFO] {package_name} 未安装")
        return False, None
    except Exception as e:
        print(f"  [ERROR] 检查失败: {e}")
        return False, None

def install_package_with_retry(package_name, version=None, max_retries=3):
    """
    安装包（带重试机制）
    
    Args:
        package_name: 包名
        version: 指定版本（可选）
        max_retries: 最大重试次数
    
    Returns:
        (success: bool, message: str)
    """
    package_spec = f"{package_name}=={version}" if version else package_name
    print(f"[INSTALL] 安装 {package_spec}...")
    
    for attempt in range(1, max_retries + 1):
        print(f"  [尝试 {attempt}/{max_retries}]")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_spec, "--timeout", "30"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"  [OK] {package_spec} 安装成功")
                return True, f"Successfully installed {package_spec}"
            else:
                error_msg = result.stderr.strip()
                print(f"  [ERROR] 安装失败: {error_msg}")
                
                # 如果是网络错误，等待后重试
                if "network" in error_msg.lower() or "timeout" in error_msg.lower():
                    if attempt < max_retries:
                        wait_time = attempt * 2  # 递增等待时间
                        print(f"  [WAIT] 等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            print(f"  [ERROR] 安装超时")
            if attempt < max_retries:
                print(f"  [WAIT] 等待 2 秒后重试...")
                time.sleep(2)
                continue
            return False, "Installation timeout"
        except Exception as e:
            print(f"  [ERROR] 安装异常: {e}")
            return False, str(e)
    
    return False, f"Failed after {max_retries} attempts"

def verify_installation(package_name):
    """验证安装是否成功（通过导入测试）"""
    print(f"[VERIFY] 验证 {package_name} 安装...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {package_name}; print({package_name}.__version__)"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  [OK] {package_name} 可正常导入，版本: {version}")
            return True, version
        else:
            print(f"  [ERROR] 导入失败: {result.stderr}")
            return False, None
    except Exception as e:
        print(f"  [ERROR] 验证失败: {e}")
        return False, None

def save_experience(task_id, success, details):
    """保存执行经验到experience_library"""
    experience = {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'error_type': 'dependency_error',
        'regeneration': True,
        'success': success,
        'details': details,
        'improvements': [
            '在任务开始前验证所有依赖',
            '添加网络连接检查',
            '实现重试机制（最多3次）',
            '明确指定依赖版本',
            '添加安装后验证'
        ]
    }
    
    with open(EXPERIENCE_LIB, 'a', encoding='utf-8') as f:
        f.write(json.dumps(experience, ensure_ascii=False) + '\n')
    
    print(f"[SAVE] 经验已保存到 {EXPERIENCE_LIB}")

def main():
    """主函数：执行lesson-002重生任务"""
    print("=" * 70)
    print("Lesson-002 Regeneration: Dependency Error Recovery")
    print("任务：安装pandas（带依赖验证和重试机制）")
    print("=" * 70)
    print()
    
    task_id = "lesson-002"
    start_time = time.time()
    
    # Step 1: 前置检查
    print("[PHASE 1] 前置依赖检查")
    print("-" * 70)
    
    # 1.1 检查网络
    network_ok = check_network_connectivity()
    if not network_ok:
        print("\n[FAIL] 网络连接失败，无法继续")
        save_experience(task_id, False, {
            'phase': 'network_check',
            'error': 'Network connectivity failed'
        })
        return False
    
    # 1.2 检查pip
    pip_ok = check_pip_available()
    if not pip_ok:
        print("\n[FAIL] pip不可用，无法继续")
        save_experience(task_id, False, {
            'phase': 'pip_check',
            'error': 'pip not available'
        })
        return False
    
    print()
    
    # Step 2: 检查pandas是否已安装
    print("[PHASE 2] 检查目标包")
    print("-" * 70)
    
    installed, current_version = check_package_installed("pandas")
    
    if installed:
        print(f"\n[INFO] pandas 已安装（版本 {current_version}），跳过安装")
        
        # 验证可用性
        verify_ok, _ = verify_installation("pandas")
        if verify_ok:
            elapsed = time.time() - start_time
            print(f"\n[SUCCESS] 任务完成（耗时 {elapsed:.2f}s）")
            save_experience(task_id, True, {
                'phase': 'already_installed',
                'version': current_version,
                'elapsed_time': elapsed
            })
            return True
    
    print()
    
    # Step 3: 安装pandas（带重试）
    print("[PHASE 3] 安装pandas（带重试机制）")
    print("-" * 70)
    
    # 指定稳定版本（避免最新版本可能的兼容性问题）
    target_version = "2.0.3"
    success, message = install_package_with_retry("pandas", version=target_version, max_retries=3)
    
    if not success:
        print(f"\n[FAIL] 安装失败: {message}")
        save_experience(task_id, False, {
            'phase': 'installation',
            'error': message,
            'target_version': target_version
        })
        return False
    
    print()
    
    # Step 4: 验证安装
    print("[PHASE 4] 验证安装")
    print("-" * 70)
    
    verify_ok, installed_version = verify_installation("pandas")
    
    if not verify_ok:
        print("\n[FAIL] 安装验证失败")
        save_experience(task_id, False, {
            'phase': 'verification',
            'error': 'Import test failed'
        })
        return False
    
    # Step 5: 完成
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"[SUCCESS] Lesson-002 重生任务完成！")
    print(f"  - pandas 版本: {installed_version}")
    print(f"  - 总耗时: {elapsed:.2f}s")
    print("=" * 70)
    
    save_experience(task_id, True, {
        'phase': 'completed',
        'version': installed_version,
        'elapsed_time': elapsed,
        'checks_passed': ['network', 'pip', 'installation', 'verification']
    })
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
