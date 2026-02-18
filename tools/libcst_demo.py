#!/usr/bin/env python3
"""
libcst 演示工具
展示如何使用 libcst 分析和修改 Python 代码
"""

import sys
import libcst as cst

# 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def demo_simple_analysis():
    """简单的代码分析演示"""
    print("libcst 简单分析演示")
    print("=" * 60)
    
    # 示例代码
    code = '''#!/usr/bin/env python3
import sys

def read_file():
    with open("data.txt", "r") as f:
        return f.read()

def write_file(content):
    with open("output.txt", "w") as f:
        f.write(content)

def append_file(content):
    with open("log.txt", "a") as f:
        f.write(content + "\\n")
'''
    
    print("原始代码:")
    print(code)
    
    # 解析代码
    tree = cst.parse_module(code)
    
    print("\n分析结果:")
    print("-" * 40)
    
    # 查找所有 open() 调用
    class OpenCallFinder(cst.CSTVisitor):
        def __init__(self):
            self.open_calls = []
        
        def visit_Call(self, node):
            if isinstance(node.func, cst.Name) and node.func.value == "open":
                self.open_calls.append(node)
    
    finder = OpenCallFinder()
    tree.visit(finder)
    
    print(f"找到 {len(finder.open_calls)} 个 open() 调用")
    
    for i, node in enumerate(finder.open_calls, 1):
        print(f"\n调用 {i}:")
        
        # 获取参数
        args = node.args
        if args:
            # 第一个参数通常是文件名
            if len(args) > 0:
                first_arg = args[0].value
                if isinstance(first_arg, cst.SimpleString):
                    print(f"  文件: {first_arg.value}")
            
            # 第二个参数通常是模式
            if len(args) > 1:
                second_arg = args[1].value
                if isinstance(second_arg, cst.SimpleString):
                    print(f"  模式: {second_arg.value}")
            
            # 检查关键字参数
            for arg in args:
                if arg.keyword:
                    print(f"  参数: {arg.keyword.value} = {arg.value.value}")

def demo_code_transformation():
    """代码转换演示"""
    print("\n" + "=" * 60)
    print("代码转换演示")
    print("=" * 60)
    
    # 需要修复的代码
    code = '''def process_data():
    # 读取文件
    with open("input.txt", "r") as f:
        data = f.read()
    
    # 处理数据
    result = data.upper()
    
    # 写入文件
    with open("output.txt", "w") as f:
        f.write(result)
    
    return result
'''
    
    print("原始代码:")
    print(code)
    
    # 解析代码
    tree = cst.parse_module(code)
    
    # 创建转换器来修复编码问题
    class EncodingFixer(cst.CSTTransformer):
        def leave_Call(self, original_node, updated_node):
            # 检查是否是 open() 调用
            if isinstance(original_node.func, cst.Name) and original_node.func.value == "open":
                # 获取参数
                args = list(original_node.args)
                
                # 检查模式
                mode = None
                if len(args) > 1 and isinstance(args[1].value, cst.SimpleString):
                    mode = args[1].value.value.strip('"\'')
                
                # 如果是文本模式，添加编码参数
                if mode in ("r", "w", "a"):
                    # 检查是否已有编码参数
                    has_encoding = any(
                        arg.keyword and arg.keyword.value == "encoding" 
                        for arg in args
                    )
                    
                    if not has_encoding:
                        # 添加 encoding='utf-8' 参数
                        encoding_arg = cst.Arg(
                            keyword=cst.Name("encoding"),
                            value=cst.SimpleString("'utf-8'"),
                            equal=cst.AssignEqual()
                        )
                        args.append(encoding_arg)
                    
                    # 如果是写入/追加模式，添加 errors='replace'
                    if mode in ("w", "a"):
                        has_errors = any(
                            arg.keyword and arg.keyword.value == "errors"
                            for arg in args
                        )
                        
                        if not has_errors:
                            errors_arg = cst.Arg(
                                keyword=cst.Name("errors"),
                                value=cst.SimpleString("'replace'"),
                                equal=cst.AssignEqual()
                            )
                            args.append(errors_arg)
                
                return updated_node.with_changes(args=tuple(args))
            
            return updated_node
    
    # 应用转换
    fixer = EncodingFixer()
    transformed_tree = tree.visit(fixer)
    
    print("\n修复后的代码:")
    print(transformed_tree.code)

def demo_ast_comparison():
    """AST 与 CST 比较演示"""
    print("\n" + "=" * 60)
    print("AST 与 CST 比较演示")
    print("=" * 60)
    
    code = 'result = calculate(a + b * c)'
    
    print(f"代码: {code}")
    print()
    
    # 使用标准 ast 模块
    import ast as python_ast
    
    print("标准 AST 分析:")
    python_tree = python_ast.parse(code)
    
    # 简单的 AST 遍历
    class AstVisitor(python_ast.NodeVisitor):
        def visit_BinOp(self, node):
            print(f"  二元操作: {node.op.__class__.__name__}")
            self.generic_visit(node)
        
        def visit_Call(self, node):
            print(f"  函数调用: {node.func.id}")
            self.generic_visit(node)
    
    visitor = AstVisitor()
    visitor.visit(python_tree)
    
    print("\nlibcst CST 分析:")
    cst_tree = cst.parse_module(code)
    
    # CST 访问器
    class CstVisitor(cst.CSTVisitor):
        def visit_BinaryOperation(self, node):
            print(f"  二元操作: {node.operator.__class__.__name__}")
        
        def visit_Call(self, node):
            if isinstance(node.func, cst.Name):
                print(f"  函数调用: {node.func.value}")
    
    cst_visitor = CstVisitor()
    cst_tree.visit(cst_visitor)
    
    print("\nCST 优势:")
    print("  • 保留注释和格式")
    print("  • 可以无损修改代码")
    print("  • 更容易进行代码重构")

