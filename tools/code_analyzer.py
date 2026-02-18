#!/usr/bin/env python3
"""
使用 libcst 进行代码分析
检查和修复编码相关问题
"""

import sys
import os
import ast
import libcst as cst
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

class EncodingAnalyzer(cst.CSTVisitor):
    """编码分析访问器"""
    
    def __init__(self):
        self.issues = []
        self.open_calls = []
    
    def visit_Call(self, node):
        """检查 open() 调用"""
        # 检查是否是 open() 函数调用
        if isinstance(node.func, cst.Name) and node.func.value == "open":
            self.analyze_open_call(node)
    
    def analyze_open_call(self, node):
        """分析 open() 调用的参数"""
        try:
            # 获取参数信息
            args = node.args
            mode = None
            encoding = None
            errors = None
            
            # 解析参数
            for i, arg in enumerate(args):
                # 检查模式参数（通常是第一个位置参数）
                if i == 0 and isinstance(arg.value, cst.SimpleString):
                    mode = arg.value.value.strip("'\"")
                
                # 检查关键字参数
                if arg.keyword:
                    keyword = arg.keyword.value
                    if keyword == "encoding" and isinstance(arg.value, cst.SimpleString):
                        encoding = arg.value.value.strip("'\"")
                    elif keyword == "errors" and isinstance(arg.value, cst.SimpleString):
                        errors = arg.value.value.strip("'\"")
            
            # 获取行号
            position = getattr(node, 'lineno', getattr(node, 'start_line', 0))
            
            # 记录信息
            self.open_calls.append({
                "node": node,
                "mode": mode,
                "encoding": encoding,
                "errors": errors,
                "position": position
            })
            
            # 检查问题
            if mode in ("w", "a", "r"):
                # 文本模式
                if encoding and encoding != "utf-8":
                    self.issues.append({
                        "type": "wrong_encoding",
                        "position": position,
                        "message": f"open() 调用使用编码 '{encoding}' 而不是 'utf-8'",
                        "node": node
                    })
                elif not encoding and mode in ("w", "a", "r"):
                    self.issues.append({
                        "type": "missing_encoding",
                        "position": position,
                        "message": f"open() {mode} 模式缺少 encoding='utf-8'",
                        "node": node
                    })
                
                if mode in ("w", "a") and errors != "replace":
                    self.issues.append({
                        "type": "missing_errors",
                        "position": position,
                        "message": f"open() {mode} 模式缺少 errors='replace'",
                        "node": node
                    })
                    
        except Exception as e:
            print(f"分析 open() 调用时出错: {e}")

class EncodingFixer(cst.CSTTransformer):
    """编码修复转换器"""
    
    def __init__(self, issues):
        self.issues = issues
        self.fixed_count = 0
    
    def leave_Call(self, original_node, updated_node):
        """修复 open() 调用"""
        # 检查是否是 open() 函数调用
        if isinstance(original_node.func, cst.Name) and original_node.func.value == "open":
            # 检查是否有需要修复的问题
            for issue in self.issues:
                if issue["node"] == original_node:
                    if issue["type"] == "missing_errors":
                        # 添加 errors='replace' 参数
                        updated_node = self.add_errors_param(updated_node)
                        self.fixed_count += 1
                    elif issue["type"] == "wrong_encoding":
                        # 修复编码参数
                        updated_node = self.fix_encoding_param(updated_node)
                        self.fixed_count += 1
        
        return updated_node
    
    def add_errors_param(self, node):
        """添加 errors='replace' 参数"""
        # 创建新的参数
        errors_arg = cst.Arg(
            keyword=cst.Name("errors"),
            value=cst.SimpleString("'replace'"),
            equal=cst.AssignEqual()
        )
        
        # 添加到参数列表
        new_args = node.args + (errors_arg,)
        return node.with_changes(args=new_args)
    
    def fix_encoding_param(self, node):
        """修复编码参数为 utf-8"""
        # 查找并替换 encoding 参数
        new_args = []
        for arg in node.args:
            if arg.keyword and arg.keyword.value == "encoding":
                # 替换为 utf-8
                new_arg = arg.with_changes(
                    value=cst.SimpleString("'utf-8'")
                )
                new_args.append(new_arg)
            else:
                new_args.append(arg)
        
        return node.with_changes(args=tuple(new_args))

def analyze_file(file_path):
    """分析单个文件"""
    print(f"分析文件: {file_path}")
    
    try:
        # 读取文件
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析为 CST
        tree = cst.parse_module(content)
        
        # 分析
        analyzer = EncodingAnalyzer()
        tree.visit(analyzer)
        
        return analyzer.issues, analyzer.open_calls
        
    except Exception as e:
        print(f"分析 {file_path} 时出错: {e}")
        return [], []

