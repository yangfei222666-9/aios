---
name: github-repo-analyzer
version: 1.0.0
description: 分析 GitHub 项目架构，产出结构化报告，与太极OS对比差距，输出可执行改进建议。把"看过"变成"可比较、可吸收、可落地"的学习输入。
---

# GitHub Repo Analyzer

## 目标

把 GitHub 项目从"看过"变成"可比较、可吸收、可落地"的学习输入。

直接服务太极OS核心使命：持续学习 GitHub 上的 AIOS / Agent / Skill 项目。

## 输入

| 参数 | 必需 | 说明 |
|------|------|------|
| `--repo` | ✅ | GitHub repo URL 或本地仓库路径 |
| `--focus` | ❌ | 分析重点：architecture / agent / memory / skill / workflow（默认 all） |
| `--baseline` | ❌ | 对比基线目录（默认太极OS当前模块） |
| `--output` | ❌ | 输出目录（默认 `output/`） |
| `--depth` | ❌ | 分析深度：quick / standard / deep（默认 standard） |

## 输出

| 文件 | 说明 |
|------|------|
| `repo_summary.md` | 仓库概览（定位、规模、核心模块） |
| `architecture_map.json` | 架构映射（五层模型） |
| `key_patterns.json` | 值得学习的设计模式 |
| `gap_vs_taijios.md` | 与太极OS的对比差距 |
| `next_actions.md` | 可执行改进建议 |

## 固定输出结构

每次分析必须覆盖以下 7 个维度：

1. **仓库定位** — 这个项目是什么、解决什么问题
2. **五层映射** — 感知 / 决策 / 执行 / 记忆 / 进化
3. **核心执行链** — 任务从输入到完成的主路径
4. **核心记忆链** — 经验从产生到复用的主路径
5. **观测/恢复能力** — 可观测性、容错、恢复机制
6. **对太极OS的启发** — 值得学习的 3 个点
7. **可直接复用的设计** — 能直接搬过来用的模式

## 使用方式

### 命令行

```bash
cd C:\Users\A\.openclaw\workspace\skills\github-repo-analyzer
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 analyzer.py --repo https://github.com/example/project
```

### 分析本地仓库

```bash
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 analyzer.py --repo C:\path\to\local\repo --focus architecture
```

### 指定分析重点

```bash
# 只看 Agent 和 Memory 相关
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 analyzer.py --repo https://github.com/example/project --focus agent,memory
```

### 在 OpenClaw 中使用

当用户说"分析这个 GitHub 项目"或"学习这个仓库"时：

1. 运行 analyzer.py 对目标仓库进行分析
2. 产出结构化报告
3. 将关键发现沉淀到 `memory/` 或 `docs/`

## MVP 最小范围

第一版只支持：
- 单仓库分析
- 目录结构扫描
- 核心模块职责识别（README + 目录 + 关键文件）
- 执行链追踪
- 记忆链追踪
- 恢复链追踪
- 值得学习的 3 个点
- 对太极OS的 3 个缺口
- 3 条可执行改进建议

## 验收标准

1. ✅ 能对 1 个仓库产出结构化报告
2. ✅ 能明确 5 个核心模块职责
3. ✅ 能给出太极OS对比差距
4. ✅ 能产出 3 条可执行改进建议
5. ✅ 结果可沉淀到 docs / memory

## 依赖

- Python 3.12+
- requests（GitHub API 访问）
- pathlib（本地仓库扫描）

## 与其他技能的关系

```
github-repo-analyzer → pattern-detector → lesson-extractor
```

本技能是**输入主链**的起点，产出的 `key_patterns.json` 可供 `pattern-detector` 消费。

---

**版本：** 1.0.0
**创建者：** 小九 + 珊瑚海
**最后更新：** 2026-03-11
