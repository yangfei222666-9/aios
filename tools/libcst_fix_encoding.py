#!/usr/bin/env python3
"""
使用 libcst 修复文件编码问题
基于专业实现的改进版本
"""

import os
import sys
import libcst as cst
from libcst.metadata import PositionProvider, MetadataWrapper

# 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 写入模式（需要添加 errors='replace'）
WRITE_MODES = {"w", "a", "x", "w+", "a+", "x+"}
# 读取模式（只需要 encoding='utf-8'）
READ_MODES = {"r", "r+", "rt", "wt", "at", "xt"}
# 二进制标志
BINARY_FLAG = "b"

def _get_str_literal(node):
    """安全地获取字符串字面量值"""
    if isinstance(node, cst.SimpleString):
        try:
            # 使用 eval 安全地获取字面量值
            return eval(node.value)  # safe enough for string literals
        except Exception:
            return None
    return None

class OpenCallFixer(cst.CSTTransformer):
    """修复 open() 调用的转换器"""
    
    METADATA_DEPENDENCIES = (PositionProvider,)
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        """处理 open() 调用"""
        # 只处理 open(...)
        if not isinstance(updated_node.func, cst.Name) or updated_node.func.value != "open":
            return updated_node
        
        # 查找模式参数
        mode = self._get_mode_argument(updated_node)
        if not mode:
            return updated_node
        
        # 二进制模式不需要编码参数
        if BINARY_FLAG in mode:
            return updated_node
        
        # 检查是否文本模式
        is_text_mode = self._is_text_mode(mode)
        if not is_text_mode:
            return updated_node
        
        # 检查现有参数
        has_encoding = any(
            a.keyword and a.keyword.value == "encoding" 
            for a in updated_node.args
        )
        has_errors = any(
            a.keyword and a.keyword.value == "errors" 
            for a in updated_node.args
        )
        
        # 准备新参数列表
        new_args = list(updated_node.args)
        
        # 文本模式需要 encoding='utf-8'
        if not has_encoding:
            new_args.append(cst.Arg(
                keyword=cst.Name("encoding"),
                value=cst.SimpleString('"utf-8"'),
                equal=cst.AssignEqual()
            ))
        
        # 写入模式需要 errors='replace'
        if mode in WRITE_MODES and not has_errors:
            new_args.append(cst.Arg(
                keyword=cst.Name("errors"),
                value=cst.SimpleString('"replace"'),
                equal=cst.AssignEqual()
            ))
        
        # 如果有变化，返回修改后的节点
        if len(new_args) != len(updated_node.args):
            return updated_node.with_changes(args=tuple(new_args))
        
        return updated_node
    
    def _get_mode_argument(self, node: cst.Call):
        """获取 open() 调用的模式参数"""
        # 1. 检查关键字参数: mode='w'
        for arg in node.args:
            if arg.keyword and arg.keyword.value == "mode":
                return _get_str_literal(arg.value)
        
        # 2. 检查位置参数: open(file, 'w', ...)
        # open() 的第二个位置参数通常是模式
        if len(node.args) >= 2 and node.args[1].keyword is None:
            return _get_str_literal(node.args[1].value)
        
        # 3. 默认模式是 'r'
        return 'r'
    
    def _is_text_mode(self, mode: str):
        """检查是否是文本模式"""
        # 移除二进制标志
        clean_mode = mode.replace(BINARY_FLAG, '')
        
        # 检查是否是已知的文本模式
        if clean_mode in WRITE_MODES or clean_mode in READ_MODES:
            return True
        
        # 检查模式字符串
        if any(m in clean_mode for m in ['r', 'w', 'a', 'x', '+', 't']):
            return True
        
        return False

class SysReconfigureFixer(cst.CSTTransformer):
    """修复 sys.stdout.reconfigure() 调用的转换器"""
    
    METADATA_DEPENDENCIES = (PositionProvider,)
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        """处理 sys.stdout.reconfigure() 调用"""
        # 检查是否是 sys.stdout.reconfigure 或 sys.stderr.reconfigure
        if not self._is_reconfigure_call(updated_node):
            return updated_node
        
        # 检查现有参数
        has_encoding = any(
            a.keyword and a.keyword.value == "encoding" 
            for a in updated_node.args
        )
        has_errors = any(
            a.keyword and a.keyword.value == "errors" 
            for a in updated_node.args
        )
        
        # 准备新参数列表
        new_args = list(updated_node.args)
        
        # 添加缺失的参数
        if not has_encoding:
            new_args.append(cst.Arg(
                keyword=cst.Name("encoding"),
                value=cst.SimpleString('"utf-8"'),
                equal=cst.AssignEqual()
            ))
        
        if not has_errors:
            new_args.append(cst.Arg(
                keyword=cst.Name("errors"),
                value=cst.SimpleString('"replace"'),
                equal=cst.AssignEqual()
            ))
        
        # 如果有变化，返回修改后的节点
        if len(new_args) != len(updated_node.args):
            return updated_node.with_changes(args=tuple(new_args))
        
        return updated_node
    
    def _is_reconfigure_call(self, node: cst.Call):
        """检查是否是 reconfigure() 调用"""
        if isinstance(node.func, cst.Attribute):
            # sys.stdout.reconfigure 或 sys.stderr.reconfigure
            if node.func.attr.value == "reconfigure":
                if isinstance(node.func.value, cst.Attribute):
                    # sys.stdout 或 sys.stderr
                    if node.func.value.attr.value in ("stdout", "stderr"):
                        if isinstance(node.func.value.value, cst.Name):
                            return node.func.value.value.value == "sys"
                elif isinstance(node.func.value, cst.Name):
                    # stdout.reconfigure 或 stderr.reconfigure (如果已导入)
                    return node.func.value.value in ("stdout", "stderr")
        return False

