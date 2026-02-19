#!/usr/bin/env python3
"""
测试 libcst 修复工具
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

def test_basic_fix():
    """测试基本修复功能"""
    print("测试 libcst 修复工具")
    print("=" * 60)
    
    # 创建测试代码
    test_code = '''#!/usr/bin/env python3
import sys

def read_file():
    with open("data.txt", "r") as f:
        return f.read()

def write_file(content):
    with open("output.txt", "w") as f:
        f.write(content)

def append_log(message):
    with open("app.log", "a") as f:
        f.write(f"{message}\\n")

def read_config():
    with open("config.yaml", "r", encoding="gbk") as f:
        import yaml
        return yaml.safe_load(f)

def binary_read():
    with open("data.bin", "rb") as f:
        return f.read()

def binary_write(data):
    with open("output.bin", "wb") as f:
        f.write(data)
'''
    
    print("测试代码（有编码问题）:")
    print(test_code)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        # 导入修复工具
        from tools.libcst_fix_encoding import fix_file
        
        print("\n应用修复...")
        changed = fix_file(temp_file, backup=False)
        
        if changed:
            print("✅ 文件已修复")
            
            # 读取修复后的内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                fixed_code = f.read()
            
            print("\n修复后的代码:")
            print(fixed_code)
            
            # 验证修复
            expected_fixes = [
                'open("data.txt", "r", encoding="utf-8")',
                'open("output.txt", "w", encoding="utf-8", errors="replace")',
                'open("app.log", "a", encoding="utf-8", errors="replace")',
                'open("config.yaml", "r", encoding="utf-8")',  # 修复了 gbk
                'open("data.bin", "rb")',  # 二进制模式不变
                'open("output.bin", "wb")',  # 二进制模式不变
            ]
            
            all_fixed = True
            for expected in expected_fixes:
                if expected in fixed_code:
                    print(f"✅ 包含: {expected}")
                else:
                    print(f"❌ 缺少: {expected}")
                    all_fixed = False
            
            return all_fixed
        else:
            print("❌ 文件未修复")
            return False
            
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_sys_reconfigure_fix():
    """测试 sys.stdout.reconfigure 修复"""
    print("\n" + "=" * 60)
    print("测试 sys.stdout.reconfigure 修复")
    print("=" * 60)
    
    test_code = '''#!/usr/bin/env python3
import sys

# 不完整的 reconfigure
sys.stdout.reconfigure()
sys.stderr.reconfigure()

# 只有 encoding
sys.stdout.reconfigure(encoding="utf-8")

# 只有 errors
sys.stderr.reconfigure(errors="replace")

# 正确的配置
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
'''
    
    print("测试代码:")
    print(test_code)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        from tools.libcst_fix_encoding import fix_file
        
        print("\n应用修复...")
        changed = fix_file(temp_file, backup=False)
        
        if changed:
            print("✅ 文件已修复")
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                fixed_code = f.read()
            
            print("\n修复后的代码:")
            print(fixed_code)
            
            # 验证修复
            expected_lines = [
                'sys.stdout.reconfigure(encoding="utf-8", errors="replace")',
                'sys.stderr.reconfigure(encoding="utf-8", errors="replace")',
                'sys.stdout.reconfigure(encoding="utf-8", errors="replace")',
                'sys.stderr.reconfigure(encoding="utf-8", errors="replace")',
                'sys.stdout.reconfigure(encoding="utf-8", errors="replace")',
            ]
            
            all_fixed = True
            lines = fixed_code.split('\n')
            for expected in expected_lines:
                if any(expected in line for line in lines):
                    print(f"✅ 包含: {expected}")
                else:
                    print(f"❌ 缺少: {expected}")
                    all_fixed = False
            
            return all_fixed
        else:
            print("❌ 文件未修复")
            return False
            
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_complex_modes():
    """测试复杂模式"""
    print("\n" + "=" * 60)
    print("测试复杂文件模式")
    print("=" * 60)
    
    test_code = '''#!/usr/bin/env python3
# 各种文件模式测试
with open("test1.txt", "w+") as f:
    pass

with open("test2.txt", "a+", encoding="utf-8") as f:
    pass

with open("test3.txt", "x", errors="replace") as f:
    pass

with open("test4.txt", "wt") as f:
    pass

with open("test5.bin", "wb") as f:
    pass

with open("test6.txt", "r+", encoding="gbk", errors="ignore") as f:
    pass
'''
    
    print("测试代码:")
    print(test_code)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        from tools.libcst_fix_encoding import fix_file
        
        print("\n应用修复...")
        changed = fix_file(temp_file, backup=False)
        
        if changed:
            print("✅ 文件已修复")
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                fixed_code = f.read()
            
            print("\n修复后的代码:")
            print(fixed_code)
            
            # 验证特定修复
            checks = [
                ('"w+"', 'encoding="utf-8", errors="replace"', True),
                ('"a+"', 'encoding="utf-8", errors="replace"', True),  # 应该添加 errors
                ('"x"', 'encoding="utf-8", errors="replace"', True),
                ('"wt"', 'encoding="utf-8", errors="replace"', True),
                ('"wb"', 'encoding="utf-8"', False),  # 二进制模式不应有编码
                ('"r+"', 'encoding="utf-8"', True),  # 应该修复 gbk
                ('"r+"', 'errors="replace"', False),  # 读取模式不需要 errors
            ]
            
            all_passed = True
            for mode, expected, should_contain in checks:
                lines = fixed_code.split('\n')
                found = any(mode in line and expected in line for line in lines)
                
                if should_contain and found:
                    print(f"✅ 模式 {mode} 正确包含 {expected}")
                elif not should_contain and not found:
                    print(f"✅ 模式 {mode} 正确不包含 {expected}")
                else:
                    print(f"❌ 模式 {mode} 验证失败")
                    all_passed = False
            
            return all_passed
        else:
            print("❌ 文件未修复")
            return False
            
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def main():
    """主测试函数"""
    print("libcst 修复工具测试套件")
    print("=" * 60)
    
    tests = [
        ("基本修复功能", test_basic_fix),
        ("sys.stdout.reconfigure 修复", test_sys_reconfigure_fix),
        ("复杂文件模式", test_complex_modes),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}")
        print("-" * 40)
        
        try:
            passed = test_func()
            status = "✅ 通过" if passed else "❌ 失败"
            results.append((test_name, passed))
            print(f"结果: {status}")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:30} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 所有测试通过！")
        print()
        print("libcst 修复工具功能:")
        print("  1. ✅ 自动修复 open() 调用的编码问题")
        print("  2. ✅ 智能处理各种文件模式")
        print("  3. ✅ 修复 sys.stdout.reconfigure 调用")
        print("  4. ✅ 正确处理二进制模式")
        print("  5. ✅ 保留现有正确参数")
        print()
        print("工具位置: tools/libcst_fix_encoding.py")
        print("使用方法: python tools/libcst_fix_encoding.py [目录]")
        return 0
    else:
        print("⚠️ 部分测试失败")
        print()
        print("失败的测试:")
        for test_name, passed in results:
            if not passed:
                print(f"  • {test_name}")
        return 1

if __name__ == "__main__":
    sys.exit(main())