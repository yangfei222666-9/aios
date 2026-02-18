#!/usr/bin/env python3
"""
简单的 libcst 修复工具
基于提供的专业实现
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

WRITE_MODES = {"w", "a", "x", "w+", "a+", "x+"}
BINARY_FLAG = "b"

def _get_str_literal(node):
    """安全获取字符串字面量"""
    if isinstance(node, cst.SimpleString):
        try:
            return eval(node.value)  # 对字面量安全
        except Exception:
            return None
    return None

class OpenCallFixer(cst.CSTTransformer):
    """修复 open() 调用"""
    
    METADATA_DEPENDENCIES = (PositionProvider,)
    
    def __init__(self):
        super().__init__()
        self.visited = 0      # 访问的 open() 调用总数
        self.candidates = 0   # 符合条件的候选调用
        self.patched = 0      # 实际修复的调用
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        # 只处理 open(...)
        if not isinstance(updated_node.func, cst.Name) or updated_node.func.value != "open":
            return updated_node
        
        self.visited += 1
        
        # 查找模式参数
        mode = None
        
        # 关键字参数: mode='w'
        for arg in updated_node.args:
            if arg.keyword and arg.keyword.value == "mode":
                mode = _get_str_literal(arg.value)
                break
        
        # 位置参数: open(file, 'w', ...)
        if mode is None and len(updated_node.args) >= 2 and updated_node.args[1].keyword is None:
            mode = _get_str_literal(updated_node.args[1].value)
        
        if not mode:
            return updated_node
        
        # 二进制模式不需要编码
        if BINARY_FLAG in mode:
            return updated_node
        
        # 写入模式需要修复
        if mode not in WRITE_MODES:
            return updated_node
        
        self.candidates += 1
        
        # 检查现有参数
        has_encoding = any(
            a.keyword and a.keyword.value == "encoding" 
            for a in updated_node.args
        )
        has_errors = any(
            a.keyword and a.keyword.value == "errors" 
            for a in updated_node.args
        )
        
        # 如果已经都有正确的参数，不需要修复
        if has_encoding and has_errors:
            return updated_node
        
        new_args = list(updated_node.args)
        patched = False
        
        # 添加缺失的参数
        if not has_encoding:
            new_args.append(cst.Arg(
                keyword=cst.Name("encoding"),
                value=cst.SimpleString('"utf-8"'),
                equal=cst.AssignEqual()
            ))
            patched = True
        
        if not has_errors:
            new_args.append(cst.Arg(
                keyword=cst.Name("errors"),
                value=cst.SimpleString('"replace"'),
                equal=cst.AssignEqual()
            ))
            patched = True
        
        if patched:
            self.patched += 1
            return updated_node.with_changes(args=tuple(new_args))
        
        return updated_node

def fix_one_file(path: str, backup: bool = True, verbose: bool = False, stats: bool = False) -> bool:
    """修复单个文件"""
    try:
        # 读取文件
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            old_src = f.read()
        
        try:
            # 解析为 CST
            mod = cst.parse_module(old_src)
            
            # 使用元数据包装器
            wrapper = MetadataWrapper(mod)
            
            # 创建修复器并应用修复
            fixer = OpenCallFixer()
            new_mod = wrapper.visit(fixer)
            new_src = new_mod.code
            
            # 显示统计信息
            if stats and fixer.visited > 0:
                print(f"  [统计] visited={fixer.visited}, candidates={fixer.candidates}, patched={fixer.patched}")
            
            # 检查是否有变化
            if new_src == old_src:
                if verbose:
                    print(f"无需修改: {path}")
                return False
            
            # 有变化，需要修复
            if verbose:
                print(f"需要修复: {path}")
            
            # 创建备份
            if backup:
                bak = path + ".bak"
                if not os.path.exists(bak):
                    with open(bak, "w", encoding="utf-8", errors="replace") as f:
                        f.write(old_src)
                    if verbose:
                        print(f"  创建备份: {bak}")
            
            # 写入修复后的代码
            with open(path, "w", encoding="utf-8", errors="replace") as f:
                f.write(new_src)
            
            if verbose:
                print(f"  已修复: {path}")
            
            return True
            
        except cst.ParserSyntaxError as e:
            print(f"语法错误: {path} - {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            return False
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return False

def find_py_files(path: str):
    """查找 Python 文件"""
    # 注意：现在路径验证已经在主函数中完成
    # 这里假设路径是有效的 .py 文件或目录
    
    if os.path.isfile(path):
        # 单个文件（已经是 .py 文件）
        yield path
    else:  # 是目录
        # 目录
        for base, _, files in os.walk(path):
            for fn in files:
                if fn.endswith(".py"):
                    yield os.path.join(base, fn)

def main():
    """主函数"""
    print("简单 libcst 修复工具")
    print("=" * 60)
    print("基于专业实现的简化版本")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description="修复 Python 文件的编码问题")
    parser.add_argument("path", nargs="?", default=".", help="要修复的目录或文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--stats", "-s", action="store_true", help="显示修复统计信息")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份文件")
    parser.add_argument("--dry-run", action="store_true", help="只显示需要修复的文件，不实际修改")
    parser.add_argument("--allow-nonpy", action="store_true", help="允许输入非 .py 文件（将跳过）")
    
    args = parser.parse_args()
    
    # 调试：打印参数
    if args.verbose:
        print("ARGS:", args)
        print(f"  path: {repr(args.path)}")
        print(f"  verbose: {args.verbose}")
        print(f"  stats: {args.stats}")
        print(f"  no_backup: {args.no_backup}")
        print(f"  dry_run: {args.dry_run}")
        print()
    
    # 使用 pathlib 进行路径验证
    from pathlib import Path
    
    # 统一的错误处理函数
    def fail(msg: str, code: int = 2):
        print(f"错误: {msg}", file=sys.stderr)
        print("提示: 使用 --help 查看用法", file=sys.stderr)
        raise SystemExit(code)
    
    target = Path(args.path)
    
    # 安全的路径解析函数
    def safe_resolve(p: Path) -> str:
        """安全地解析路径为字符串，优先使用 resolve()，失败时使用 absolute()"""
        try:
            return str(p.resolve())
        except Exception:
            # 如果 resolve() 失败（例如权限问题），使用 absolute() 作为后备
            return str(p.absolute())
    
    # 验证路径是否存在
    if not target.exists():
        fail(f"路径不存在: {safe_resolve(target)}", 2)
    
    # 验证路径类型（必须是文件或目录）
    if not (target.is_file() or target.is_dir()):
        fail(f"路径不是文件也不是目录: {safe_resolve(target)}", 2)
    
    # 如果是文件，检查是否是 .py 文件
    if target.is_file() and target.suffix.lower() != ".py":
        if args.allow_nonpy:
            # 允许非 .py 文件，直接退出（跳过）
            if args.verbose:
                print(f"跳过: 非 .py 文件: {safe_resolve(target)}")
            raise SystemExit(0)
        fail(f"只支持 .py 文件: {safe_resolve(target)}", 2)
    
    changed = 0
    total = 0
    errors = 0
    
    print(f"处理路径: {args.path}")
    if args.dry_run:
        print("模式: 干运行（只检查不修改）")
    if args.no_backup:
        print("模式: 不创建备份")
    print()
    
    for p in find_py_files(args.path):
        total += 1
        
        if args.verbose:
            print(f"处理文件 {total}: {p}")
        
        try:
            if args.dry_run:
                # 干运行模式：只检查是否需要修复
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    old_src = f.read()
                
                try:
                    mod = cst.parse_module(old_src)
                    wrapper = MetadataWrapper(mod)
                    fixer = OpenCallFixer()
                    new_mod = wrapper.visit(fixer)
                    new_src = new_mod.code
                    
                    # 显示统计信息
                    if args.stats and fixer.visited > 0:
                        print(f"  [统计] visited={fixer.visited}, candidates={fixer.candidates}, patched={fixer.patched}")
                    
                    if new_src != old_src:
                        changed += 1
                        print(f"需要修复: {p}")
                    elif args.verbose:
                        print(f"无需修改: {p}")
                        
                except cst.ParserSyntaxError as e:
                    errors += 1
                    print(f"语法错误: {e}", file=sys.stderr)
                except Exception as e:
                    errors += 1
                    print(f"错误: {e}", file=sys.stderr)
                    
            else:
                # 正常模式：实际修复
                if fix_one_file(p, backup=not args.no_backup, verbose=args.verbose, stats=args.stats):
                    changed += 1
                    if not args.verbose:
                        print(f"修复: {p}")
                        
        except Exception as e:
            errors += 1
            print(f"错误: {e}", file=sys.stderr)
    
    print("\n" + "=" * 60)
    print("修复完成:")
    print("=" * 60)
    
    print(f"处理文件数: {total}")
    print(f"修复文件数: {changed}")
    print(f"错误文件数: {errors}")
    
    if args.dry_run:
        print("\n干运行模式：未实际修改文件")
        if changed > 0:
            print(f"发现 {changed} 个文件需要修复")
            print("\n运行以下命令进行修复:")
            print(f"  python {__file__} {args.path}")
    else:
        if changed > 0 and not args.no_backup:
            print(f"备份文件: {changed} 个 (.bak)")
            print("\n提示: 修复完成后可以安全删除备份文件")
    
    if errors == 0:
        if changed == 0:
            print("\n✅ 所有文件都已符合编码规范")
        else:
            print(f"\n✅ 修复完成，修复了 {changed} 个文件")
    else:
        print(f"\n⚠️ 完成，但有 {errors} 个错误")
    
    # 只要有文件被处理（无论成功或失败），就返回 0
    # 只有在完全无法处理任何文件时才返回 1
    if total == 0:
        print("❌ 没有找到任何 Python 文件")
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())