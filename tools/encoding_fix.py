#!/usr/bin/env python3
"""
编码修复工具
解决 Windows 控制台编码问题
"""

import sys
import os
import io
from typing import Optional

def fix_encoding():
    """
    修复系统编码配置
    
    在 Windows 上，默认编码可能是 GBK，这会导致 Unicode 字符显示问题。
    此函数强制使用 UTF-8 编码。
    """
    # 检查当前平台
    if sys.platform == "win32":
        try:
            # 方法1: 重新配置标准输出
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            
            print(f"[编码修复] 标准输出已配置为 UTF-8")
            return True
            
        except AttributeError:
            # Python 3.7 以下版本不支持 reconfigure
            try:
                # 方法2: 替换标准输出
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
                
                print(f"[编码修复] 标准输出已替换为 UTF-8 包装器")
                return True
                
            except Exception as e:
                print(f"[编码修复警告] 无法配置编码: {e}")
                return False
    else:
        # 非 Windows 平台通常使用 UTF-8
        print(f"[编码修复] 非 Windows 平台，当前编码: {sys.stdout.encoding}")
        return True

def set_environment_encoding():
    """
    设置环境变量以使用 UTF-8 编码
    """
    # 设置 Python 相关环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 设置通用环境变量
    if sys.platform == "win32":
        os.environ['CHCP'] = '65001'  # UTF-8 代码页
    
    print(f"[环境编码] 已设置环境变量支持 UTF-8")

def safe_print(text: str, file=sys.stdout, **kwargs):
    """
    安全的打印函数，处理编码问题
    
    参数:
        text: 要打印的文本
        file: 输出文件（默认 stdout）
        **kwargs: 其他 print 参数
    """
    try:
        print(text, file=file, **kwargs)
    except UnicodeEncodeError:
        # 编码错误时使用 errors='replace'
        if hasattr(file, 'reconfigure'):
            file.reconfigure(errors='replace')
            print(text, file=file, **kwargs)
        else:
            # 尝试使用替代编码
            try:
                encoded = text.encode('utf-8', errors='replace').decode('utf-8')
                print(encoded, file=file, **kwargs)
            except:
                # 最后的手段：替换无法编码的字符
                safe_text = text.encode('ascii', errors='replace').decode('ascii')
                print(safe_text, file=file, **kwargs)

def get_safe_string(text: str) -> str:
    """
    获取安全的字符串表示，用于日志和输出
    
    参数:
        text: 输入文本
    
    返回:
        安全的字符串
    """
    if not isinstance(text, str):
        text = str(text)
    
    try:
        # 尝试正常编码
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        # 替换无法编码的字符
        return text.encode('utf-8', errors='replace').decode('utf-8')

def test_encoding_fix():
    """测试编码修复"""
    print("编码修复测试")
    print("=" * 60)
    
    # 测试各种 Unicode 字符
    test_chars = [
        "✅ 测试通过",
        "🎉 庆祝成功",
        "🎤 语音系统",
        "✨ 完美运行",
        "中文测试",
        "English test",
        "混合 Mixed 文本",
    ]
    
    print("原始打印测试:")
    for char in test_chars:
        try:
            print(f"  测试: {char}")
        except UnicodeEncodeError as e:
            print(f"  错误: {e} - 字符: {repr(char)}")
    
    print("\n安全打印测试:")
    for char in test_chars:
        safe_print(f"  测试: {char}")
    
    print("\n安全字符串测试:")
    for char in test_chars:
        safe_str = get_safe_string(char)
        print(f"  原始: {repr(char)}")
        print(f"  安全: {repr(safe_str)}")
    
    print("\n" + "=" * 60)
    print("编码信息:")
    print(f"  平台: {sys.platform}")
    print(f"  默认编码: {sys.getdefaultencoding()}")
    print(f"  文件系统编码: {sys.getfilesystemencoding()}")
    print(f"  Stdout 编码: {sys.stdout.encoding}")
    print(f"  Stderr 编码: {sys.stderr.encoding}")
    
    return True

def apply_encoding_fix_to_scripts():
    """
    为现有脚本应用编码修复
    
    返回:
        修改的脚本列表
    """
    scripts_to_fix = [
        "tools/wake_listener.py",
        "tools/command_router.py",
        "tools/voice_command_handler_integrated.py",
        "tools/unicode_sanitizer.py",
        "tools/simple_tts.py",
    ]
    
    modified = []
    
    for script_path in scripts_to_fix:
        if not os.path.exists(script_path):
            continue
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经包含编码修复
            if 'sys.stdout.reconfigure' in content or 'fix_encoding' in content:
                continue
            
            # 在文件开头添加编码修复
            lines = content.split('\n')
            
            # 找到 shebang 之后的位置
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('#!/'):
                    insert_index = i + 1
                elif line.strip() and insert_index == 0:
                    insert_index = i
            
            # 插入编码修复代码
            encoding_fix = '''# 编码修复
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
'''
            
            lines.insert(insert_index, encoding_fix)
            new_content = '\n'.join(lines)
            
            with open(script_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(new_content)
            
            modified.append(script_path)
            print(f"[编码修复] 已修复: {script_path}")
            
        except Exception as e:
            print(f"[编码修复错误] 无法修复 {script_path}: {e}")
    
    return modified

if __name__ == "__main__":
    # 应用编码修复
    fix_encoding()
    set_environment_encoding()
    
    # 测试
    test_encoding_fix()
    
    # 询问是否修复现有脚本
    print("\n" + "=" * 60)
    response = input("是否要修复现有脚本的编码问题？(y/n): ")
    
    if response.lower() == 'y':
        modified = apply_encoding_fix_to_scripts()
        if modified:
            print(f"\n已修复 {len(modified)} 个脚本:")
            for script in modified:
                print(f"  • {script}")
        else:
            print("\n所有脚本都已包含编码修复或无需修复")
    
    print("\n编码修复完成！")