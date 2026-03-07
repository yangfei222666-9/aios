# GitHub Agent/AIOS 生态全景 - 2026 Q1

> 调研时间：2026-03-06 | 调研人：小九
> 扫描范围：GitHub 近 3-6 个月活跃的 Agent/AIOS/Multi-Agent 项目
> 筛选标准：Stars > 500 或架构有独特价值

---

## 一、项目总览（18 个项目）

| # | 项目 | Stars | 语言 | 核心定位 | 最近更新 | 关注维度 |
|---|------|-------|------|---------|---------|---------|
| 1 | **openai/swarm** | 21.1k | Python | 轻量多Agent编排（教育性质） | 已停更→迁移到 Agents SDK | 编排 |
| 2 | **microsoft/agent-framework** | 7.7k | Python/.NET | 企业级Agent框架（原AutoGen+SK合并） | 活跃 | 编排/观测/调度 |
| 3 | **kyegomez/swarms** | 5.8k | Python | 企业级多Agent编排 | 活跃 | 编排/架构 |
| 4 | **agiresearch/AIOS** | 5.3k | Python | AI Agent操作系统（学术） | 活跃 | AIOS/调度/内存 |
| 5 | **VRSEN/agency-swarm** | 4k | Python | 可靠多Agent编排 | 活跃 | 编排/通信流 |
| 6 | **bytedance/deer-flow** | 趋势#1 | Python | SuperAgent Harness（研究+代码+创作） | 非常活跃 | 子Agent/沙箱/记忆 |
| 7 | **SolaceLabs/solace-agent-mesh** | 2.1k | Python | 事件驱动多Agent | 活跃 | 事件驱动 |
| 8 | **Kocoro-lab/Shannon** | 1.1k | Go/Rust | 生产级多Agent编排 | 活跃 | 容错/预算/观测 |
| 9 | **volcengine/OpenViking** | 趋势 | Python/Rust | Agent上下文数据库 | 非常活跃 | 记忆/检索 |
| 10 | **NevaMind-AI/memU** | 趋势 | Python | 24/7 主动Agent记忆 | 非常活跃 | 记忆/主动 |
| 11 | **trycua/cua** | 12.9k | Python | Computer-Use Agent基础设施 | 非常活跃 | 评估/沙箱 |
| 12 | **THUDM/AgentBench** | 3.2k | Python | Agent评估基准（ICLR'24） | 活跃 | 评估 |
| 13 | **sierra-research/tau2-bench** | 809 | Python | 对话Agent评估 | 活跃 | 评估 |
| 14 | **facebookresearch/meta-agents-research-environments** | 446 | Python | Meta Agent研究环境 | 活跃 | 评估 |
| 15 | **Doriandarko/make-it-heavy** | 1.1k | Python | 多Agent模拟Grok Heavy | 停更 | 架构参考 |
| 16 | **foreveryh/mentis** | 294 | Python | LangGraph多Agent编排 | 停更 | 架构参考 |
| 17 | **alibaba/OpenSandbox** | 趋势 | Python | 通用AI沙箱平台 | 活跃 | 沙箱/评估 |
| 18 | **LongCipher/TradingAgents** | - | Python | 金融多Agent（Bull vs Bear） | 已学习 | 对抗验证 |

---

## 二、深读 5 个项目（按对 AIOS 价值排序）

### 🥇 1. Shannon（Kocoro-lab）— 生产级多Agent编排

**为什么重要：** 这是目前开源项目中最接近"生产级AIOS"的实现，Go+Rust+Python 三语言架构。

**核心架构：**
- Orchestrator（Go）— 任务路由、预算执行、会话管理、OPA策略
- Agent Core（Rust）— WASI沙箱、策略执行、会话工作区
- LLM Service（Python）— 15+ LLM提供商抽象、MCP工具、技能系统
- 数据层 — PostgreSQL（状态）+ Redis（会话）+ Qdrant（向量记忆）

**亮点功能：**
- ⏪ **Time-Travel Debugging** — 可以回放任何执行步骤，逐步调试
- 💰 **Token Budget Control** — 硬预算限制 + 自动模型降级（80%预算时切换便宜模型）
- 🔒 **WASI Sandbox** — 代码在隔离沙箱执行，无网络、只读文件系统
- 👤 **Human-in-the-Loop** — 敏感操作暂停等待人工审批
- 📊 **完整观测** — Prometheus + OpenTelemetry + Grafana + 实时SSE事件流
- 🐝 **Swarm模式** — P2P多Agent协作，无中央监督者
- 📋 **OPA策略治理** — 基于团队/角色的权限控制
- ⏰ **定时任务** — Cron调度 + 每次运行预算上限

**对我们的启发：**
1. Time-Travel Debugging 是我们完全缺失的能力
2. Token Budget 硬限制 + 自动降级比我们的方案更成熟
3. WASI沙箱比Docker更轻量安全
4. OPA策略治理是企业级必备

---

### 🥈 2. DeerFlow 2.0（ByteDance）— SuperAgent Harness

**为什么重要：** 字节跳动出品，2026-02-28 登顶 GitHub Trending #1，从深度研究框架进化为通用SuperAgent。

**核心架构：**
- 基于 LangGraph + LangChain
- 子Agent动态生成 — Lead Agent按需spawn子Agent，各自独立上下文
- 沙箱文件系统 — 每个任务在隔离Docker容器中运行
- 技能系统 — SKILL.md格式，渐进式加载（按需加载，不一次性塞满上下文）
- MCP Server支持 — 可扩展工具

