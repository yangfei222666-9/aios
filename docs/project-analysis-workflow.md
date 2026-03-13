# 开源项目拆解工作流

**用途：** 标准化开源项目的工程借鉴流程

**目标：** 从"发现项目"到"落地改进"的完整闭环

---

## 完整流程（4 步）

### 1. 发现项目

**触发条件：**
- GitHub Trending 发现
- 社区推荐
- 技术文章提及
- 用户主动要求拆解

**记录位置：**
- `memory/tech-watch-list.md` 的"待拆解项目"区

**记录内容：**
- 项目名
- GitHub 地址
- 发现来源
- 初步关注点

---

### 2. 按模板拆解

**执行方式：**
- 使用 `docs/project-analysis-template.md` 模板
- 深入阅读仓库结构、关键代码、issues、discussions
- 严格按 9 个部分输出报告

**输出位置：**
- `memory/YYYY-MM-DD-[项目名]-analysis.md`

**核心要求：**
- 必须引用真实代码/结构
- 区分工程事实和营销叙事
- 明确"可直接借/可改造借/暂时别借"

---

### 3. 更新观察清单

**执行方式：**
- 在 `memory/tech-watch-list.md` 追加简版记录
- 包含：一句话判断、最值得借的 3 点、最不能抄的 3 点、下一步动作

**目的：**
- 快速查阅历史拆解结果
- 避免重复拆解
- 积累工程判断经验

---

### 4. 有价值再进任务队列

**判断标准：**
- "可直接借"的点 ≥ 2 个
- 对太极OS当前阶段有明确价值
- 风险可控（不依赖巨量算力、不需要重构核心）

**执行方式：**
- 在 `aios/agent_system/task_queue.jsonl` 创建任务
- 任务类型：`improvement`
- 优先级：根据价值和紧急度判断（P0/P1/P2）

**任务示例：**
```json
{
  "task_id": "task_paperclip_orchestration",
  "type": "improvement",
  "priority": "P1",
  "title": "借鉴 Paperclip 的 orchestration 设计",
  "description": "参考 Paperclip 的任务编排机制，优化太极OS的 Agent 调度",
  "source": "memory/2026-03-13-paperclip-analysis.md",
  "status": "pending",
  "created_at": "2026-03-13T21:50:00+08:00"
}
```

---

## 关键原则

### 1. 不是所有项目都要拆

**跳过条件：**
- 纯概念项目（无代码实现）
- 玩具级 demo（无生产价值）
- 与太极OS方向完全不相关

### 2. 不是所有拆解都要进队列

**进队列条件：**
- 有明确可借鉴的工程实现
- 对太极OS当前阶段有价值
- 风险可控，不需要大规模重构

### 3. 拆解报告是资产

**长期价值：**
- 积累工程判断经验
- 避免被高概念口号误导
- 形成太极OS的技术雷达

---

## 工具支持

### 当前可用
- `web_search` - 搜索项目信息
- `browser` - 深入阅读仓库
- `write` - 输出拆解报告
- `edit` - 更新观察清单

### 未来可能
- 自动化 GitHub Trending 监控
- 自动化拆解报告生成（基于 LLM）
- 自动化任务队列推荐

---

## 示例：Paperclip 拆解流程

### 1. 发现项目
- 来源：用户主动要求
- 记录：`memory/tech-watch-list.md` 待拆解区

### 2. 按模板拆解
- 使用：`docs/project-analysis-template.md`
- 输出：`memory/2026-03-13-paperclip-analysis.md`

### 3. 更新观察清单
- 追加：`memory/tech-watch-list.md` 已拆解区
- 包含：一句话判断 + 3 点值得借 + 3 点不能抄

### 4. 进任务队列（如果有价值）
- 创建：`task_queue.jsonl` 任务
- 类型：`improvement`
- 优先级：根据价值判断

---

**版本：** v1.0  
**创建时间：** 2026-03-13  
**维护者：** 小九 + 珊瑚海
