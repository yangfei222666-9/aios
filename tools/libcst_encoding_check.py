#!/usr/bin/env python3
"""
使用 libcst 检查和修复编码问题
专门针对语音唤醒系统的实际需求
"""

import sys
import os
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

class SystemEncodingChecker:
    """系统编码检查器"""
    
    def __init__(self):
        self.results = {
            "files_checked": 0,
            "files_with_issues": 0,
            "total_issues": 0,
            "issues_by_type": {},
            "fixed_files": 0
        }
    
    def check_file(self, file_path):
        """检查单个文件"""
        self.results["files_checked"] += 1
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析为 CST
            tree = cst.parse_module(content)
            
            # 检查编码问题
            checker = EncodingChecker()
            tree.visit(checker)
            
            if checker.issues:
                self.results["files_with_issues"] += 1
                self.results["total_issues"] += len(checker.issues)
                
                # 统计问题类型
                for issue in checker.issues:
                    issue_type = issue["type"]
                    self.results["issues_by_type"][issue_type] = \
                        self.results["issues_by_type"].get(issue_type, 0) + 1
                
                return checker.issues, checker.open_calls
            else:
                return [], checker.open_calls
                
        except Exception as e:
            print(f"检查 {file_path} 时出错: {e}")
            return [], []
    
    def fix_file(self, file_path, issues):
        """修复单个文件"""
        if not issues:
            return False
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析为 CST
            tree = cst.parse_module(content)
            
            # 应用修复
            fixer = EncodingFixer(issues)
            new_tree = tree.visit(fixer)
            
            if fixer.fixed_count > 0:
                # 备份原文件
                backup_path = file_path.with_suffix(file_path.suffix + ".libcst.bak")
                with open(backup_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(content)
                
                # 写入修复后的内容
                with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(new_tree.code)
                
                self.results["fixed_files"] += 1
                return True, fixer.fixed_count, backup_path
            else:
                return False, 0, None
                
        except Exception as e:
            print(f"修复 {file_path} 时出错: {e}")
            return False, 0, None

class EncodingChecker(cst.CSTVisitor):
    """编码检查访问器"""
    
    def __init__(self):
        self.issues = []
        self.open_calls = []
    
    def visit_Call(self, node):
        """检查函数调用"""
        # 检查 open() 调用
        if self._is_open_call(node):
            self._check_open_call(node)
        
        # 检查 sys.stdout.reconfigure 调用
        elif self._is_reconfigure_call(node):
            self._check_reconfigure_call(node)
    
    def _is_open_call(self, node):
        """检查是否是 open() 调用"""
        if isinstance(node.func, cst.Name):
            return node.func.value == "open"
        return False
    
    def _is_reconfigure_call(self, node):
        """检查是否是 sys.stdout.reconfigure 调用"""
        if isinstance(node.func, cst.Attribute):
            if isinstance(node.func.value, cst.Attribute):
                # sys.stdout.reconfigure
                if (node.func.value.attr.value == "stdout" and 
                    node.func.attr.value == "reconfigure"):
                    if isinstance(node.func.value.value, cst.Name):
                        return node.func.value.value.value == "sys"
            elif isinstance(node.func.value, cst.Name):
                # stdout.reconfigure (如果已经导入)
                if node.func.value.value == "stdout" and node.func.attr.value == "reconfigure":
                    return True
        return False
    
    def _check_open_call(self, node):
        """检查 open() 调用"""
        try:
            # 获取参数
            args = node.args
            mode = None
            encoding = None
            errors = None
            
            # 解析位置参数
            for i, arg in enumerate(args):
                if not arg.keyword:  # 位置参数
                    if i == 1 and isinstance(arg.value, cst.SimpleString):  # 模式参数
                        mode = arg.value.value.strip("'\"")
            
            # 解析关键字参数
            for arg in args:
                if arg.keyword:
                    keyword = arg.keyword.value
                    if keyword == "encoding" and isinstance(arg.value, cst.SimpleString):
                        encoding = arg.value.value.strip("'\"")
                    elif keyword == "errors" and isinstance(arg.value, cst.SimpleString):
                        errors = arg.value.value.strip("'\"")
            
            # 记录调用信息
            self.open_calls.append({
                "mode": mode,
                "encoding": encoding,
                "errors": errors
            })
            
            # 检查问题
            if mode in ("r", "w", "a"):
                # 文本模式必须指定编码
                if not encoding:
                    self.issues.append({
                        "type": "missing_encoding",
                        "node": node,
                        "message": f"open() {mode} 模式缺少 encoding='utf-8'"
                    })
                elif encoding != "utf-8":
                    self.issues.append({
                        "type": "wrong_encoding",
                        "node": node,
                        "message": f"open() 使用编码 '{encoding}' 而不是 'utf-8'"
                    })
                
                # 写入/追加模式需要 errors='replace'
                if mode in ("w", "a") and errors != "replace":
                    self.issues.append({
                        "type": "missing_errors",
                        "node": node,
                        "message": f"open() {mode} 模式缺少 errors='replace'"
                    })
                    
        except Exception as e:
            print(f"分析 open() 调用时出错: {e}")
    
    def _check_reconfigure_call(self, node):
        """检查 sys.stdout.reconfigure 调用"""
        try:
            encoding = None
            errors = None
            
            # 检查参数
            for arg in node.args:
                if arg.keyword:
                    keyword = arg.keyword.value
                    if keyword == "encoding" and isinstance(arg.value, cst.SimpleString):
                        encoding = arg.value.value.strip("'\"")
                    elif keyword == "errors" and isinstance(arg.value, cst.SimpleString):
                        errors = arg.value.value.strip("'\"")
            
            # 检查问题
            if encoding != "utf-8":
                self.issues.append({
                    "type": "wrong_reconfigure_encoding",
                    "node": node,
                    "message": f"sys.stdout.reconfigure() 使用编码 '{encoding}' 而不是 'utf-8'"
                })
            
            if errors != "replace":
                self.issues.append({
                    "type": "missing_reconfigure_errors",
                    "node": node,
                    "message": f"sys.stdout.reconfigure() 缺少 errors='replace'"
                })
                
        except Exception as e:
            print(f"分析 reconfigure() 调用时出错: {e}")

class EncodingFixer(cst.CSTTransformer):
    """编码修复转换器"""
    
    def __init__(self, issues):
        self.issues = issues
        self.fixed_count = 0
    
    def leave_Call(self, original_node, updated_node):
        """修复函数调用"""
        # 检查是否有需要修复的问题
        for issue in self.issues:
            if issue["node"] == original_node:
                if issue["type"] == "missing_encoding":
                    updated_node = self._add_encoding_param(updated_node)
                    self.fixed_count += 1
                elif issue["type"] == "wrong_encoding":
                    updated_node = self._fix_encoding_param(updated_node)
                    self.fixed_count += 1
                elif issue["type"] == "missing_errors":
                    updated_node = self._add_errors_param(updated_node)
                    self.fixed_count += 1
                elif issue["type"] == "wrong_reconfigure_encoding":
                    updated_node = self._fix_reconfigure_encoding(updated_node)
                    self.fixed_count += 1
                elif issue["type"] == "missing_reconfigure_errors":
                    updated_node = self._add_reconfigure_errors(updated_node)
                    self.fixed_count += 1
        
        return updated_node
    
    def _add_encoding_param(self, node):
        """添加 encoding='utf-8' 参数"""
        encoding_arg = cst.Arg(
            keyword=cst.Name("encoding"),
            value=cst.SimpleString("'utf-8'"),
            equal=cst.AssignEqual()
        )
        return node.with_changes(args=node.args + (encoding_arg,))
    
    def _fix_encoding_param(self, node):
        """修复编码参数为 utf-8"""
        new_args = []
        for arg in node.args:
            if arg.keyword and arg.keyword.value == "encoding":
                new_arg = arg.with_changes(value=cst.SimpleString("'utf-8'"))
                new_args.append(new_arg)
            else:
                new_args.append(arg)
        return node.with_changes(args=tuple(new_args))
    
    def _add_errors_param(self, node):
        """添加 errors='replace' 参数"""
        errors_arg = cst.Arg(
            keyword=cst.Name("errors"),
            value=cst.SimpleString("'replace'"),
            equal=cst.AssignEqual()
        )
        return node.with_changes(args=node.args + (errors_arg,))
    
    def _fix_reconfigure_encoding(self, node):
        """修复 sys.stdout.reconfigure 的编码参数"""
        new_args = []
        for arg in node.args:
            if arg.keyword and arg.keyword.value == "encoding":
                new_arg = arg.with_changes(value=cst.SimpleString("'utf-8'"))
                new_args.append(new_arg)
            else:
                new_args.append(arg)
        return node.with_changes(args=tuple(new_args))
    
    def _add_reconfigure_errors(self, node):
        """为 sys.stdout.reconfigure 添加 errors='replace'"""
        errors_arg = cst.Arg(
            keyword=cst.Name("errors"),
            value=cst.SimpleString("'replace'"),
            equal=cst.AssignEqual()
        )
        return node.with_changes(args=node.args + (errors_arg,))

def main():
    """主函数"""
    print("语音唤醒系统 - libcst 编码检查工具")
    print("=" * 60)
    print("使用 libcst 进行专业的代码分析和修复")
    print()
    
    # 创建检查器
    checker = SystemEncodingChecker()
    
    # 检查目录
    directories = ["tools", "."]
    
    all_issues = {}
    all_open_calls = {}
    
    print("开始检查文件...")
    print("-" * 40)
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for py_file in Path(directory).rglob("*.py"):
            # 跳过备份文件
            if py_file.suffix == ".bak":
                continue
                
            issues, open_calls = checker.check_file(py_file)
            
            if issues:
                all_issues[py_file] = issues
                all_open_calls[py_file] = open_calls
                
                print(f"❌ {py_file}: {len(issues)} 个问题")
            else:
                print(f"✅ {py_file}: 通过")
    
    print("\n" + "=" * 60)
    print("检查结果汇总:")
    print("=" * 60)
    
    print(f"检查文件数: {checker.results['files_checked']}")
    print(f"有问题文件: {checker.results['files_with_issues']}")
    print(f"总问题数: {checker.results['total_issues']}")
    
    if checker.results['issues_by_type']:
        print("\n问题类型分布:")
        for issue_type, count in checker.results['issues_by_type'].items():
            print(f"  {issue_type}: {count}")
    
    # 显示详细问题
    if all_issues:
        print("\n详细问题列表:")
        print("-" * 40)
        
        for file_path, issues in all_issues.items():
            print(f"\n{file_path}:")
            for issue in issues:
                print(f"  • {issue['message']}")
    
    # 询问是否修复
    print("\n" + "=" * 60)
    
    if all_issues:
        response = input("是否要自动修复这些问题？(y/n): ")
        
        if response.lower() == 'y':
            print("\n开始自动修复...")
            print("-" * 40)
            
            fixed_files = []
            total_fixes = 0
            backups = []
            
            for file_path, issues in all_issues.items():
                print(f"修复: {file_path}...")
                fixed, count, backup = checker.fix_file(file_path, issues)
                
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
                print(f"✅ 成功修复 {len(fixed_files)} 个文件")
                print(f"✅ 共修复 {total_fixes} 个问题")
                print(f"📁 创建了 {len(backups)} 个备份文件")
                
                print("\n修复的文件:")
                for file_path in fixed_files:
                    print(f"  • {file_path}")
                
                print("\n备份文件 (.libcst.bak):")
                for backup in backups:
                    print(f"  • {backup}")
                
                print("\n提示: 修复完成后可以安全删除备份文件")
            else:
                print("✅ 所有文件都已符合编码规范")
        else:
            print("跳过自动修复")
    else:
        print("✅ 恭喜！所有文件都符合编码规范")
    
    print("\n" + "=" * 60)
    print("libcst 编码检查工具完成")
    print("=" * 60)
    
    print("\nlibcst 的优势:")
    print("  • 🔍 精确的代码分析")
    print("  • 🔧 无损的代码修改")
    print("  • 📊 详细的报告")
    print("  • 🛠️ 自动化的修复")
    
    print("\n在语音唤醒系统中的应用:")
    print("  • 确保所有文件操作使用正确的编码")
    print("  • 自动修复编码问题")
    print("  • 提高代码质量和可维护性")
    print("  • 预防未来的编码问题")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())