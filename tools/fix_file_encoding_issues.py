#!/usr/bin/env python3
"""
修复文件编码问题
处理 BOM、换行符等编码问题
"""

import sys
import os
import re

# 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def detect_file_issues(file_path):
    """检测文件的编码问题"""
    issues = []
    
    try:
        # 读取原始字节
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        
        # 1. 检查 BOM
        if content_bytes.startswith(b'\xef\xbb\xbf'):
            issues.append(('BOM', 'UTF-8 BOM 字符'))
        
        # 2. 检查混合换行符
        has_crlf = b'\r\n' in content_bytes
        has_lf = b'\n' in content_bytes.replace(b'\r\n', b'')
        has_cr = b'\r' in content_bytes.replace(b'\r\n', b'')
        
        if has_crlf and has_lf:
            issues.append(('MIXED_LINE_ENDINGS', '混合换行符 (CRLF 和 LF)'))
        elif has_cr:
            issues.append(('CR_LINE_ENDINGS', 'CR 换行符'))
        
        # 3. 尝试解码检查编码问题
        try:
            content_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            issues.append(('UTF8_DECODE_ERROR', f'UTF-8 解码错误: {e}'))
        
        # 4. 检查文件大小
        file_size = len(content_bytes)
        if file_size > 10 * 1024 * 1024:  # 10MB
            issues.append(('LARGE_FILE', f'文件过大: {file_size:,} 字节'))
        
        return issues
        
    except Exception as e:
        return [('ERROR', f'检测文件时出错: {e}')]

def fix_file_issues(file_path, backup=True):
    """修复文件的编码问题"""
    try:
        # 读取原始字节
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        
        original_bytes = content_bytes
        changes = []
        
        # 1. 移除 BOM
        if content_bytes.startswith(b'\xef\xbb\xbf'):
            content_bytes = content_bytes[3:]
            changes.append('移除 UTF-8 BOM')
        
        # 2. 统一换行符为 LF
        # 先替换 CRLF 为 LF
        content_bytes = content_bytes.replace(b'\r\n', b'\n')
        # 再替换单独的 CR 为 LF
        content_bytes = content_bytes.replace(b'\r', b'\n')
        
        if b'\r' in original_bytes or b'\r\n' in original_bytes:
            changes.append('统一换行符为 LF')
        
        # 3. 尝试解码和重新编码
        try:
            # 解码为字符串
            content_str = content_bytes.decode('utf-8', errors='replace')
            
            # 重新编码为 UTF-8
            content_bytes = content_str.encode('utf-8')
            
            if 'replace' in content_str:
                changes.append('修复了编码错误字符')
                
        except UnicodeDecodeError as e:
            # 如果还是无法解码，使用 errors='replace'
            content_str = content_bytes.decode('utf-8', errors='replace')
            content_bytes = content_str.encode('utf-8')
            changes.append(f'强制修复编码错误: {e}')
        
        # 检查是否有变化
        if content_bytes == original_bytes:
            return False, [], None
        
        # 创建备份
        backup_path = None
        if backup:
            backup_path = file_path + '.encoding.bak'
            if not os.path.exists(backup_path):
                with open(backup_path, 'wb') as f:
                    f.write(original_bytes)
        
        # 写入修复后的文件
        with open(file_path, 'wb') as f:
            f.write(content_bytes)
        
        return True, changes, backup_path
        
    except Exception as e:
        return False, [f'修复时出错: {e}'], None

def find_files_with_issues(root_dir):
    """查找有编码问题的文件"""
    import argparse
    
    parser = argparse.ArgumentParser(description="查找和修复文件编码问题")
    parser.add_argument("path", nargs="?", default=".", help="要检查的目录或文件")
    parser.add_argument("--fix", action="store_true", help="自动修复问题")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--extensions", default=".py,.txt,.md,.yaml,.yml,.json", 
                       help="要检查的文件扩展名（逗号分隔）")
    
    args = parser.parse_args()
    
    extensions = set(ext.strip() for ext in args.extensions.split(','))
    
    files_with_issues = []
    total_files = 0
    
    print("文件编码问题检查工具")
    print("=" * 60)
    
    if os.path.isfile(args.path):
        files_to_check = [args.path]
    else:
        files_to_check = []
        for root, dirs, filenames in os.walk(args.path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    files_to_check.append(os.path.join(root, filename))
    
    print(f"检查 {len(files_to_check)} 个文件...")
    print()
    
    for file_path in files_to_check:
        total_files += 1
        
        issues = detect_file_issues(file_path)
        
        if issues:
            files_with_issues.append((file_path, issues))
            
            if args.verbose:
                print(f"❌ {file_path}:")
                for issue_type, description in issues:
                    print(f"    • {issue_type}: {description}")
            else:
                print(f"❌ {file_path}: {len(issues)} 个问题")
        elif args.verbose:
            print(f"✅ {file_path}: 通过")
    
    print()
    print("=" * 60)
    print(f"检查完成:")
    print(f"  总文件数: {total_files}")
    print(f"  有问题文件: {len(files_with_issues)}")
    
    if files_with_issues:
        print()
        print("问题文件列表:")
        for file_path, issues in files_with_issues:
            print(f"  • {file_path}")
            for issue_type, description in issues:
                print(f"      {issue_type}: {description}")
        
        if args.fix:
            print()
            print("开始自动修复...")
            print("-" * 40)
            
            fixed_files = 0
            backups_created = 0
            
            for file_path, issues in files_with_issues:
                print(f"修复: {file_path}...")
                fixed, changes, backup_path = fix_file_issues(file_path)
                
                if fixed:
                    fixed_files += 1
                    print(f"  ✅ 修复完成")
                    for change in changes:
                        print(f"     • {change}")
                    if backup_path:
                        backups_created += 1
                        print(f"     备份: {backup_path}")
                else:
                    print(f"  ⏭️ 无需修复")
            
            print()
            print("=" * 60)
            print(f"修复完成:")
            print(f"  修复文件数: {fixed_files}")
            print(f"  备份文件数: {backups_created}")
            
            if backups_created > 0:
                print()
                print("提示: 可以安全删除备份文件 (.encoding.bak)")
        
        elif not args.fix and files_with_issues:
            print()
            print("运行以下命令进行修复:")
            print(f"  python {__file__} {args.path} --fix")
    
    else:
        print()
        print("✅ 所有文件都没有编码问题")
    
    return 0

def main():
    """主函数"""
    return find_files_with_issues('.')

if __name__ == "__main__":
    sys.exit(main())