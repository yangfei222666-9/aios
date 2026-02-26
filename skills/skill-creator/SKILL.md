---
name: skill-creator
description: Create or update agent skills. Use when designing, building, or packaging skills that include scripts, references, and resources. Analyzes code, extracts patterns, generates SKILL.md documentation, and packages skills for sharing.
---

# Skill Creator - 工作流转化为可复用 Skill

## 核心功能

把临时脚本、工作流、自动化任务转化成标准化的 OpenClaw Skill。

**自动化流程：**
1. **分析代码** - 提取函数、类、依赖、文档字符串
2. **推断用途** - 自动分类（monitoring/automation/information/etc.）
3. **提取关键词** - 从代码和函数名中提取技术关键词
4. **生成文档** - 自动生成标准 SKILL.md（frontmatter + 使用说明）
5. **打包 Skill** - 复制脚本 + 生成文档 + 创建目录结构

## 使用方式

### 交互式创建（推荐）

```bash
cd C:\Users\A\.openclaw\workspace\skills\skill-creator
python skill_creator.py
```

**交互流程：**
1. 输入脚本路径
2. 自动分析并显示结果
3. 输入 skill 名称和描述
4. 确认并创建

**示例：**
```
🎨 Skill Creator - 交互式创建

📂 脚本路径: C:\Users\A\Desktop\my_script.py

🔍 分析脚本...

📊 分析结果:
   名称: my_script
   用途: automation
   函数: 3 个
   类: 1 个
   依赖: requests
   关键词: api, http, automation, task

📝 输入元数据:
   Skill 名称 [my-script]: my-automation
   描述 [Automate tasks via API]: 

✅ 即将创建 skill: my-automation
   继续? [Y/n]: y

✅ Skill 创建成功: C:\Users\A\.openclaw\workspace\skills\my-automation
📄 SKILL.md: C:\Users\A\.openclaw\workspace\skills\my-automation\SKILL.md
🐍 脚本: C:\Users\A\.openclaw\workspace\skills\my-automation\my_script.py

🎉 完成！

下一步:
   1. 编辑 SKILL.md 完善文档
   2. 测试 skill: cd my-automation && python my_script.py
   3. 重建索引: cd ../find-skills && python find_skill.py rebuild
```

### 命令行模式

```bash
python skill_creator.py <脚本路径> [skill名称] [描述]
```

**示例：**
```bash
# 自动推断名称和描述
python skill_creator.py C:\Users\A\Desktop\monitor.py

# 指定名称
python skill_creator.py C:\Users\A\Desktop\monitor.py server-monitor

# 指定名称和描述
python skill_creator.py C:\Users\A\Desktop\monitor.py server-monitor "Monitor server health"
```

## 生成的 Skill 结构

```
my-automation/
├── SKILL.md              # 标准文档（frontmatter + 使用说明）
├── README.md             # 简短介绍
└── my_script.py          # 原始脚本（复制）
```

## SKILL.md 模板

自动生成的 SKILL.md 包含：

```markdown
---
name: my-automation
description: Automate tasks via API
---

# My Automation

## 功能

Automate tasks via API

## 使用方式

### 命令行
...

### 在 OpenClaw 中使用
...

## 核心功能

### 主要函数
- `fetch_data()` - Fetch Data
- `process_task()` - Process Task

## 依赖
- requests

## 元数据
- **分类:** automation
- **关键词:** api, http, automation, task
- **创建时间:** 2026-02-26

---

**版本:** 1.0  
**创建者:** skill-creator  
**最后更新:** 2026-02-26
```

## 代码分析能力

### 提取内容
- **文档字符串** - Python docstring 或注释块
- **函数** - 所有 `def` 定义的函数
- **类** - 所有 `class` 定义的类
- **依赖** - `import` 和 `from` 语句（过滤标准库）
- **关键词** - 从代码、函数名、类名中提取

### 自动分类
基于关键词自动推断用途：
- **monitoring** - monitor, health, check, status
- **maintenance** - backup, cleanup, organize
- **information** - search, fetch, scrape, crawl
- **automation** - automate, workflow, task
- **testing** - test, ui, screenshot
- **aios** - agent, aios, orchestrat
- **utility** - 其他

