#!/usr/bin/env python3
"""
自动修复文件编码问题
为写入/追加模式的文件操作添加 errors="replace" 参数
"""

import os
import re
import sys
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

def fix_file_operations(file_path: Path):
    """修复单个文件的文件操作编码"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # 修复写入模式
        # 匹配: open(..., "w", encoding="utf-8")
        # 替换为: open(..., "w", encoding="utf-8", errors="replace")
        pattern_w = r'open\(([^)]*)"w"([^)]*encoding=["\']utf-8["\'])([^)]*)\)'
        replacement_w = r'open(\1"w"\2, errors="replace"\3)'
        content = re.sub(pattern_w, replacement_w, content)
        
        # 修复单引号版本
        pattern_w_single = r"open\(([^)]*)'w'([^)]*encoding=['\"]utf-8['\"])([^)]*)\)"
        replacement_w_single = r"open(\1'w'\2, errors='replace'\3)"
        content = re.sub(pattern_w_single, replacement_w_single, content)
        
        # 修复追加模式
        pattern_a = r'open\(([^)]*)"a"([^)]*encoding=["\']utf-8["\'])([^)]*)\)'
        replacement_a = r'open(\1"a"\2, errors="replace"\3)'
        content = re.sub(pattern_a, replacement_a, content)
        
        # 修复单引号追加版本
        pattern_a_single = r"open\(([^)]*)'a'([^)]*encoding=['\"]utf-8['\"])([^)]*)\)"
        replacement_a_single = r"open(\1'a'\2, errors='replace'\3)"
        content = re.sub(pattern_a_single, replacement_a_single, content)
        
        # 检查是否有变化
        if content != original_content:
            # 备份原文件
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            with open(backup_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(original_content)
            
            # 写入修复后的内容
            with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            
            return True, backup_path
        else:
            return False, None
            
    except Exception as e:
        print(f"修复 {file_path} 时出错: {e}")
        return False, None

def main():
    """主修复函数"""
    print("文件编码自动修复工具")
    print("=" * 60)
    print("为写入/追加模式的文件操作添加 errors='replace' 参数")
    print()
    
    # 需要修复的文件列表（从检查结果中获取）
    files_to_fix = [
        "tools/command_router.py",
        "tools/direct_transcribe.py",
        "tools/encoding_fix.py",
        "tools/simple_transcribe.py",
        "tools/simple_tts.py",
        "tools/transcribe_audio.py",
        "tools/tts_speaker.py",
        "tools/voice_command_handler.py",
        "tools/voice_command_handler_integrated.py",
        "tools/wake_listener.py",
        "final_system_verification.py",
        "test_complete_system.py",
        "test_final_audio_system.py",
        "test_integrated_system.py",
        "test_state_machine_fix.py",
        "check_file_encoding.py",
    ]
    
    fixed_files = []
    backup_files = []
    
    for file_path_str in files_to_fix:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"跳过: {file_path} (文件不存在)")
            continue
        
        print(f"处理: {file_path}...")
        fixed, backup = fix_file_operations(file_path)
        
        if fixed:
            print(f"  ✅ 已修复")
            fixed_files.append(file_path)
            if backup:
                backup_files.append(backup)
        else:
            print(f"  ⏭️ 无需修复")
    
    print("\n" + "=" * 60)
    print("修复结果汇总:")
    print("=" * 60)
    
    if fixed_files:
        print(f"✅ 已修复 {len(fixed_files)} 个文件:")
        for file_path in fixed_files:
            print(f"  • {file_path}")
        
        if backup_files:
            print(f"\n📁 创建了 {len(backup_files)} 个备份文件:")
            for backup in backup_files:
                print(f"  • {backup}")
            print("\n提示: 可以安全删除 .bak 备份文件")
        
        print("\n🎉 文件编码修复完成！")
        print()
        print("修复内容:")
        print("  1. 为写入模式添加 errors='replace'")
        print("  2. 为追加模式添加 errors='replace'")
        print("  3. 确保所有文本文件操作都有错误处理")
        print()
        print("现在可以运行检查工具验证修复:")
        print("  python check_file_encoding.py")
        return 0
    else:
        print("✅ 所有文件都已符合编码规范，无需修复")
        return 0

if __name__ == "__main__":
    sys.exit(main())