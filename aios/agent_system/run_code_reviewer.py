"""
Code_Reviewer 直接执行脚本 v1.0

最小执行链路：
1. 接收明确输入（target_path + focus）
2. 读取目标文件
3. 执行代码审查（问题 / 建议 / 优先级）
4. 写回结果（memory + execution record）
5. 输出最终 outcome
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
AIOS_ROOT = Path(__file__).parent
WORKSPACE_ROOT = AIOS_ROOT.parent.parent  # .openclaw/workspace

# 数据目录
DATA_DIR = AIOS_ROOT / "data"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
EXECUTION_RECORD = DATA_DIR / "agent_execution_record.jsonl"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def log_execution(record: dict):
    """记录执行到 agent_execution_record.jsonl"""
    with open(EXECUTION_RECORD, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_to_memory(content: str, date_str: str) -> str:
    """写回到 memory/YYYY-MM-DD.md"""
    memory_file = MEMORY_DIR / f"{date_str}.md"
    with open(memory_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n{content}\n")
    return str(memory_file)


# 默认排除的目录（已废弃代码不参与审查）
EXCLUDED_DIRS = {"_deprecated", "__pycache__", ".git", "node_modules"}


def read_target_files(target_path: str, exclude_dirs: set = None) -> dict:
    """
    读取审查目标文件
    
    Args:
        target_path: 相对于 AIOS_ROOT 的路径（文件或目录）
        exclude_dirs: 要排除的目录名集合（默认排除 _deprecated 等）
    
    Returns:
        dict: {filename: content}
    """
    if exclude_dirs is None:
        exclude_dirs = EXCLUDED_DIRS
    
    full_path = AIOS_ROOT / target_path
    if not full_path.exists():
        # 也尝试相对于 workspace
        full_path = WORKSPACE_ROOT / target_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"审查目标不存在: {target_path}")
    
    files = {}
    if full_path.is_file():
        # 单文件：检查是否在排除目录中
        if not any(part in exclude_dirs for part in full_path.parts):
            files[str(full_path.relative_to(AIOS_ROOT))] = full_path.read_text(encoding="utf-8")
    elif full_path.is_dir():
        for py_file in sorted(full_path.rglob("*.py")):
            # 跳过排除目录中的文件
            if any(part in exclude_dirs for part in py_file.relative_to(full_path).parts):
                continue
            try:
                rel = str(py_file.relative_to(AIOS_ROOT))
                files[rel] = py_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, ValueError):
                # 跳过无法解码的文件（二进制/非UTF-8）或路径不在 AIOS_ROOT 下的文件
                continue
    
    return files


def review_code(files: dict, focus: str) -> dict:
    """
    执行代码审查
    
    Args:
        files: {filename: content}
        focus: 审查关注点
    
    Returns:
        dict: {
            "issues": [{"file", "line_hint", "severity", "description"}],
            "suggestions": [{"file", "description", "priority"}],
            "summary": str
        }
    """
    issues = []
    suggestions = []
    
    for filename, content in files.items():
        lines = content.split("\n")
        total_lines = len(lines)
        
        # === 检查项 ===
        
        # 1. 文件大小
        if total_lines > 300:
            issues.append({
                "file": filename,
                "line_hint": f"1-{total_lines}",
                "severity": "P2",
                "description": f"文件过长（{total_lines} 行），建议拆分"
            })
        
        # 2. 缺少 docstring
        has_module_docstring = '"""' in "\n".join(lines[:5]) or "'''" in "\n".join(lines[:5])
        if not has_module_docstring:
            issues.append({
                "file": filename,
                "line_hint": "1",
                "severity": "P2",
                "description": "缺少模块级 docstring"
            })
        
        # 3. 裸 except
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:" or stripped == "except Exception:":
                issues.append({
                    "file": filename,
                    "line_hint": str(i),
                    "severity": "P1",
                    "description": f"裸 except 捕获（第 {i} 行），可能吞掉重要异常"
                })
        
        # 4. 硬编码路径
        for i, line in enumerate(lines, 1):
            if "C:\\Users" in line or "C:/Users" in line:
                issues.append({
                    "file": filename,
                    "line_hint": str(i),
                    "severity": "P1",
                    "description": f"硬编码绝对路径（第 {i} 行），降低可移植性"
                })
        
        # 5. TODO / FIXME / HACK（仅检测注释行）
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 只检测注释行（# 开头）
            if stripped.startswith("#") and not stripped.startswith("#!"):
                for marker in ["TODO", "FIXME", "HACK", "XXX"]:
                    if marker in stripped:
                        issues.append({
                            "file": filename,
                            "line_hint": str(i),
                            "severity": "P2",
                            "description": f"未完成标记 {marker}（第 {i} 行）: {stripped[:80]}"
                        })
                        break  # 每行只报告一次
        
        # 6. 未使用的 import（简单检测）
        import_names = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("import ") and " as " not in stripped:
                mod = stripped.split("import ")[-1].strip()
                if "," not in mod:
                    import_names.append((i, mod.split(".")[-1]))
            elif stripped.startswith("from ") and "import " in stripped:
                parts = stripped.split("import ")[-1].strip()
                for name in parts.split(","):
                    name = name.strip().split(" as ")[-1].strip()
                    if name:
                        import_names.append((i, name))
        
        rest_of_code = "\n".join(lines)
        for line_num, name in import_names:
            # 简单计数：如果名字在代码中只出现 1 次（即 import 行本身），可能未使用
            count = rest_of_code.count(name)
            if count <= 1 and name not in ["sys", "os", "json"]:
                suggestions.append({
                    "file": filename,
                    "description": f"可能未使用的 import: {name}（第 {line_num} 行）",
                    "priority": "P2"
                })
        
        # 7. 函数复杂度（简单：超过 50 行的函数）
        func_start = None
        func_name = None
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("def "):
                if func_start and (i - func_start) > 50:
                    suggestions.append({
                        "file": filename,
                        "description": f"函数 {func_name} 过长（{i - func_start} 行，从第 {func_start} 行开始），建议拆分",
                        "priority": "P2"
                    })
                func_start = i
                func_name = line.strip().split("(")[0].replace("def ", "")
        # 检查最后一个函数
        if func_start and (total_lines - func_start) > 50:
            suggestions.append({
                "file": filename,
                "description": f"函数 {func_name} 过长（{total_lines - func_start} 行），建议拆分",
                "priority": "P2"
            })
        
        # 8. 错误处理建议
        has_try = any("try:" in line for line in lines)
        if not has_try and total_lines > 30:
            suggestions.append({
                "file": filename,
                "description": "缺少错误处理（try/except），建议为关键操作添加异常处理",
                "priority": "P1"
            })
    
    # 生成摘要
    p0_count = len([i for i in issues if i["severity"] == "P0"])
    p1_count = len([i for i in issues if i["severity"] == "P1"])
    p2_count = len([i for i in issues if i["severity"] == "P2"])
    
    summary = f"审查了 {len(files)} 个文件，发现 {len(issues)} 个问题（P0:{p0_count} P1:{p1_count} P2:{p2_count}），{len(suggestions)} 条建议"
    
    return {
        "issues": issues,
        "suggestions": suggestions,
        "summary": summary
    }