**亮点功能：**
- 🧠 **Context Engineering** — 子Agent隔离上下文 + 自动摘要压缩 + 中间结果卸载到文件系统
- 📁 **沙箱文件系统** — /mnt/user-data/{uploads, workspace, outputs}
- 🔧 **渐进式技能加载** — 只在需要时加载技能，保持上下文窗口精简
- 🧵 **长期记忆** — 跨会话持久化用户画像、偏好、知识
- 🐍 **嵌入式Python客户端** — 可作为库直接调用，不需要HTTP服务

**对我们的启发：**
1. 渐进式技能加载 — 我们的Agent加载所有技能太浪费token
2. Context Engineering — 子Agent隔离 + 自动摘要是我们需要的
3. 嵌入式客户端模式 — 可以让AIOS作为库被其他项目调用

---

### 🥉 3. OpenViking（火山引擎）— Agent上下文数据库

**为什么重要：** 专门解决Agent上下文管理问题，用文件系统范式统一管理记忆/资源/技能。

**核心架构：**
- viking:// 虚拟文件系统 — 统一URI管理所有上下文
- L0/L1/L2 三层上下文 — 摘要(~100 tokens) / 概览(~2k tokens) / 完整内容
- 目录递归检索 — 先锁定高分目录，再精细探索内容
- 可视化检索轨迹 — 可观测的检索路径

**亮点功能：**
- 📂 **文件系统范式** — ls/find/tree 操作上下文，像开发者管理文件
- 📊 **三层加载** — 按需加载，大幅节省token（实测比LanceDB节省92%+）
- 🔍 **递归检索** — 意图分析→初始定位→精细探索→递归下钻→结果聚合
- 👁️ **可视化轨迹** — 检索路径可观测，方便调试
- 🤖 **VikingBot** — 内置Agent框架
- 📈 **实测数据** — 比原生OpenClaw记忆提升43-49%，token成本降低83-96%

**对我们的启发：**
1. L0/L1/L2 三层上下文加载 — 我们的记忆系统缺少分层
2. 文件系统范式管理上下文 — 比我们的扁平JSON更结构化
3. 可视化检索轨迹 — 我们的记忆检索是黑盒

---

### 4. memU（NevaMind-AI）— 24/7主动Agent记忆

**为什么重要：** 专为长时间运行的主动Agent设计的记忆框架，和我们的使用场景高度匹配。

**核心架构：**
- Memory as File System — 分层记忆（preferences/relationships/knowledge/context）
- 三层记忆 — Resource（原始数据）/ Item（提取的事实）/ Category（自动分类）
- 双模式检索 — RAG（毫秒级）+ LLM（深度推理）
- 主动记忆生命周期 — 监控→记忆→预测意图→主动执行

**亮点功能：**
- 🤖 **主动意图捕获** — 理解用户即将做什么，提前行动
- 💰 **成本高效** — 缓存洞察，避免冗余LLM调用
- 🔄 **持续学习** — memorize() 实时处理，零延迟
- 📊 **92.09% Locomo准确率** — 有benchmark验证
- 🧩 **完整生态** — memU + memU-server + memU-ui

**对我们的启发：**
1. 主动意图预测 — 我们的记忆是被动的，缺少预测能力
2. 双模式检索 — RAG快速 + LLM深度，按场景选择
3. 有benchmark验证 — 我们缺少记忆系统的量化评估

---

### 5. Microsoft Agent Framework — 企业级Agent框架

**为什么重要：** 微软官方出品，AutoGen + Semantic Kernel 合并后的统一框架。

**核心架构：**
- Graph-based Workflows — DAG编排，支持streaming/checkpointing/human-in-the-loop/time-travel
- AF Labs — 实验性功能（benchmarking、强化学习）
- DevUI — 交互式开发调试UI
- OpenTelemetry — 内置分布式追踪
- Middleware — 灵活的中间件系统

**亮点功能：**
- 📊 **Graph Workflows** — 数据流编排 + checkpoint + time-travel
- 🔍 **DevUI** — 可视化Agent开发调试
- 📡 **OpenTelemetry** — 分布式追踪和监控
- 🔌 **Middleware** — 请求/响应处理管道
- 🌐 **Python + .NET** — 双语言支持

**对我们的启发：**
1. Graph Workflow + Checkpoint — 我们的任务编排缺少checkpoint和恢复
2. DevUI — 可视化调试工具是开发体验的关键
3. Middleware模式 — 可以用来实现我们的安全护栏

---

## 三、趋势总结

### 2026 Q1 Agent生态关键趋势

1. **从框架到平台** — 单纯的Agent框架已不够，需要完整的运行时（沙箱、文件系统、记忆、调度）
2. **上下文工程崛起** — OpenViking/memU/DeerFlow都在解决"如何高效管理Agent上下文"
3. **生产级要求提高** — Shannon/Microsoft AF 都强调观测性、预算控制、安全沙箱
4. **记忆系统专业化** — 从简单的向量检索进化到分层记忆、主动记忆、文件系统范式
5. **评估基准成熟** — AgentBench/tau2-bench/cua-bench 提供标准化评估
6. **技能系统标准化** — SKILL.md 格式被多个项目采用（DeerFlow、Swarms、Shannon）
7. **Time-Travel Debugging** — Shannon和Microsoft AF都支持执行回放

---

*调研完成。详细对比分析见 `aios_gap_analysis.md`，改进建议见 `next_3_upgrades.md`。*
