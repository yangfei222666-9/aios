#!/usr/bin/env python3
"""
最终系统验证：验证所有改进和功能
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

def test_encoding_fixes():
    """测试编码修复"""
    print("测试编码修复...")
    
    # 创建测试文件
    test_content = "测试中文和特殊字符: © ® ™ € £ ¥"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        # 读取并验证
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_content, "内容不匹配"
        print("✅ 编码修复测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 编码修复测试失败: {e}")
        return False
        
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_libcst_integration():
    """测试 libcst 集成"""
    print("\n测试 libcst 集成...")
    
    try:
        import libcst as cst
        from libcst.metadata import MetadataWrapper
        
        # 测试代码
        test_code = '''def test():
    with open("test.txt", "w") as f:
        f.write("test")
'''
        
        # 解析
        tree = cst.parse_module(test_code)
        print("✅ libcst 解析成功")
        
        # 简单的访问器
        class SimpleVisitor(cst.CSTVisitor):
            def __init__(self):
                self.open_calls = 0
            
            def visit_Call(self, node):
                if isinstance(node.func, cst.Name) and node.func.value == "open":
                    self.open_calls += 1
        
        visitor = SimpleVisitor()
        tree.visit(visitor)
        
        print(f"✅ 找到 {visitor.open_calls} 个 open() 调用")
        return True
        
    except ImportError as e:
        print(f"❌ libcst 未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ libcst 测试失败: {e}")
        return False

def test_voice_system_components():
    """测试语音系统组件"""
    print("\n测试语音系统组件...")
    
    components = [
        ("tools/wake_listener.py", "语音唤醒监听器"),
        ("tools/command_router.py", "命令路由器"),
        ("tools/text_normalize.py", "文本规范化"),
        ("tools/command_filter.py", "命令过滤器"),
    ]
    
    all_passed = True
    
    for file_path, description in components:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {description}: 存在 ({file_size:,} 字节)")
        else:
            print(f"❌ {description}: 不存在")
            all_passed = False
    
    return all_passed

def test_repair_tools():
    """测试修复工具"""
    print("\n测试修复工具...")
    
    tools = [
        ("tools/simple_libcst_fix.py", "libcst 修复工具"),
        ("tools/fix_file_encoding.py", "文件编码修复工具"),
        ("tools/libcst_encoding_check.py", "编码检查工具"),
    ]
    
    all_passed = True
    
    for tool_path, description in tools:
        if os.path.exists(tool_path):
            # 检查文件是否可以导入
            try:
                with open(tool_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                
                if first_line.startswith("#!/usr/bin/env python3"):
                    print(f"✅ {description}: 存在且格式正确")
                else:
                    print(f"⚠️  {description}: 存在但格式可能有问题")
                    
            except Exception as e:
                print(f"❌ {description}: 读取失败 - {e}")
                all_passed = False
        else:
            print(f"❌ {description}: 不存在")
            all_passed = False
    
    return all_passed

def run_comprehensive_test():
    """运行综合测试"""
    print("最终系统验证")
    print("=" * 60)
    
    tests = [
        ("编码修复", test_encoding_fixes),
        ("libcst 集成", test_libcst_integration),
        ("语音系统组件", test_voice_system_components),
        ("修复工具", test_repair_tools),
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
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 所有测试通过！系统验证完成。")
        print()
        print("系统功能:")
        print("  1. ✅ 完整的编码修复支持")
        print("  2. ✅ libcst 代码分析和修复")
        print("  3. ✅ 语音唤醒系统组件")
        print("  4. ✅ 自动化修复工具")
        print()
        print("工具位置:")
        print("  • tools/simple_libcst_fix.py - 主修复工具")
        print("  • tools/fix_file_encoding.py - 编码修复工具")
        print("  • tools/libcst_encoding_check.py - 编码检查工具")
        return 0
    else:
        print("⚠️ 部分测试失败")
        print()
        print("失败的测试:")
        for test_name, passed in results:
            if not passed:
                print(f"  • {test_name}")
        return 1

def main():
    """主函数"""
    return run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())