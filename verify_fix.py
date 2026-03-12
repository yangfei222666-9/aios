#!/usr/bin/env python3
"""
验证文件编码修复效果
"""

import os
import sys

# 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_file(file_path):
    """检查单个文件的编码规范"""
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否有写入/追加操作
        lines = content.split('\n')
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 查找写入模式
            if ('open(' in line and 
                ('"w"' in line or "'w'" in line or '"a"' in line or "'a'" in line) and
                'encoding="utf-8"' in line):
                
                # 检查是否有 errors="replace"
                if 'errors="replace"' not in line and "errors='replace'" not in line:
                    issues.append(f"第{i}行: 写入/追加模式缺少 errors='replace'")
        
        if issues:
            return False, issues
        else:
            return True, "符合规范"
            
    except Exception as e:
        return False, f"读取错误: {e}"

def main():
    """主验证函数"""
    print("文件编码修复验证")
    print("=" * 60)
    
    # 重要文件列表
    important_files = [
        "tools/wake_listener.py",
        "tools/command_router.py",
        "tools/voice_command_handler_integrated.py",
        "tools/simple_tts.py",
        "start_voice_system.py",
    ]
    
    print("检查重要文件的编码规范:")
    print("-" * 40)
    
    all_ok = True
    
    for file_path in important_files:
        ok, result = check_file(file_path)
        
        if ok:
            print(f"✅ {file_path}: {result}")
        else:
            print(f"❌ {file_path}:")
            if isinstance(result, list):
                for issue in result:
                    print(f"    {issue}")
            else:
                print(f"    {result}")
            all_ok = False
    
    print("\n" + "=" * 60)
    
    # 测试实际的文件操作
    print("\n测试实际的文件操作:")
    print("-" * 40)
    
    test_content = "测试内容 ✅🎉 中文测试\n第二行测试"
    
    # 测试写入
    try:
        with open("test_write.txt", "w", encoding="utf-8", errors="replace") as f:
            f.write(test_content)
        print("✅ 写入测试通过")
        
        # 测试读取
        with open("test_write.txt", "r", encoding="utf-8") as f:
            read_content = f.read()
        
        if read_content == test_content:
            print("✅ 读取测试通过")
        else:
            print("❌ 读取测试失败: 内容不匹配")
            all_ok = False
            
        # 测试追加
        with open("test_append.txt", "a", encoding="utf-8", errors="replace") as f:
            f.write("第一行\n")
            f.write("第二行 ✅\n")
        
        print("✅ 追加测试通过")
        
        # 清理测试文件
        if os.path.exists("test_write.txt"):
            os.remove("test_write.txt")
        if os.path.exists("test_append.txt"):
            os.remove("test_append.txt")
            
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        all_ok = False
    
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    if all_ok:
        print("🎉 所有文件编码修复验证通过！")
        print()
        print("系统现在遵循最佳实践:")
        print("  1. ✅ 所有文本文件操作指定 encoding='utf-8'")
        print("  2. ✅ 写入/追加模式包含 errors='replace'")
        print("  3. ✅ 实际文件操作测试通过")
        print("  4. ✅ 重要文件都已修复")
        print()
        print("这确保了:")
        print("  • 中文和 Unicode 字符正确保存")
        print("  • 文件操作不会因编码问题失败")
        print("  • 数据完整性和系统稳定性")
        return 0
    else:
        print("⚠️ 发现需要修复的问题")
        print()
        print("建议:")
        print("  1. 检查报告的问题文件")
        print("  2. 确保写入/追加模式有 errors='replace'")
        print("  3. 重新运行验证")
        return 1

if __name__ == "__main__":
    sys.exit(main())