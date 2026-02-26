---
name: find-skills
description: Intelligent skill discovery and recommendation system. Helps users find the right skill for their needs through smart matching, category browsing, and usage-based recommendations. Use when users ask "how do I do X", "find a skill for X", or want to explore available capabilities.
---

# Find Skills v2.0 - 智能 Skill 推荐系统

## 核心功能

### 1. 智能搜索
- **关键词匹配** - 自动匹配 skill 名称、描述、关键词
- **相似度评分** - 0-100% 匹配度，优先推荐高相关度
- **使用频率加成** - 常用 skill 优先推荐

### 2. 分类浏览
- **8 大分类** - monitoring, automation, information, maintenance, ui-tools, aios, productivity, other
- **26+ skills** - 覆盖系统监控、自动化、信息获取、文件管理等

### 3. 智能对比
- **多结果对比** - 找到多个相似 skill 时自动对比
- **共同点分析** - 提取共同关键词
- **独特特性** - 突出每个 skill 的独特优势

## 使用方式

### 命令行（推荐）

```bash
# 搜索 skill
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

**搜索监控相关 skill：**
```bash
python find_skill.py search server monitor
```

输出：
```
🔍 搜索: server monitor

找到 2 个相关 skill:

1. 📦 server-health
   Comprehensive server health monitoring...
   📂 分类: monitoring
   🎯 匹配度: 80%

2. 📦 system_resource_monitor
   A clean, reliable system resource monitor...
   📂 分类: monitoring
   🎯 匹配度: 75%

📊 对比分析:
   共同点: monitor, system, server
   独特特性:
      • server-health: telegram, ui
      • system_resource_monitor: cpu, memory, disk
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
├── skill_matcher.py      # 智能匹配算法
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
  "total": 26,
  "version": "2.0",
  "last_updated": "2026-02-26T15:24:59"
}
```

## 匹配算法

**相似度计算（0-1）：**
- 名称匹配：40%
- 描述匹配：30%
- 关键词匹配：20%
- 使用频率加成：10%

**过滤阈值：** 相似度 > 0.1 才返回

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

## 未来改进（Phase 2）

1. **ClawdHub 集成** - 本地没有 → 搜索 ClawdHub → 一键安装
2. **自然语言查询** - "我想监控服务器" → 自动提取关键词
3. **推荐理由** - 解释为什么推荐这个 skill
4. **A/B 测试** - 跟踪推荐效果，优化算法
5. **用户反馈** - 记录"有用/无用"，改进推荐

## 常见问题

**Q: 为什么搜索中文没结果？**  
A: 当前版本主要匹配英文关键词。建议用英文搜索，或浏览分类。Phase 2 会支持中文。

**Q: 如何提高匹配准确度？**  
A: 使用更具体的关键词，如"server monitor"而非"monitor"。

**Q: 索引多久更新一次？**  
A: 手动更新。新增 skill 后运行 `python find_skill.py rebuild`。

---

**版本：** v2.0  
**最后更新：** 2026-02-26  
**维护者：** 小九 + 珊瑚海
