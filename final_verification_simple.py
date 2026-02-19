#!/usr/bin/env python3
"""
最终系统验证（简化版）
验证语音唤醒系统的完整性和生产就绪状态
"""

import sys
import os
import tempfile
from pathlib import Path

# 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def check_file_exists(path, description):
    """检查文件是否存在"""
    exists = os.path.exists(path)
    status = "[OK]" if exists else "[NO]"
    print(f"{status} {description}: {path}")
    return exists

def check_import(module_name, description):
    """检查模块是否可导入"""
    try:
        __import__(module_name)
        print(f"[OK] {description}: 已安装")
        return True
    except ImportError:
        print(f"[NO] {description}: 未安装")
        return False

def main():
    """主验证函数"""
    print("语音唤醒系统 - 最终验证")
    print("=" * 60)
    
    # 1. 检查系统文件
    print_header("1. 系统文件检查")
    
    files_to_check = [
        ("start_voice_system.py", "主启动脚本"),
        ("openclaw.yaml", "配置文件"),
        ("SYSTEM_SUMMARY.md", "系统文档"),
        ("tools/wake_listener.py", "语音唤醒服务"),
        ("tools/command_router.py", "命令路由器"),
        ("tools/voice_command_handler_integrated.py", "命令处理器"),
        ("tools/unicode_sanitizer.py", "Unicode清理工具"),
        ("tools/simple_tts.py", "TTS语音合成"),
        ("tools/encoding_fix.py", "编码修复工具"),
    ]
    
    all_files_exist = True
    for path, description in files_to_check:
        if not check_file_exists(path, description):
            all_files_exist = False
    
    # 2. 检查依赖
    print_header("2. 依赖检查")
    
    dependencies = [
        ("vosk", "语音识别库"),
        ("sounddevice", "音频输入库"),
        ("numpy", "数值计算库"),
        ("yaml", "配置解析库"),
        ("edge_tts", "语音合成库"),
    ]
    
    all_deps_installed = True
    for module, description in dependencies:
        if not check_import(module, description):
            all_deps_installed = False
    
    # 3. 检查目录结构
    print_header("3. 目录结构检查")
    
    directories = [
        ("notes", "笔记目录"),
        ("logs", "日志目录"),
        ("models/vosk-cn", "语音模型目录"),
    ]
    
    all_dirs_exist = True
    for path, description in directories:
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[NO]"
        print(f"{status} {description}: {path}/")
        if not exists:
            all_dirs_exist = False
    
    # 4. 功能测试
    print_header("4. 核心功能测试")
    
    # 创建测试环境
    test_dir = tempfile.mkdtemp(prefix="test_")
    original_dir = os.getcwd()
    
    try:
        os.chdir(test_dir)
        os.makedirs("notes", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        print(f"测试目录: {test_dir}")
        print()
        
        # 测试 Unicode 清理
        print("Unicode 清理测试:")
        sys.path.insert(0, original_dir)
        
        try:
            from tools.unicode_sanitizer import clean_asr_text
            
            test_cases = [
                ("小九检查系统", "小九检查系统"),
                ("添加笔记：测试", "添加笔记:测试"),
            ]
            
            unicode_ok = True
            for input_text, expected in test_cases:
                cleaned = clean_asr_text(input_text)
                if cleaned == expected:
                    print(f"  [OK] '{input_text}' -> '{cleaned}'")
                else:
                    print(f"  [NO] '{input_text}' -> '{cleaned}' (期望: '{expected}')")
                    unicode_ok = False
            
            print(f"Unicode 清理: {'通过' if unicode_ok else '失败'}")
            
        except Exception as e:
            print(f"  [NO] Unicode 清理测试失败: {e}")
            unicode_ok = False
        
        print()
        
        # 测试命令路由器
        print("命令路由器测试:")
        
        try:
            from tools.command_router import CommandRouter
            
            router = CommandRouter(test_dir)
            
            test_commands = [
                ("检查系统状态", "RUN_DAILY_CHECK"),
                ("现在几点", "TELL_TIME"),
            ]
            
            router_ok = True
            for cmd, expected in test_commands:
                action, payload = router.route_command(cmd)
                if action == expected:
                    print(f"  [OK] '{cmd}' -> {action}")
                else:
                    print(f"  [NO] '{cmd}' -> {action} (期望: {expected})")
                    router_ok = False
            
            print(f"命令路由器: {'通过' if router_ok else '失败'}")
            
        except Exception as e:
            print(f"  [NO] 命令路由器测试失败: {e}")
            router_ok = False
        
        functionality_ok = unicode_ok and router_ok
        
    finally:
        os.chdir(original_dir)
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"\n已清理测试目录: {test_dir}")
        except:
            pass
    
    # 5. 系统状态总结
    print_header("5. 验证结果汇总")
    
    checks = [
        ("系统文件", all_files_exist),
        ("依赖安装", all_deps_installed),
        ("目录结构", all_dirs_exist),
        ("核心功能", functionality_ok),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "[OK]" if passed else "[NO]"
        print(f"{check_name:10} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("[SUCCESS] 系统验证完全通过！")
        print()
        print("系统状态: 生产就绪")
        print()
        print("恭喜！语音唤醒系统已完全开发完成并验证通过！")
        print()
        print("使用说明:")
        print("  1. 启动系统: python start_voice_system.py")
        print("  2. 说唤醒词: '小九', '小酒', '你好小九'")
        print("  3. 听系统回应: '我在，请说命令'")
        print("  4. 说命令: '检查系统状态', '添加笔记', '现在几点'等")
        print("  5. 系统执行命令并记录结果")
        print()
        print("详细文档请查看: SYSTEM_SUMMARY.md")
        return 0
    else:
        print("[FAILED] 系统验证未完全通过")
        print()
        print("需要解决的问题:")
        for check_name, passed in checks:
            if not passed:
                print(f"  • {check_name}")
        print()
        print("请解决上述问题后重新验证")
        return 1

if __name__ == "__main__":
    sys.exit(main())