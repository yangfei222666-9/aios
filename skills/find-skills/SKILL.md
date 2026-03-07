---
name: find-skills
version: 2.1.0
description: Intelligent skill discovery and recommendation system. Helps users find the right skill for their needs through smart matching, category browsing, and usage-based recommendations. Use when users ask "how do I do X", "find a skill for X", or want to explore available capabilities.
---

# Find Skills v2.1 - 智能 Skill 推荐系统

## 🆕 v2.1 新特性

- ✅ **中文搜索支持** - 自动翻译中文查询为英文关键词
- ✅ **自动编码处理** - UTF-8 编码，支持 emoji 和中文
- ✅ **更智能的匹配** - 降低阈值，提高关键词权重
- ✅ **47+ Skills** - 覆盖更多场景
- 🔜 **模糊搜索** - 支持拼写错误（v2.2）
- 🔜 **依赖检查** - 检查 skill 是否可用（v2.2）
- 🔜 **快速安装** - 集成 ClawdHub（v2.2）

## 核心功能

### 1. 智能搜索
- **关键词匹配** - 自动匹配 skill 名称、描述、关键词
- **中文支持** - 支持中文查询（如"监控服务器"）
- **相似度评分** - 0-100% 匹配度，优先推荐高相关度
- **使用频率加成** - 常用 skill 优先推荐

### 2. 分类浏览
- **8 大分类** - monitoring, automation, information, maintenance, ui-tools, aios, productivity, other
- **47+ skills** - 覆盖系统监控、自动化、信息获取、文件管理等

### 3. 智能对比
- **多结果对比** - 找到多个相似 skill 时自动对比
- **共同点分析** - 提取共同关键词
- **独特特性** - 突出每个 skill 的独特优势

## 使用方式

### 命令行（推荐）

```bash
# 搜索 skill（支持中文）
python find_skill.py search <查询>

# 浏览所有分类
python find_skill.py categories

# 查看某个分类
python find_skill.py category <分类名>

# 重建索引（新增 skill 后）
python find_skill.py rebuild

# 查看统计信息
python find_skill.py stats
```

### 示例

**中文搜索：**
```bash
python find_skill.py search 监控服务器
```

输出：
```
🔍 搜索: 监控服务器

找到 3 个相关 skill:

1. 📦 server-health
   Comprehensive server health monitoring...
   📂 分类: monitoring
   🎯 匹配度: 27%

2. 📦 simple-monitor
   Simple server monitoring tool
   📂 分类: monitoring
   🎯 匹配度: 24%

📊 对比分析:
   共同点: monitor
   独特特性:
      • server-health: telegram, ui
      • simple-monitor: cpu, memory, disk
```

**英文搜索：**
```bash
python find_skill.py search server monitor
```

**浏览分类：**
```bash
python find_skill.py categories
```

**查看监控分类：**
```bash
python find_skill.py category monitoring
```

## 在 OpenClaw 中使用

当用户询问"我想监控服务器"或"有什么自动化工具"时：

1. **运行搜索：**
   ```bash
   cd C:\Users\A\.openclaw\workspace\skills\find-skills
   $env:PYTHONIOENCODING='utf-8'
   python find_skill.py search <用户需求>
   ```

2. **解析结果并推荐：**
   - 单个高匹配 → 直接推荐
   - 多个匹配 → 对比并解释差异
   - 无匹配 → 建议更具体的关键词或浏览分类

3. **记录使用：**
   - 用户选择某个 skill 后，自动增加使用计数
   - 下次搜索时优先推荐常用 skill

## 架构

```
find-skills/
├── SKILL.md              # 本文档
├── find_skill.py         # 主入口（CLI）
├── skill_index.py        # 索引构建器
├── skill_matcher.py      # 智能匹配算法（含中文翻译）
└── skills_index.json     # 索引数据（自动生成）
```

## 索引结构

