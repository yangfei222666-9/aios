# 2026-03-10 Memory 系统方向 GitHub 学习

**研究对象：**
- Letta (MemGPT) - https://github.com/letta-ai/letta
- LangChain Deep Agents - https://github.com/langchain-ai/deepagents

---

## 问题 1：Memory Server 为什么要常驻？

### Letta 的做法

Letta 没有单独的 "Memory Server"，而是把记忆管理集成到 Agent 本身。但它的核心设计理念回答了"为什么要常驻"：

**关键发现：**
1. **Embedding 模型热加载** - Letta 的记忆检索依赖 embedding 模型，如果每次查询都冷启动，延迟不可接受
2. **Git-backed MemFS** - 记忆存储在 git 仓库中（`~/.letta/agents/<agent-id>/memory`），Agent 通过 bash 工具直接读写，不需要每次重新加载整个记忆树
3. **分层加载** - `system/` 目录下的记忆文件常驻在 context window，其他记忆文件只显示文件树结构，内容按需加载
4. **检索缓存** - 虽然文档没有明确提到，但从架构推断，频繁访问的记忆块应该有缓存机制

**对太极OS 的启发：**

Memory Server 常驻的核心价值不是"一直运行"，而是：
- **消除冷启动延迟** - embedding 模型加载一次，后续查询秒级响应
- **维持检索索引** - 向量索引常驻内存，不用每次重建
- **支持增量更新** - 新记忆写入时，只更新索引的增量部分，不用全量重建

### LangChain Deep Agents 的做法

Deep Agents 没有独立的 Memory Server，而是通过 **filesystem backend** 管理上下文：
- 使用 `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep` 等工具
- 大输出自动保存到文件，避免塞满 context window
- 自动压缩（auto-summarization）长对话

**核心理念：** 把记忆当成文件系统，Agent 通过工具访问，而不是把所有记忆塞进 prompt。

---

## 问题 2：长短期记忆怎么分层？

### Letta 的三层记忆架构

Letta 的 MemFS 是最清晰的分层设计：

```
memory/
├── system/                    # 常驻 context window（短期 + 核心长期）
│   ├── persona.md             # Agent 人格
│   ├── humans/                # 用户信息
│   │   ├── charles.md
│   │   └── charles_prefs.md
│   └── dev_workflow/          # 工作流规则
│       ├── git.md
│       └── planning.md
├── projects/                  # 按需加载（长期记忆）
│   ├── web-app/
│   │   ├── frontend.md
│   │   └── backend_bugs.md
│   └── ...
└── reflections/               # 延迟加载（归档记忆）
    └── 2024-01-15.md
```