def format_report(task_id: str, target_path: str, focus: str, 
                  result: dict, start_time: datetime, duration: float) -> str:
    """格式化审查报告为 markdown"""
    
    report = f"""# Code_Reviewer 审查报告

**Task ID:** {task_id}
**执行时间:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}
**审查对象:** {target_path}
**关注点:** {focus}
**耗时:** {duration:.2f}s

---

## 摘要

{result['summary']}

---

## 发现的问题

"""
    if result["issues"]:
        for issue in result["issues"]:
            report += f"- **[{issue['severity']}]** `{issue['file']}` (行 {issue['line_hint']}): {issue['description']}\n"
    else:
        report += "无问题发现。\n"
    
    report += "\n---\n\n## 改进建议\n\n"
    
    if result["suggestions"]:
        for sug in result["suggestions"]:
            report += f"- **[{sug['priority']}]** `{sug['file']}`: {sug['description']}\n"
    else:
        report += "无额外建议。\n"
    
    report += f"\n---\n\n**报告生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return report


def run_code_reviewer(task_input: dict) -> dict:
    """
    执行 Code_Reviewer
    
    Args:
        task_input: {
            "target_path": str,  # 审查目标（相对路径）
            "focus": str,        # 关注点
            "task_id": str       # 可选
        }
    
    Returns:
        dict: {
            "outcome": "success" | "partial" | "failed",
            "duration_sec": float,
            "output_path": str,
            "issues_count": int,
            "suggestions_count": int,
            "error": str | None
        }
    """
    target_path = task_input["target_path"]
    focus = task_input.get("focus", "general")
    task_id = task_input.get("task_id") or f"code-review-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    start_time = datetime.now()
    
    # 记录开始
    start_record = {
        "task_id": task_id,
        "agent_name": "Code_Reviewer",
        "trigger": "manual",
        "input": task_input,
        "start_time": start_time.isoformat(),
        "status": "started"
    }
    log_execution(start_record)
    
    print(f"=== Code_Reviewer 执行开始 ===")
    print(f"Task ID: {task_id}")
    print(f"Target: {target_path}")
    print(f"Focus: {focus}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 读取目标文件
        print("[1/3] 读取审查目标...")
        files = read_target_files(target_path)
        print(f"  读取了 {len(files)} 个文件")
        for fname in files:
            print(f"    - {fname} ({len(files[fname].splitlines())} 行)")
        print()
        
        # 2. 执行审查
        print("[2/3] 执行代码审查...")
        result = review_code(files, focus)
        print(f"  {result['summary']}")
        print()
        
        # 3. 写回结果
        print("[3/3] 写回结果...")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成报告
        report = format_report(task_id, target_path, focus, result, start_time, duration)
        
        # 写入 memory
        date_str = start_time.strftime('%Y-%m-%d')
        memory_path = write_to_memory(report, date_str)
        print(f"  写回到: {memory_path}")
        
        # 写入 execution record
        end_record = {
            "task_id": task_id,
            "agent_name": "Code_Reviewer",
            "trigger": "manual",
            "input": task_input,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": duration,
            "outcome": "success",
            "output_path": memory_path,
            "issues_count": len(result["issues"]),
            "suggestions_count": len(result["suggestions"]),
            "error": None
        }
        log_execution(end_record)
        
        # 更新 selflearn-state
        from selflearn_state import update_state
        update_state(
            agent_id="Code_Reviewer",
            success=True
        )
        
        print()
        print("=== 执行完成 ===")
        print(f"Outcome: success")
        print(f"Duration: {duration:.2f}s")
        print(f"Issues: {len(result['issues'])}")
        print(f"Suggestions: {len(result['suggestions'])}")
        print(f"Output: {memory_path}")
        
        return {
            "outcome": "success",
            "duration_sec": duration,
            "output_path": memory_path,
            "issues_count": len(result["issues"]),
            "suggestions_count": len(result["suggestions"]),
            "error": None
        }
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_record = {
            "task_id": task_id,
            "agent_name": "Code_Reviewer",
            "trigger": "manual",
            "input": task_input,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": duration,
            "outcome": "failed",
            "output_path": None,
            "error": str(e)
        }
        log_execution(error_record)
        
        # 更新 selflearn-state（失败）
        from selflearn_state import update_state
        update_state(
            agent_id="Code_Reviewer",
            success=False
        )
        
        print()
        print("=== 执行失败 ===")
        print(f"Error: {e}")
        print(f"Duration: {duration:.2f}s")
        
        return {
            "outcome": "failed",
            "duration_sec": duration,
            "output_path": None,
            "issues_count": 0,
            "suggestions_count": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) >= 2:
        target = sys.argv[1]
        focus = sys.argv[2] if len(sys.argv) >= 3 else "general"
    else:
        # 默认审查自身
        target = "run_code_reviewer.py"
        focus = "structure,quality,naming"
    
    task_input = {
        "target_path": target,
        "focus": focus
    }
    
    result = run_code_reviewer(task_input)
    
    print()
    print("=== 最终结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