## 在 OpenClaw 中使用

当用户说"我想把这个脚本变成 skill"时：

1. **运行 skill-creator：**
   ```bash
   cd C:\Users\A\.openclaw\workspace\skills\skill-creator
   $env:PYTHONIOENCODING='utf-8'
   python skill_creator.py
   ```

2. **按提示输入信息**

3. **完成后重建索引：**
   ```bash
   cd ../find-skills
   python find_skill.py rebuild
   ```

4. **测试新 skill：**
   ```bash
   python find_skill.py search <新skill名称>
   ```

## 最佳实践

### 脚本准备
1. **添加文档字符串** - 清晰描述脚本用途
2. **函数命名规范** - 使用描述性名称（如 `fetch_data` 而非 `f1`）
3. **模块化** - 拆分成多个函数，便于提取
4. **依赖声明** - 在文件顶部集中 import

### 创建后优化
1. **完善 SKILL.md** - 添加示例、常见问题、配置说明
2. **添加测试** - 创建 `test_*.py` 验证功能
3. **添加配置** - 如需配置，创建 `config.json` 或 `.env`
4. **添加依赖文件** - 如需外部依赖，创建 `requirements.txt`

### 分享 Skill
1. **打包** - 压缩整个 skill 目录
2. **发布到 GitHub** - 创建仓库，推送代码
3. **提交到 ClawdHub** - 使用 `clawdhub publish`

## 示例场景

### 场景 1：监控脚本 → Skill

**原始脚本：** `server_health.py`
```python
"""Check server health and send alerts"""
import psutil

def check_cpu():
    return psutil.cpu_percent()

def check_memory():
    return psutil.virtual_memory().percent
```

**运行 skill-creator：**
```bash
python skill_creator.py server_health.py
```

**生成：**
- `skills/server-health/SKILL.md`
- `skills/server-health/server_health.py`
- 自动分类为 `monitoring`
- 关键词：`monitor, health, server`

### 场景 2：自动化任务 → Skill

**原始脚本：** `backup_files.py`
```python
"""Backup important files to cloud storage"""
import shutil
from pathlib import Path

def backup(source, dest):
    shutil.copytree(source, dest)
```

**运行 skill-creator：**
```bash
python skill_creator.py backup_files.py file-backup "Backup files to cloud"
```

**生成：**
- `skills/file-backup/SKILL.md`
- `skills/file-backup/backup_files.py`
- 自动分类为 `maintenance`
- 关键词：`backup, file, automation`

## 技术细节

### 支持的语言
- **当前：** Python（.py）
- **未来：** Shell（.sh）、JavaScript（.js）、PowerShell（.ps1）

### 分析算法
1. **正则提取** - 函数、类、import
2. **关键词匹配** - 技术词汇库（30+ 关键词）
3. **启发式分类** - 基于关键词频率推断用途
4. **模板生成** - Markdown 模板填充

### 限制
- 仅分析语法结构，不执行代码
- 依赖提取仅限 `import` 语句
- 分类基于启发式，可能不准确（可手动修改）

## 常见问题

**Q: 生成的描述不准确怎么办？**  
A: 编辑 `SKILL.md`，手动修改 frontmatter 的 `description` 字段。

**Q: 如何添加更多文档？**  
A: 编辑 `SKILL.md`，在"使用方式"后添加章节（如"配置"、"示例"、"常见问题"）。

**Q: 如何更新已有 skill？**  
A: 重新运行 skill-creator，会覆盖 SKILL.md（建议先备份）。

**Q: 如何分享 skill？**  
A: 压缩 skill 目录，或推送到 GitHub，或使用 `clawdhub publish`。

## 未来改进

- [ ] 支持更多语言（Shell、JavaScript、PowerShell）
- [ ] 自动生成测试用例
- [ ] 集成 ClawdHub 一键发布
- [ ] 从 GitHub 仓库直接创建 skill
- [ ] 自动生成配置文件模板
- [ ] 支持多文件 skill（自动识别入口）

---

**版本：** 1.0  
**最后更新：** 2026-02-26  
**维护者：** 小九 + 珊瑚海