def fix_file(file_path, issues):
    """修复单个文件"""
    if not issues:
        return False, 0
    
    try:
        # 读取文件
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析为 CST
        tree = cst.parse_module(content)
        
        # 修复
        fixer = EncodingFixer(issues)
        new_tree = tree.visit(fixer)
        
        if fixer.fixed_count > 0:
            # 备份原文件
            backup_path = file_path + ".libcst.bak"
            with open(backup_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            
            # 写入修复后的内容
            with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(new_tree.code)
            
            return True, fixer.fixed_count, backup_path
        else:
            return False, 0, None
            
    except Exception as e:
        print(f"修复 {file_path} 时出错: {e}")
        return False, 0, None

def check_sys_encoding(file_path):
    """检查 sys.stdout.reconfigure 调用"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        issues = []
        
        # 检查是否有 sys.stdout.reconfigure
        if "sys.stdout.reconfigure" in content:
            if 'encoding="utf-8"' not in content and "encoding='utf-8'" not in content:
                issues.append("sys.stdout.reconfigure 缺少 encoding='utf-8'")
            
            if 'errors="replace"' not in content and "errors='replace'" not in content:
                issues.append("sys.stdout.reconfigure 缺少 errors='replace'")
        
        return issues
        
    except Exception as e:
        print(f"检查 {file_path} 时出错: {e}")
        return []

def main():
    """主函数"""
    print("libcst 代码分析工具")
    print("=" * 60)
    print("使用 libcst 分析和修复编码问题")
    print()
    
    # 分析目录
    directories = ["tools", "."]
    
    all_issues = []
    all_open_calls = []
    files_with_issues = []
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for py_file in Path(directory).rglob("*.py"):
            issues, open_calls = analyze_file(py_file)
            
            if issues:
                files_with_issues.append(py_file)
                all_issues.extend([(py_file, issue) for issue in issues])
            
            all_open_calls.extend([(py_file, call) for call in open_calls])
    
    # 输出结果
    print("\n" + "=" * 60)
    print("分析结果汇总:")
    print("=" * 60)
    
    if all_issues:
        print(f"发现 {len(all_issues)} 个编码问题:")
        print("-" * 40)
        
        for file_path, issue in all_issues:
            print(f"{file_path}:{issue['position']}")
            print(f"  类型: {issue['type']}")
            print(f"  问题: {issue['message']}")
            print()
    else:
        print("✅ 未发现编码问题")
    
    print(f"\n分析 {len(all_open_calls)} 个 open() 调用:")
    print("-" * 40)
    
    # 统计 open() 调用类型
    mode_stats = {}
    for file_path, call in all_open_calls:
        mode = call["mode"] or "unknown"
        mode_stats[mode] = mode_stats.get(mode, 0) + 1
    
    for mode, count in mode_stats.items():
        print(f"  {mode} 模式: {count} 次")
    
    # 检查 sys.stdout.reconfigure
    print("\n检查 sys.stdout.reconfigure 调用:")
    print("-" * 40)
    
    sys_issues = []
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for py_file in Path(directory).rglob("*.py"):
            issues = check_sys_encoding(py_file)
            if issues:
                sys_issues.append((py_file, issues))
    
    if sys_issues:
        print("发现 sys.stdout.reconfigure 问题:")
        for file_path, issues in sys_issues:
            print(f"{file_path}:")
            for issue in issues:
                print(f"  • {issue}")
    else:
        print("✅ 所有 sys.stdout.reconfigure 调用都正确")
    
    # 询问是否修复
    print("\n" + "=" * 60)
    
    if all_issues:
        response = input("是否要修复发现的问题？(y/n): ")
        
        if response.lower() == 'y':
            print("\n开始修复...")
            print("-" * 40)
            
            fixed_files = []
            total_fixes = 0
            backups = []
            
            # 按文件分组问题
            issues_by_file = {}
            for file_path, issue in all_issues:
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)
            
            # 修复每个文件
            for file_path, issues in issues_by_file.items():
                print(f"修复: {file_path}...")
                fixed, count, backup = fix_file(file_path, issues)
                
                if fixed:
                    print(f"  ✅ 修复 {count} 个问题")
                    fixed_files.append(file_path)
                    total_fixes += count
                    if backup:
                        backups.append(backup)
                else:
                    print(f"  ⏭️ 无需修复")
            
            print("\n" + "=" * 60)
            print("修复完成:")
            print("=" * 60)
            
            if fixed_files:
                print(f"✅ 修复 {len(fixed_files)} 个文件，共 {total_fixes} 个问题")
                print(f"📁 创建了 {len(backups)} 个备份文件 (.libcst.bak)")
                print("\n修复的文件:")
                for file_path in fixed_files:
                    print(f"  • {file_path}")
            else:
                print("✅ 所有文件都已符合规范")
        else:
            print("跳过修复")
    else:
        print("✅ 没有需要修复的问题")
    
    print("\n" + "=" * 60)
    print("libcst 分析工具完成")
    print("=" * 60)
    
    # 演示 libcst 功能
    print("\nlibcst 功能演示:")
    print("-" * 40)
    
    demo_code = '''# 演示代码
import sys

def test():
    with open("test.txt", "w") as f:
        f.write("测试")
    
    with open("data.txt", "r", encoding="gbk") as f:
        data = f.read()
'''
    
    print("原始代码:")
    print(demo_code)
    
    # 分析演示代码
    tree = cst.parse_module(demo_code)
    analyzer = EncodingAnalyzer()
    tree.visit(analyzer)
    
    if analyzer.issues:
        print("\n发现的问题:")
        for issue in analyzer.issues:
            print(f"  行 {issue['position']}: {issue['message']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())