```json
{
  "skills": [
    {
      "name": "server-health",
      "path": "server-health",
      "description": "Comprehensive server health monitoring...",
      "keywords": ["monitor", "system", "server", "telegram"],
      "category": "monitoring",
      "usage_count": 5
    }
  ],
  "categories": {
    "monitoring": ["server-health", "system_resource_monitor", ...]
  },
  "total": 47,
  "version": "2.1",
  "last_updated": "2026-03-04T15:32:51"
}
```

## 匹配算法

**相似度计算（0-1）：**
- 名称匹配：30%
- 描述匹配：20%
- 关键词匹配：40%（提高权重）
- 使用频率加成：10%

**过滤阈值：** 相似度 > 0.01（降低阈值，提高召回率）

## 中文关键词映射

支持以下中文关键词：

**监控相关：**
- 监控 → monitor, monitoring, watch, check
- 服务器 → server, host, machine
- 系统 → system, os
- 健康 → health, status
- 资源 → resource, usage
- 性能 → performance, perf

**自动化相关：**
- 自动化 → automation, automate, automatic
- 工作流 → workflow, flow
- 任务 → task, job
- 定时 → schedule, cron, timer

**信息相关：**
- 新闻 → news, article
- 搜索 → search, find, query
- 网页 → web, page, site
- 抓取 → scrape, crawl, fetch

**维护相关：**
- 备份 → backup, archive
- 清理 → cleanup, clean, clear
- 整理 → organize, sort
- 文件 → file, document

**UI相关：**
- 界面 → ui, interface, gui
- 测试 → test, testing
- 截图 → screenshot, capture
- 窗口 → window, windows

## 分类规则

自动分类基于关键词：
- **monitoring** - monitor, health, resource, system, server
- **automation** - automation, workflow, orchestration, team
- **information** - news, search, web, fetch
- **maintenance** - backup, cleanup, organize, file
- **ui-tools** - ui, test, screenshot, windows
- **aios** - aios, agent
- **productivity** - todoist, task, todo
- **other** - 其他

## 维护

### 新增 Skill 后
```bash
python find_skill.py rebuild
```

### 定期更新
- 每周重建索引（捕获新 skill）
- 每月清理使用计数（避免过度偏向）

## 未来改进（Phase 2 - v2.2）

1. **模糊搜索** - 支持拼写错误（Levenshtein 距离）
2. **依赖检查** - 检查 skill 是否可用（Python 版本、依赖包）
3. **ClawdHub 集成** - 本地没有 → 搜索 ClawdHub → 一键安装
4. **自然语言查询** - "我想监控服务器" → 自动提取关键词
5. **推荐理由** - 解释为什么推荐这个 skill
6. **A/B 测试** - 跟踪推荐效果，优化算法
7. **用户反馈** - 记录"有用/无用"，改进推荐
8. **使用示例展示** - 显示 skill 的使用示例

## 常见问题

**Q: 为什么中文搜索结果少？**  
A: 中文关键词会自动翻译为英文。如果结果少，试试更具体的关键词，或浏览分类。

**Q: 如何提高匹配准确度？**  
A: 使用更具体的关键词，如"server monitor"而非"monitor"。

**Q: 索引多久更新一次？**  
A: 手动更新。新增 skill 后运行 `python find_skill.py rebuild`。

**Q: 如何添加新的中文关键词？**  
A: 编辑 `skill_matcher.py` 中的 `CN_KEYWORD_MAP` 字典。

## 技术细节

### 编码处理
- 所有文件使用 UTF-8 编码
- 命令行输出使用 `$env:PYTHONIOENCODING='utf-8'`
- 支持 emoji 和中文字符

### 性能优化
- 索引缓存（避免重复读取）
- 相似度计算优化（集合运算）
- Top-K 搜索（避免全量排序）

---

**版本：** v2.1.0  
**最后更新：** 2026-03-04  
**维护者：** 小九 + 珊瑚海

**变更日志：**
- v2.1.0 (2026-03-04) - 中文搜索支持、自动编码处理、47+ skills
- v2.0.0 (2026-02-26) - 初始版本，智能搜索和分类浏览