**分层规则：**
1. **system/** - 常驻 context，包含：
   - Agent 身份和人格
   - 用户偏好和风格
   - 核心工作流规则
   - 限制：每个文件有 `limit` 字段（如 50000 字符）

2. **非 system/** - 文件树可见，内容按需加载：
   - 项目相关记忆
   - 历史反思
   - 一次性观察

3. **Git 版本控制** - 所有记忆变更都通过 git commit/push 持久化，支持：
   - 回滚错误的记忆编辑
   - 查看记忆变更历史
   - 并行 subagent 通过 git worktree 修改记忆

### LangChain Deep Agents 的做法

Deep Agents 没有显式的"长短期记忆"概念，而是通过 **context management** 实现：
- **Auto-summarization** - 对话过长时自动压缩
- **Large outputs saved to files** - 大输出不塞进 context，而是写入文件
- **Planning tool (write_todos)** - 任务分解和进度追踪，相当于"工作记忆"

**核心理念：** 不区分"长期/短期"，而是区分"当前需要的"和"可以延迟加载的"。

### 对太极OS 的启发

太极OS 当前的记忆分层可以参考 Letta 的设计：

**建议分层：**
```
memory/
├── core/                      # 常驻（类似 Letta 的 system/）
│   ├── IDENTITY.md            # Agent 身份
│   ├── USER.md                # 用户信息
│   ├── SOUL.md                # 人格和价值观
│   └── rules_derived.json     # 核心规则
├── daily/                     # 短期（最近 7 天）
│   ├── 2026-03-10.md
│   └── 2026-03-09.md
├── projects/                  # 长期（按需加载）
│   ├── aios/
│   └── skills/
└── archive/                   # 归档（延迟加载）
    └── 2026-02/
```

**压缩规则：**
- daily/ 超过 7 天 → 提炼关键信息到 MEMORY.md，原文移到 archive/
- projects/ 超过 30 天未访问 → 压缩为摘要
- archive/ 只保留索引，内容按需检索

---

## 问题 3：检索质量怎么提高？

### Letta 的检索策略

Letta 的记忆检索依赖两个机制：

1. **工具驱动的检索** - Agent 通过工具主动检索：
   - `search_memory(query)` - 语义检索
   - `read_file(path)` - 精确读取
   - `grep(pattern)` - 关键词搜索

2. **分层可见性** - 不是"检索所有记忆"，而是：
   - system/ 常驻可见
   - 非 system/ 只显示文件树（文件名 + description）
   - Agent 根据文件名和 description 判断是否需要读取完整内容

**关键设计：** 把"检索"变成"导航" - Agent 先看文件树，再决定读哪些文件，而不是一次性检索所有内容。

### LangChain Deep Agents 的检索策略

Deep Agents 没有显式的"记忆检索"，而是通过 **filesystem tools** 实现：
- `ls` - 列出文件
- `glob` - 模式匹配
- `grep` - 关键词搜索
- `read_file` - 读取文件

**核心理念：** 把检索问题转化为文件系统操作，Agent 自己决定怎么找。

### 对太极OS 的启发

太极OS 当前的记忆检索可以改进：

**当前问题：**
- 冷启动延迟 9s（embedding 模型加载）
- 没有元数据过滤
- 没有相关性排序
- 低价值上下文无法排除

**改进建议：**

#### 1. 元数据过滤（Pre-filter）

在语义检索之前，先用元数据过滤：
```python
def search_memory(query: str, filters: dict = None):
    # 先用元数据过滤
    if filters:
        candidates = filter_by_metadata(
            date_range=filters.get('date_range'),
            tags=filters.get('tags'),
            file_type=filters.get('file_type')
        )
    else:
        candidates = all_memories
    
    # 再做语义检索
    results = semantic_search(query, candidates)
    return results
```

#### 2. 混合检索（Hybrid Search）

结合语义检索和关键词检索：
```python
def hybrid_search(query: str, k: int = 5):
    # 语义检索
    semantic_results = vector_search(query, k=k*2)
    
    # 关键词检索
    keyword_results = keyword_search(query, k=k*2)
    
    # 融合排序（RRF - Reciprocal Rank Fusion）
    final_results = rrf_merge(semantic_results, keyword_results, k=k)
    return final_results
```

#### 3. 相关性重排序（Re-ranking）

检索后用更强的模型重排序：
```python
def search_with_rerank(query: str, k: int = 5):
    # 第一阶段：快速检索（top 20）
    candidates = vector_search(query, k=20)
    
    # 第二阶段：重排序（top 5）
    reranked = rerank_model.rank(query, candidates)
    return reranked[:k]
```

#### 4. 低价值上下文过滤

根据历史使用频率和时效性过滤：
```python
def filter_low_value(results: list):
    filtered = []
    for result in results:
        # 过滤条件
        if result.access_count < 2 and result.age_days > 30:
            continue  # 低频 + 陈旧 = 低价值
        if result.relevance_score < 0.5:
            continue  # 相关性太低
        filtered.append(result)
    return filtered
```

---

## 今日输出

### 1. 架构启发

**Letta 的 MemFS 设计最值得借鉴：**

把记忆当成 **git-backed filesystem**，而不是数据库：
- Agent 通过 bash 工具（read/write/edit）操作记忆
- 分层可见性（system/ 常驻，其他按需加载）
- Git 版本控制（支持回滚、历史查看、并行编辑）
- 文件树导航（先看结构，再读内容）

这种设计的核心优势：
- **Agent 友好** - Agent 已经会用 bash 工具，不需要学新的记忆 API
- **可观测** - 记忆变更都有 git commit，可以看到 Agent 改了什么
- **可回滚** - 记忆编辑错误可以 git revert
- **可并行** - 多个 subagent 通过 git worktree 同时编辑记忆

### 2. 与太极OS 的差距判断

**太极OS 当前的记忆系统 vs Letta/Deep Agents：**

| 维度 | 太极OS | Letta | Deep Agents |
|------|--------|-------|-------------|
| 记忆存储 | JSONL + Markdown | Git-backed MemFS | Filesystem |
| 分层加载 | ❌ 全量加载 | ✅ system/ 常驻，其他按需 | ✅ 自动压缩 |
| 版本控制 | ❌ 无 | ✅ Git | ❌ 无 |
| 检索方式 | 语义检索 | 文件树导航 + 工具检索 | Filesystem 工具 |
| 冷启动 | 9s | 未知（推测 <1s） | 未知 |
| 元数据过滤 | ❌ 无 | ✅ 文件 frontmatter | ❌ 无 |
| 并行编辑 | ❌ 不支持 | ✅ Git worktree | ❌ 不支持 |

**核心差距：**
1. **没有分层加载** - 太极OS 每次都加载所有记忆，Letta 只加载 system/ + 按需加载
2. **没有版本控制** - 记忆编辑无法回滚，无法查看历史
3. **没有元数据过滤** - 检索前无法用日期/标签/类型过滤
4. **没有文件树导航** - Agent 无法先看结构再决定读什么

### 3. 可执行改进建议

#### 建议 1：引入分层加载（高优先级）

**目标：** 减少每次加载的记忆量，降低 token 消耗和延迟。

**实施：**
```python
# memory_loader.py
class MemoryLoader:
    def load_core(self):
        """加载核心记忆（常驻）"""
        return {
            'IDENTITY.md': read_file('IDENTITY.md'),
            'USER.md': read_file('USER.md'),
            'SOUL.md': read_file('SOUL.md'),
            'rules_derived.json': read_json('memory/lessons.json')
        }
    
    def load_recent(self, days=7):
        """加载最近记忆（短期）"""
        recent_files = get_files_in_range(
            'memory/',
            start_date=today - timedelta(days=days),
            end_date=today
        )
        return {f: read_file(f) for f in recent_files}
    
    def load_on_demand(self, path):
        """按需加载（长期）"""
        return read_file(path)
```

**收益：**
- 减少 50-70% 的记忆加载量
- 降低 context window 压力
- 加快启动速度

#### 建议 2：Memory Server 改为 HTTP API（中优先级）

**目标：** 消除冷启动延迟，支持并发查询。

**实施：**
```python
# memory_server.py
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import lancedb

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')  # 启动时加载一次
db = lancedb.connect('memory.db')

@app.post("/search")
def search(query: str, filters: dict = None, k: int = 5):
    # embedding 模型已热加载，秒级响应
    embedding = model.encode([query])[0]
    results = db.search(embedding, k=k, filters=filters)
    return results

@app.post("/ingest")
def ingest(text: str, metadata: dict):
    embedding = model.encode([text])[0]
    db.insert({'text': text, 'embedding': embedding, 'metadata': metadata})
    return {'status': 'ok'}
```

**启动方式：**
```bash
# 开机自启或手动启动
python memory_server.py
```

**收益：**
- 冷启动延迟从 9s → <1s
- 支持并发查询
- 可以独立重启，不影响主进程

#### 建议 3：引入元数据过滤（低优先级，观察期后）

**目标：** 提高检索精度，减少无关结果。

**实施：**
```python
# 在 memory 文件中增加 frontmatter
# memory/2026-03-10.md
---
date: 2026-03-10
tags: [coder-dispatcher, timeout, failure-analysis]
type: daily
priority: high
---

# 2026-03-10 日志
...
```

```python
# 检索时支持过滤
results = memory_search(
    query="coder-dispatcher 失败原因",
    filters={
        'date_range': ('2026-02-25', '2026-03-10'),
        'tags': ['coder-dispatcher', 'failure-analysis'],
        'type': 'daily'
    },
    k=5
)
```

**收益：**
- 减少无关结果
- 提高检索精度
- 支持时间范围查询

---

## 总结

**今天学到的最重要的一点：**

Memory Server 的价值不是"一直运行"，而是 **消除冷启动 + 支持分层加载 + 维持检索索引**。

Letta 的 MemFS 设计最值得借鉴：把记忆当成 git-backed filesystem，Agent 通过 bash 工具操作，分层可见性（system/ 常驻，其他按需加载），Git 版本控制支持回滚和并行编辑。

太极OS 当前最大的差距是 **没有分层加载**，每次都加载所有记忆，导致 token 消耗高、延迟大。

**观察期后的优先级：**
1. 引入分层加载（高）
2. Memory Server 改为 HTTP API（中）
3. 引入元数据过滤（低）

---

**研究时间：** 2026-03-10 20:43 - 20:50  
**研究者：** 小九  
**存档 ID：** （待生成）
