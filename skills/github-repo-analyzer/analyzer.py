#!/usr/bin/env python3
"""
GitHub Repo Analyzer v1.0.0
把 GitHub 项目从"看过"变成"可比较、可吸收、可落地"的学习输入。

输出：
  - repo_summary.md
  - architecture_map.json
  - key_patterns.json
  - gap_vs_taijios.md
  - next_actions.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# 太极OS 基线模块（用于对比）
TAIJIOS_BASELINE = {
    "perception": ["heartbeat", "alerts", "task_queue"],
    "decision": ["task_executor", "router", "scheduler"],
    "execution": ["agent_system", "sessions_spawn", "skill_system"],
    "memory": ["memory_server", "lessons.json", "MEMORY.md", "daily_logs"],
    "evolution": ["self_improving_loop", "learning_agents", "pattern_history"],
}

# 五层模型关键词映射
LAYER_KEYWORDS = {
    "perception": ["input", "sensor", "listen", "watch", "monitor", "trigger", "event", "webhook", "poll", "heartbeat", "alert", "notification"],
    "decision": ["decide", "route", "schedule", "plan", "strategy", "policy", "priority", "dispatch", "orchestrat", "coordinator"],
    "execution": ["execute", "run", "worker", "agent", "task", "action", "command", "process", "handler", "perform"],
    "memory": ["memory", "store", "persist", "cache", "history", "log", "record", "embed", "vector", "retriev", "knowledge", "lesson"],
    "evolution": ["learn", "improve", "evolve", "adapt", "feedback", "optimize", "self-improv", "meta", "reflect", "grow"],
}


def clone_repo(repo_url: str, target_dir: str) -> str:
    """克隆 GitHub 仓库到临时目录"""
    print(f"📥 Cloning {repo_url}...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, target_dir],
            capture_output=True, text=True, check=True, timeout=120
        )
        return target_dir
    except subprocess.CalledProcessError as e:
        print(f"❌ Clone failed: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ git not found. Please install git.")
        sys.exit(1)


def scan_directory_structure(repo_path: str, max_depth: int = 3) -> dict:
    """扫描目录结构"""
    structure = {"dirs": [], "files": [], "total_files": 0, "total_dirs": 0}
    repo = Path(repo_path)

    for item in sorted(repo.rglob("*")):
        rel = item.relative_to(repo)
        depth = len(rel.parts)
        if depth > max_depth:
            continue
        # 跳过隐藏目录和常见噪音
        skip = [".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", "dist", "build", ".egg-info"]
        if any(part in skip for part in rel.parts):
            continue

        if item.is_dir():
            structure["dirs"].append(str(rel))
            structure["total_dirs"] += 1
        else:
            structure["files"].append(str(rel))
            structure["total_files"] += 1

    return structure


def read_readme(repo_path: str) -> str:
    """读取 README"""
    for name in ["README.md", "readme.md", "README.rst", "README.txt", "README"]:
        p = Path(repo_path) / name
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:8000]
            except Exception:
                pass
    return ""


def detect_language_and_framework(repo_path: str) -> dict:
    """检测主要语言和框架"""
    repo = Path(repo_path)
    ext_count = {}
    for f in repo.rglob("*"):
        if f.is_file() and not any(p in str(f) for p in [".git", "__pycache__", "node_modules"]):
            ext = f.suffix.lower()
            if ext:
                ext_count[ext] = ext_count.get(ext, 0) + 1

    # 框架检测
    frameworks = []
    markers = {
        "FastAPI": ["fastapi"],
        "Flask": ["flask"],
        "Django": ["django"],
        "LangChain": ["langchain"],
        "LlamaIndex": ["llama_index", "llamaindex"],
        "CrewAI": ["crewai"],
        "AutoGen": ["autogen"],
        "React": ["react"],
        "Next.js": ["next"],
        "Express": ["express"],
    }

    # 扫描 requirements.txt / pyproject.toml / package.json
    for dep_file in ["requirements.txt", "pyproject.toml", "package.json", "setup.py", "setup.cfg"]:
        p = repo / dep_file
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8", errors="replace").lower()
                for fw, keywords in markers.items():
                    if any(kw in content for kw in keywords):
                        frameworks.append(fw)
            except Exception:
                pass

    top_langs = sorted(ext_count.items(), key=lambda x: -x[1])[:5]
    return {
        "languages": {ext: count for ext, count in top_langs},
        "frameworks": list(set(frameworks)),
        "primary_language": top_langs[0][0] if top_langs else "unknown",
    }


def map_to_five_layers(repo_path: str, structure: dict) -> dict:
    """将仓库模块映射到五层模型"""
    layers = {layer: [] for layer in LAYER_KEYWORDS}
    repo = Path(repo_path)

    # 扫描目录名和文件名
    all_paths = structure["dirs"] + structure["files"]
    for path_str in all_paths:
        path_lower = path_str.lower()
        for layer, keywords in LAYER_KEYWORDS.items():
            if any(kw in path_lower for kw in keywords):
                layers[layer].append(path_str)
                break

    # 扫描 Python 文件的 docstring 和类名
    for py_file in repo.rglob("*.py"):
        if any(p in str(py_file) for p in [".git", "__pycache__", "node_modules", "venv"]):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")[:3000]
            rel = str(py_file.relative_to(repo))
            for layer, keywords in LAYER_KEYWORDS.items():
                if any(kw in content.lower() for kw in keywords):
                    if rel not in layers[layer]:
                        layers[layer].append(rel)
                    break
        except Exception:
            pass

    # 去重并限制每层最多 10 个
    return {layer: sorted(set(items))[:10] for layer, items in layers.items()}


def identify_core_modules(repo_path: str, structure: dict) -> list:
    """识别核心模块（基于目录大小和关键文件）"""
    repo = Path(repo_path)
    modules = []

    # 顶层目录作为候选模块
    for d in structure["dirs"]:
        if "/" not in d and "\\" not in d:  # 只看顶层
            dir_path = repo / d
            if dir_path.is_dir():
                file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
                # 尝试读取 __init__.py 或 README
                desc = ""
                for doc_file in ["__init__.py", "README.md", "readme.md"]:
                    doc_path = dir_path / doc_file
                    if doc_path.exists():
                        try:
                            content = doc_path.read_text(encoding="utf-8", errors="replace")[:500]
                            # 提取 docstring
                            match = re.search(r'"""(.+?)"""', content, re.DOTALL)
                            if match:
                                desc = match.group(1).strip()[:200]
                            elif doc_file.lower().startswith("readme"):
                                lines = content.strip().split("\n")
                                desc = lines[0].strip("# ").strip()[:200] if lines else ""
                        except Exception:
                            pass
                        break

                modules.append({
                    "name": d,
                    "file_count": file_count,
                    "description": desc or f"Module: {d}",
                })

    # 按文件数排序，取 Top 10
    modules.sort(key=lambda x: -x["file_count"])
    return modules[:10]


def analyze_execution_chain(repo_path: str) -> dict:
    """分析执行链（入口 → 处理 → 输出）"""
    repo = Path(repo_path)
    chain = {"entry_points": [], "processors": [], "outputs": []}

    # 查找入口文件
    entry_patterns = ["main.py", "app.py", "server.py", "cli.py", "run.py", "__main__.py", "index.py"]
    for pattern in entry_patterns:
        for f in repo.rglob(pattern):
            if not any(p in str(f) for p in [".git", "__pycache__", "node_modules", "venv", "test"]):
                chain["entry_points"].append(str(f.relative_to(repo)))

    # 查找处理器
    processor_patterns = ["*handler*", "*processor*", "*worker*", "*executor*", "*agent*", "*task*"]
    for pattern in processor_patterns:
        for f in repo.rglob(f"{pattern}.py"):
            if not any(p in str(f) for p in [".git", "__pycache__", "node_modules", "venv", "test"]):
                chain["processors"].append(str(f.relative_to(repo)))

    # 查找输出
    output_patterns = ["*output*", "*result*", "*report*", "*export*", "*writer*"]
    for pattern in output_patterns:
        for f in repo.rglob(f"{pattern}.py"):
            if not any(p in str(f) for p in [".git", "__pycache__", "node_modules", "venv", "test"]):
                chain["outputs"].append(str(f.relative_to(repo)))

    return chain


def analyze_memory_chain(repo_path: str) -> dict:
    """分析记忆链（存储 → 检索 → 复用）"""
    repo = Path(repo_path)
    chain = {"storage": [], "retrieval": [], "reuse": []}

    storage_patterns = ["*store*", "*persist*", "*save*", "*db*", "*database*", "*cache*", "*memory*"]
    retrieval_patterns = ["*retriev*", "*search*", "*query*", "*fetch*", "*load*", "*embed*", "*vector*"]
    reuse_patterns = ["*learn*", "*lesson*", "*feedback*", "*improve*", "*adapt*", "*knowledge*"]

    for patterns, key in [(storage_patterns, "storage"), (retrieval_patterns, "retrieval"), (reuse_patterns, "reuse")]:
        for pattern in patterns:
            for f in repo.rglob(f"{pattern}.py"):
                if not any(p in str(f) for p in [".git", "__pycache__", "node_modules", "venv", "test"]):
                    rel = str(f.relative_to(repo))
                    if rel not in chain[key]:
                        chain[key].append(rel)

    return chain


def analyze_observability(repo_path: str) -> dict:
    """分析观测和恢复能力"""
    repo = Path(repo_path)
    capabilities = {
        "logging": False,
        "metrics": False,
        "tracing": False,
        "health_check": False,
        "backup": False,
        "recovery": False,
        "alerting": False,
        "details": [],
    }

    keywords_map = {
        "logging": ["logging", "logger", "log_"],
        "metrics": ["metrics", "prometheus", "statsd", "counter", "gauge", "histogram"],
        "tracing": ["tracing", "trace", "span", "opentelemetry", "jaeger"],
        "health_check": ["health", "healthcheck", "health_check", "readiness", "liveness"],
        "backup": ["backup", "snapshot", "dump", "export"],
        "recovery": ["recover", "restore", "rollback", "failover", "retry"],
        "alerting": ["alert", "notify", "notification", "webhook", "slack"],
    }

    for py_file in repo.rglob("*.py"):
        if any(p in str(py_file) for p in [".git", "__pycache__", "node_modules", "venv"]):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")[:5000].lower()
            rel = str(py_file.relative_to(repo))
            for cap, keywords in keywords_map.items():
                if any(kw in content for kw in keywords):
                    if not capabilities[cap]:
                        capabilities[cap] = True
                        capabilities["details"].append(f"{cap}: found in {rel}")
        except Exception:
            pass

    return capabilities


def compare_with_taijios(layers: dict, observability: dict) -> dict:
    """与太极OS基线对比"""
    gaps = []
    strengths = []

    for layer, baseline_modules in TAIJIOS_BASELINE.items():
        repo_modules = layers.get(layer, [])
        if len(repo_modules) > len(baseline_modules):
            strengths.append({
                "layer": layer,
                "detail": f"目标仓库在 {layer} 层有 {len(repo_modules)} 个模块，太极OS有 {len(baseline_modules)} 个",
                "repo_modules": repo_modules[:5],
            })
        elif len(repo_modules) < len(baseline_modules):
            gaps.append({
                "layer": layer,
                "detail": f"太极OS在 {layer} 层有 {len(baseline_modules)} 个模块，目标仓库只有 {len(repo_modules)} 个",
                "taijios_advantage": baseline_modules,
            })

    # 观测能力对比
    obs_gaps = []
    for cap, has_it in observability.items():
        if cap == "details":
            continue
        if has_it and cap in ["tracing", "metrics"]:
            gaps.append({
                "layer": "observability",
                "detail": f"目标仓库有 {cap}，太极OS当前缺少",
                "recommendation": f"考虑引入 {cap} 能力",
            })

    return {"gaps": gaps[:5], "strengths": strengths[:5]}


def generate_reports(
    repo_url: str,
    repo_path: str,
    structure: dict,
    lang_info: dict,
    layers: dict,
    modules: list,
    exec_chain: dict,
    mem_chain: dict,
    observability: dict,
    comparison: dict,
    readme: str,
    output_dir: str,
):
    """生成所有输出文件"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    repo_name = repo_url.rstrip("/").split("/")[-1] if "://" in repo_url else Path(repo_url).name

    # 1. repo_summary.md
    summary = f"""# {repo_name} - 仓库分析报告

**分析时间：** {now}
**仓库地址：** {repo_url}
**主要语言：** {lang_info['primary_language']}
**框架：** {', '.join(lang_info['frameworks']) or '未检测到'}
**文件数：** {structure['total_files']} | **目录数：** {structure['total_dirs']}

## 仓库定位

{readme[:500] if readme else '（未找到 README）'}

## 核心模块（Top {len(modules)}）

| 模块 | 文件数 | 说明 |
|------|--------|------|
"""
    for m in modules:
        summary += f"| {m['name']} | {m['file_count']} | {m['description'][:60]} |\n"

    summary += f"""
## 五层映射

### 感知层（Perception）
{chr(10).join('- ' + p for p in layers.get('perception', [])[:5]) or '- 未检测到'}

### 决策层（Decision）
{chr(10).join('- ' + p for p in layers.get('decision', [])[:5]) or '- 未检测到'}

### 执行层（Execution）
{chr(10).join('- ' + p for p in layers.get('execution', [])[:5]) or '- 未检测到'}

### 记忆层（Memory）
{chr(10).join('- ' + p for p in layers.get('memory', [])[:5]) or '- 未检测到'}

### 进化层（Evolution）
{chr(10).join('- ' + p for p in layers.get('evolution', [])[:5]) or '- 未检测到'}

## 核心执行链

**入口：** {', '.join(exec_chain['entry_points'][:3]) or '未检测到'}
**处理器：** {', '.join(exec_chain['processors'][:5]) or '未检测到'}
**输出：** {', '.join(exec_chain['outputs'][:3]) or '未检测到'}

## 核心记忆链

**存储：** {', '.join(mem_chain['storage'][:3]) or '未检测到'}
**检索：** {', '.join(mem_chain['retrieval'][:3]) or '未检测到'}
**复用：** {', '.join(mem_chain['reuse'][:3]) or '未检测到'}

## 观测/恢复能力

| 能力 | 状态 |
|------|------|
| 日志 | {'✅' if observability['logging'] else '❌'} |
| 指标 | {'✅' if observability['metrics'] else '❌'} |
| 追踪 | {'✅' if observability['tracing'] else '❌'} |
| 健康检查 | {'✅' if observability['health_check'] else '❌'} |
| 备份 | {'✅' if observability['backup'] else '❌'} |
| 恢复 | {'✅' if observability['recovery'] else '❌'} |
| 告警 | {'✅' if observability['alerting'] else '❌'} |

---
*Generated by github-repo-analyzer v1.0.0*
"""
    (out / "repo_summary.md").write_text(summary, encoding="utf-8")

    # 2. architecture_map.json
    arch_map = {
        "repo": repo_url,
        "analyzed_at": now,
        "language": lang_info,
        "five_layers": layers,
        "core_modules": modules,
        "execution_chain": exec_chain,
        "memory_chain": mem_chain,
        "observability": observability,
    }
    (out / "architecture_map.json").write_text(
        json.dumps(arch_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3. key_patterns.json
    patterns = []
    for layer, items in layers.items():
        if items:
            patterns.append({
                "layer": layer,
                "pattern": f"{layer} 层有 {len(items)} 个相关模块",
                "modules": items[:5],
                "worth_learning": len(items) > 2,
            })
    (out / "key_patterns.json").write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. gap_vs_taijios.md
    gap_md = f"""# {repo_name} vs 太极OS - 差距分析

**分析时间：** {now}

## 太极OS 的优势

"""
    for s in comparison.get("strengths", []):
        gap_md += f"### {s['layer']} 层\n{s['detail']}\n\n"

    gap_md += "\n## 太极OS 的缺口\n\n"
    for g in comparison.get("gaps", []):
        gap_md += f"### {g['layer']} 层\n{g['detail']}\n"
        if "recommendation" in g:
            gap_md += f"**建议：** {g['recommendation']}\n"
        gap_md += "\n"

    (out / "gap_vs_taijios.md").write_text(gap_md, encoding="utf-8")

    # 5. next_actions.md
    actions = f"""# {repo_name} - 可执行改进建议

**分析时间：** {now}

## 建议 1：补强最弱层

"""
    # 找最弱层
    weakest = min(layers.items(), key=lambda x: len(x[1]))
    actions += f"太极OS 在 **{weakest[0]}** 层最薄弱（仅 {len(weakest[1])} 个模块）。\n"
    actions += f"建议参考目标仓库的 {weakest[0]} 层设计进行补强。\n\n"

    actions += "## 建议 2：引入缺失的观测能力\n\n"
    missing_obs = [k for k, v in observability.items() if v and k != "details" and k in ["metrics", "tracing"]]
    if missing_obs:
        actions += f"目标仓库具备 {', '.join(missing_obs)}，太极OS 可考虑引入。\n\n"
    else:
        actions += "目标仓库的观测能力与太极OS相当，暂无明显缺口。\n\n"

    actions += "## 建议 3：复用设计模式\n\n"
    for p in patterns[:3]:
        if p["worth_learning"]:
            actions += f"- **{p['layer']}** 层的模块组织方式值得参考\n"

    actions += f"\n---\n*Generated by github-repo-analyzer v1.0.0*\n"
    (out / "next_actions.md").write_text(actions, encoding="utf-8")

    return out


def main():
    parser = argparse.ArgumentParser(description="GitHub Repo Analyzer v1.0.0")
    parser.add_argument("--repo", required=True, help="GitHub repo URL or local path")
    parser.add_argument("--focus", default="all", help="Focus: architecture/agent/memory/skill/workflow/all")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--depth", default="standard", choices=["quick", "standard", "deep"], help="Analysis depth")
    args = parser.parse_args()

    repo_path = args.repo
    is_remote = repo_path.startswith("http://") or repo_path.startswith("https://") or repo_path.startswith("git@")

    # 如果是远程仓库，先克隆
    tmp_dir = None
    if is_remote:
        tmp_dir = tempfile.mkdtemp(prefix="repo-analyzer-")
        repo_path = clone_repo(args.repo, os.path.join(tmp_dir, "repo"))

    if not Path(repo_path).exists():
        print(f"❌ Path not found: {repo_path}")
        sys.exit(1)

    print(f"🔍 Analyzing {args.repo}...")

    # 执行分析
    structure = scan_directory_structure(repo_path)
    print(f"  📁 {structure['total_files']} files, {structure['total_dirs']} dirs")

    readme = read_readme(repo_path)
    lang_info = detect_language_and_framework(repo_path)
    print(f"  🔤 Primary: {lang_info['primary_language']}, Frameworks: {lang_info['frameworks']}")

    layers = map_to_five_layers(repo_path, structure)
    modules = identify_core_modules(repo_path, structure)
    print(f"  🧩 {len(modules)} core modules identified")

    exec_chain = analyze_execution_chain(repo_path)
    mem_chain = analyze_memory_chain(repo_path)
    observability = analyze_observability(repo_path)

    comparison = compare_with_taijios(layers, observability)
    print(f"  📊 {len(comparison['gaps'])} gaps, {len(comparison['strengths'])} strengths vs TaijiOS")

    # 生成报告
    out = generate_reports(
        args.repo, repo_path, structure, lang_info, layers, modules,
        exec_chain, mem_chain, observability, comparison, readme, args.output
    )

    print(f"\n✅ Analysis complete! Reports saved to: {out}")
    print(f"  📄 repo_summary.md")
    print(f"  📄 architecture_map.json")
    print(f"  📄 key_patterns.json")
    print(f"  📄 gap_vs_taijios.md")
    print(f"  📄 next_actions.md")

    # 清理临时目录
    if tmp_dir:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