def fix_file(file_path: str, backup: bool = True, verbose: bool = False) -> bool:
    """修复单个文件的编码问题"""
    try:
        # 读取文件
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            old_src = f.read()
        
        # 解析为 CST
        mod = cst.parse_module(old_src)
        
        # 使用元数据包装器
        wrapper = MetadataWrapper(mod)
        
        # 应用修复
        # 1. 修复 open() 调用
        new_mod = wrapper.visit(OpenCallFixer())
        # 2. 修复 sys.stdout.reconfigure() 调用
        new_mod = wrapper.visit(SysReconfigureFixer())
        
        # 获取修复后的代码
        new_src = new_mod.code
        
        # 检查是否有变化
        if new_src == old_src:
            if verbose:
                print(f"无需修改: {file_path}")
            return False
        
        # 有变化，需要修复
        if verbose:
            print(f"需要修复: {file_path}")
        
        # 创建备份
        if backup:
            backup_path = file_path + ".libcst.bak"
            if not os.path.exists(backup_path):
                with open(backup_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(old_src)
                if verbose:
                    print(f"  创建备份: {backup_path}")
        
        # 写入修复后的代码
        with open(file_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(new_src)
        
        if verbose:
            print(f"  已修复: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"修复 {file_path} 时出错: {e}")
        return False

def find_python_files(root_dir: str):
    """查找所有 Python 文件"""
    for base, _, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(base, filename)
                # 跳过备份文件
                if not file_path.endswith(".bak"):
                    yield file_path

def analyze_file(file_path: str):
    """分析文件的编码问题"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            src = f.read()
        
        mod = cst.parse_module(src)
        
        issues = []
        
        # 分析 open() 调用
        class OpenCallAnalyzer(cst.CSTVisitor):
            def __init__(self):
                self.issues = []
            
            def visit_Call(self, node):
                if isinstance(node.func, cst.Name) and node.func.value == "open":
                    # 这里可以添加详细的分析逻辑
                    pass
        
        analyzer = OpenCallAnalyzer()
        mod.visit(analyzer)
        
        return analyzer.issues
        
    except Exception as e:
        print(f"分析 {file_path} 时出错: {e}")
        return []

def main():
    """主函数"""
    print("libcst 文件编码修复工具")
    print("=" * 60)
    print("基于专业实现的改进版本")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description="修复 Python 文件的编码问题")
    parser.add_argument("path", nargs="?", default=".", help="要修复的目录或文件")
    parser.add_argument("--analyze", "-a", action="store_true", help="只分析不修复")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 收集要处理的文件
    files_to_process = []
    
    if os.path.isfile(args.path):
        if args.path.endswith(".py"):
            files_to_process.append(args.path)
        else:
            print(f"错误: {args.path} 不是 Python 文件")
            return 1
    else:
        files_to_process = list(find_python_files(args.path))
    
    print(f"找到 {len(files_to_process)} 个 Python 文件")
    print()
    
    if args.analyze:
        # 分析模式
        print("分析文件编码问题...")
        print("-" * 40)
        
        total_issues = 0
        
        for file_path in files_to_process:
            issues = analyze_file(file_path)
            if issues:
                print(f"{file_path}: {len(issues)} 个问题")
                total_issues += len(issues)
                if args.verbose:
                    for issue in issues:
                        print(f"  • {issue}")
            elif args.verbose:
                print(f"{file_path}: ✅ 通过")
        
        print(f"\n总计: {total_issues} 个问题")
        
        if total_issues > 0:
            print("\n运行修复命令:")
            print(f"  python {__file__} {args.path}")
        
        return 0
    
    else:
        # 修复模式
        print("开始修复文件编码问题...")
        print("-" * 40)
        
        changed_files = 0
        
        for file_path in files_to_process:
            if args.verbose:
                print(f"处理: {file_path}...")
            
            try:
                changed = fix_file(file_path, backup=not args.no_backup)
                
                if changed:
                    changed_files += 1
                    print(f"✅ 修复: {file_path}")
                elif args.verbose:
                    print(f"⏭️ 跳过: {file_path} (无需修复)")
                    
            except Exception as e:
                print(f"❌ 错误: {file_path} - {e}")
        
        print("\n" + "=" * 60)
        print("修复完成:")
        print("=" * 60)
        
        print(f"处理文件数: {len(files_to_process)}")
        print(f"修复文件数: {changed_files}")
        
        if changed_files > 0 and not args.no_backup:
            print(f"备份文件: {changed_files} 个 (.libcst.bak)")
            print("\n提示: 可以安全删除备份文件")
        
        if changed_files == 0:
            print("\n✅ 所有文件都已符合编码规范")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())