def demo_practical_use():
    """实际应用演示"""
    print("\n" + "=" * 60)
    print("实际应用演示：修复编码问题")
    print("=" * 60)
    
    # 实际项目中的代码片段
    project_code = '''#!/usr/bin/env python3
import sys

def load_config():
    """加载配置文件"""
    try:
        with open("config.yaml", "r") as f:
            import yaml
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}

def save_results(data):
    """保存结果到文件"""
    with open("results.txt", "w") as f:
        for item in data:
            f.write(f"{item}\\n")

def log_message(message):
    """记录日志"""
    with open("app.log", "a") as f:
        f.write(f"{message}\\n")
'''
    
    print("项目代码（有编码问题）:")
    print(project_code)
    
    # 分析问题
    tree = cst.parse_module(project_code)
    
    class ProblemAnalyzer(cst.CSTVisitor):
        def __init__(self):
            self.problems = []
        
        def visit_Call(self, node):
            if isinstance(node.func, cst.Name) and node.func.value == "open":
                # 分析参数
                args = node.args
                mode = None
                has_encoding = False
                has_errors = False
                
                # 检查模式
                if len(args) > 1 and isinstance(args[1].value, cst.SimpleString):
                    mode = args[1].value.value.strip('"\'')
                
                # 检查关键字参数
                for arg in args:
                    if arg.keyword:
                        if arg.keyword.value == "encoding":
                            has_encoding = True
                        elif arg.keyword.value == "errors":
                            has_errors = True
                
                # 记录问题
                if mode in ("r", "w", "a"):
                    if not has_encoding:
                        self.problems.append(f"缺少 encoding='utf-8' (模式: {mode})")
                    if mode in ("w", "a") and not has_errors:
                        self.problems.append(f"缺少 errors='replace' (模式: {mode})")
    
    analyzer = ProblemAnalyzer()
    tree.visit(analyzer)
    
    print("\n发现的问题:")
    if analyzer.problems:
        for problem in analyzer.problems:
            print(f"  • {problem}")
    else:
        print("  ✅ 没有发现问题")
    
    # 自动修复
    print("\n自动修复...")
    
    class AutoFixer(cst.CSTTransformer):
        def leave_Call(self, original_node, updated_node):
            if isinstance(original_node.func, cst.Name) and original_node.func.value == "open":
                args = list(original_node.args)
                mode = None
                
                # 获取模式
                if len(args) > 1 and isinstance(args[1].value, cst.SimpleString):
                    mode = args[1].value.value.strip('"\'')
                
                if mode in ("r", "w", "a"):
                    # 检查并添加 encoding
                    has_encoding = any(
                        arg.keyword and arg.keyword.value == "encoding"
                        for arg in args
                    )
                    
                    if not has_encoding:
                        args.append(cst.Arg(
                            keyword=cst.Name("encoding"),
                            value=cst.SimpleString("'utf-8'"),
                            equal=cst.AssignEqual()
                        ))
                    
                    # 检查并添加 errors（写入/追加模式）
                    if mode in ("w", "a"):
                        has_errors = any(
                            arg.keyword and arg.keyword.value == "errors"
                            for arg in args
                        )
                        
                        if not has_errors:
                            args.append(cst.Arg(
                                keyword=cst.Name("errors"),
                                value=cst.SimpleString("'replace'"),
                                equal=cst.AssignEqual()
                            ))
                
                return updated_node.with_changes(args=tuple(args))
            
            return updated_node
    
    fixer = AutoFixer()
    fixed_tree = tree.visit(fixer)
    
    print("\n修复后的代码:")
    print(fixed_tree.code)

def main():
    """主演示函数"""
    print("libcst 代码分析和转换演示")
    print("=" * 60)
    print("libcst 是一个用于分析和修改 Python 代码的库")
    print("它可以无损地解析、分析和转换 Python 代码")
    print()
    
    # 运行演示
    demo_simple_analysis()
    demo_code_transformation()
    demo_ast_comparison()
    demo_practical_use()
    
    print("\n" + "=" * 60)
    print("libcst 主要功能总结:")
    print("=" * 60)
    print("1. 🔍 代码分析")
    print("   • 查找特定的代码模式")
    print("   • 分析代码结构和依赖")
    print("   • 检查编码规范和最佳实践")
    print()
    print("2. 🔧 代码转换")
    print("   • 无损修改代码")
    print("   • 自动修复编码问题")
    print("   • 代码重构和优化")
    print()
    print("3. 📊 代码统计")
    print("   • 统计函数调用次数")
    print("   • 分析代码复杂度")
    print("   • 检查代码质量")
    print()
    print("4. 🛠️ 实际应用")
    print("   • 自动化代码审查")
    print("   • 编码规范检查")
    print("   • 代码迁移和升级")
    print()
    print("在语音唤醒系统中的潜在应用:")
    print("  • 自动检查和修复编码问题")
    print("  • 分析代码质量和复杂度")
    print("  • 自动化重构和优化")
    print("  • 代码规范检查工具")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())