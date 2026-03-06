# GitHub 情报扫描 2026-03-06

## 执行摘要

本次扫描覆盖 AIOS/Agent OS、Agent Marketplace、Adversarial Validation、Self-Improving Agent、Agent Orchestration 五大方向，共分析 11 个高活跃项目。最大发现：**Skills 标准化生态正在形成行业共识**（OpenAI/HuggingFace/Anthropic 三方同时推出 Agent Skills 格式），以及 **ByteDance DeerFlow 2.0 以 SuperAgent Harness 架构登顶 GitHub Trending**，其 subagent + sandbox + memory 三位一体设计与我们 AIOS 高度重叠但执行层更完整。建议优先级：Skills 标准化接入（高）> 沙箱隔离执行（高）> 分层上下文数据库（中）。

---

## 项目清单（11个）

### 1. agiresearch/AIOS ⭐ ~5k（持续增长）
- **why_now**: COLM 2025 论文接收，v0.2.2 大重构，LiteCUA 计算机使用 agent 集成，NAACL 2025 Cerebrum SDK 论文发表，近 30 天多次 release
- **what_to_copy**: Kernel + SDK 分离架构（AIOS Kernel 管资源调度，Cerebrum SDK 面向开发者）；AgentHub 分发机制（upload/download/list agent）；LLM 调度层（context switch、memory management、tool management 统一抽象）；MCP Server 集成 VM Controller 做沙箱
- **risk**: 中（架构相似，需区分定位）
- **effort**: 3
- **decision**: 延后（持续跟踪，重点学习 Kernel/SDK 分离边界设计）

### 2. agiresearch/Cerebrum ⭐ ~1.5k
- **why_now**: AIOS 官方 SDK，AgentHub 已上线（app.aios.foundation），支持 agent 上传/下载/运行，NAACL 2025 论文
- **what_to_copy**: AgentHub CLI 命令集（list-agenthub-agents / download-agent / upload-agent / list-toolhub-tools）；agent 目录结构标准（entry.py + config.json + meta_requirements.txt）；ToolHub 与 AgentHub 双市场并行设计
- **risk**: 低
- **effort**: 2
- **decision**: 做（参考 AgentHub 的 agent 打包规范，升级我们本地 Agent 市场的 manifest 格式）

### 3. bytedance/DeerFlow ⭐ 登顶 GitHub Trending（2026-02-28 #1）
- **why_now**: 2.0 完全重写，2026-02-28 登顶 GitHub Trending，SuperAgent Harness 概念：orchestrates sub-agents + memory + sandboxes + skills；BytePlus InfoQuest 搜索工具集成；Docker/K8s 多模式沙箱
- **what_to_copy**: SuperAgent Harness 模式（主 agent 调度 subagent 处理不同层级任务）；三层沙箱模式（Local/Docker/K8s 按需切换）；Skills 扩展机制（MCP Server + OAuth token flow）；config.yaml 统一模型配置（支持任意 LangChain provider）
- **risk**: 中（依赖 LangChain 生态）
- **effort**: 4
- **decision**: 延后（沙箱模式值得借鉴，但整体架构重叠度高，选择性吸收）

### 4. volcengine/OpenViking ⭐ 新项目（trending）
- **why_now**: 字节跳动火山引擎开源，专为 AI Agent 设计的 Context Database，文件系统范式统一管理 memory/resources/skills，L0/L1/L2 三层按需加载
- **what_to_copy**: **L0/L1/L2 分层上下文加载**（L0=目录索引，L1=摘要，L2=全文，按需展开，大幅节省 token）；目录递归检索（目录定位 + 语义搜索组合）；可视化检索轨迹（debug RAG 问题）；自动会话压缩提取长期记忆
- **risk**: 低（纯库，无侵入性）
- **effort**: 3
- **decision**: 做（L0/L1/L2 分层加载直接可用于优化我们的 LanceDB 经验库检索，降低 token 消耗）

### 5. alibaba/OpenSandbox ⭐ 新项目（trending）
- **why_now**: 阿里开源，多语言 SDK（Python/Java/TS/Go），统一沙箱 API，支持 Docker/K8s，内置 gVisor/Kata/Firecracker 强隔离，已集成 Claude Code/Gemini CLI/Codex CLI
- **what_to_copy**: 沙箱生命周期管理 API（create/kill/timeout）；统一 Ingress Gateway + per-sandbox egress 网络策略；强隔离运行时（gVisor/Firecracker）用于高风险 agent 执行；Code Interpreter SDK 模式
- **risk**: 中（需要 Docker/K8s 基础设施）
- **effort**: 4
- **decision**: 延后（当 Agent 市场需要执行用户上传 agent 时，OpenSandbox 是首选沙箱方案）

### 6. letta-ai/letta ⭐ 21.4k（持续高活跃，2天前更新）
- **why_now**: 前 MemGPT，stateful agent 平台，支持 continual learning，推荐 Opus 4.5 和 GPT-5.2，有 model leaderboard，Skills + Subagents 内置，2天前仍在更新
- **what_to_copy**: **memory_blocks 设计**（human/persona 分块，agent 可读写自己的记忆）；continual learning 机制（agent 随使用变聪明）；model leaderboard（评估不同模型在 agent 任务上的表现）；Letta Code CLI（本地运行 agent + memory）
- **risk**: 低
- **effort**: 2
- **decision**: 做（memory_blocks 分块设计可直接借鉴，增强我们 LanceDB 经验库的结构化程度）

### 7. FoundationAgents/MetaGPT ⭐ ~50k
- **why_now**: MGX（MetaGPT X）2025-02-19 发布，ProductHunt #1，AFlow（自动化 agentic workflow 生成）ICLR 2025 oral，SPO/AOT 新论文
- **what_to_copy**: **AFlow 自动化工作流生成**（用 LLM 自动生成和优化 agent workflow，类似我们的 64 卦决策但更系统化）；SOP 团队模式（Product Manager/Architect/Engineer 角色分工）；Debate 用例（内置辩论 agent 示例）
- **risk**: 低
- **effort**: 3
- **decision**: 延后（AFlow 论文值得深读，自动化 workflow 生成是我们 Evolution Score 提升的潜在路径）

### 8. microsoft/AutoGen ⭐ ~40k（持续活跃）
- **why_now**: AgentChat + AutoGen Studio，AgentTool 支持 agent 作为工具调用其他 agent，MCP Workbench 集成，Microsoft Agent Framework 新公告
- **what_to_copy**: **AgentTool 模式**（agent 作为工具被其他 agent 调用，实现嵌套编排）；McpWorkbench（多 MCP server 统一管理）；AutoGen Studio 无代码 GUI（agent workflow 可视化编排）
- **risk**: 低
- **effort**: 2
- **decision**: 做（AgentTool 嵌套调用模式可增强我们的 Spawn Lock 方案，实现更细粒度的 agent 编排）

### 9. openai/skills + huggingface/skills + obra/superpowers ⭐ 行业标准化趋势
- **why_now**: OpenAI Codex、HuggingFace、Anthropic Claude Code、Google Gemini CLI 同时采用 Agent Skills 标准（SKILL.md + .agents/skills/ 目录）；obra/superpowers 实现了完整的 subagent-driven-development 工作流；jeffallan/claude-skills 提供 66 个专业技能
- **what_to_copy**: **Agent Skills 标准格式**（SKILL.md + YAML frontmatter，跨平台兼容）；Superpowers 的 subagent-driven-development（每个任务派发独立 subagent，两阶段 review）；技能自动激活机制（agent 根据任务类型自动加载相关 skill）
- **risk**: 低
- **effort**: 2
- **decision**: 做（我们的 AGENTS.md/TOOLS.md 体系可升级为标准 Skills 格式，提升与外部生态的互操作性）

### 10. composiohq/composio ⭐ ~20k（高活跃）
- **why_now**: 1000+ toolkits，统一工具搜索 + 上下文管理 + 认证 + 沙箱工作台，支持 OpenAI/Anthropic/LangChain/CrewAI/AutoGen 等全主流框架
- **what_to_copy**: **工具市场设计**（1000+ 预集成工具，按 toolkit 分组，用户级认证隔离）；context management（工具调用上下文自动管理）；sandboxed workbench（工具执行沙箱）
- **risk**: 低
- **effort**: 2
- **decision**: 延后（我们 Agent 市场 MVP 稳定后，参考 Composio 的 toolkit 分组和认证模型扩展工具生态）

### 11. MAD (Multi-Agent Debate) ⭐ 526（NeurIPS 2025 Spotlight）
- **why_now**: NeurIPS 2025 Spotlight 论文"Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs?"，526 stars，多 agent 辩论 vs 投票决策对比研究，ICASSP 2026 Agent4Debate
- **what_to_copy**: **Debate vs Vote 决策机制对比**（辩论适合开放性问题，投票适合收敛性决策）；Bayesian Nash Equilibrium 信念驱动辩论（ICML 2025）；动态角色分配（Searcher/Analyzer/Writer/Reviewer）
- **risk**: 低
- **effort**: 2
- **decision**: 做（直接增强我们已上线的 Bull vs Bear Adversarial Validation，引入 Debate vs Vote 动态切换机制）

---

## 5个核心借鉴点

### 1. 架构：Skills 标准化 + Kernel/SDK 分离

**来源**: OpenAI/HuggingFace/Anthropic Skills 标准 + AIOS Kernel/Cerebrum SDK 分离

当前行业正在形成 Agent Skills 标准（SKILL.md + .agents/skills/），三大 AI 公司同时采用。AIOS 的 Kernel/SDK 分离提供了清晰的资源管理边界。

**对 AIOS 的意义**: 将我们的 AGENTS.md/TOOLS.md 升级为标准 Skills 格式，同时明确 AIOS Core（调度/记忆/工具）与 Agent SDK（用户开发接口）的边界。

### 2. 评估：Debate vs Vote 动态决策 + Model Leaderboard

**来源**: MAD/NeurIPS 2025 + Letta model leaderboard

我们已有 Bull vs Bear 辩论，但缺乏"何时辩论、何时投票"的动态切换逻辑。Letta 的 model leaderboard 提供了 agent 任务维度的模型评估基准。

**对 AIOS 的意义**: Adversarial Validation 增加 Debate/Vote 模式选择器（开放性问题→辩论，收敛性决策→投票）；建立 AIOS 内部 model benchmark。

### 3. 商业化：AgentHub 双市场 + Composio Toolkit 分组

**来源**: AIOS Cerebrum AgentHub + Composio 1000+ toolkits

Agent 市场的商业化路径：Agent 市场（按功能分类）+ Tool 市场（按 toolkit 分组）双轨并行，用户级认证隔离是关键。

**对 AIOS 的意义**: 我们本地 Agent 市场 MVP 升级路径：增加 ToolHub、标准化 agent manifest（entry.py + config.json + meta_requirements.txt）、引入用户级工具认证。

### 4. 运维：L0/L1/L2 分层上下文 + 沙箱执行隔离

**来源**: OpenViking L0/L1/L2 + OpenSandbox/DeerFlow 沙箱

L0/L1/L2 分层加载大幅降低 token 消耗（只在需要时展开全文）。沙箱隔离是 Agent 市场安全运行的基础设施。

**对 AIOS 的意义**: LanceDB 经验库增加分层索引（L0=标签/摘要，L1=关键步骤，L2=完整记录）；LowSuccess_Agent 重生执行引入 Docker 沙箱隔离。

### 5. 安全：DM Pairing 策略 + 沙箱强隔离 + 工具执行审计

**来源**: OpenClaw DM pairing + OpenSandbox gVisor/Firecracker + Composio sandboxed workbench

Agent 安全三层：输入层（DM pairing，未知来源需配对验证）、执行层（沙箱隔离，gVisor/Firecracker）、工具层（per-sandbox egress 网络策略）。

**对 AIOS 的意义**: Agent 市场上线外部 agent 前，必须引入执行沙箱；工具调用增加 audit log；高风险操作（文件删除/网络请求）需二次确认。

---

## 映射到 AIOS Roadmap

| 借鉴点 | 对应 AIOS 模块 | 优先级 | 预计工期 |
|--------|---------------|--------|---------|
| Agent Skills 标准格式（SKILL.md） | AGENTS.md / TOOLS.md 体系 | 高 | 1天 |
| Debate vs Vote 动态切换 | Adversarial Validation（Bull vs Bear） | 高 | 2-3天 |
| memory_blocks 分块设计 | LanceDB 经验库结构化 | 高 | 2天 |
| AgentTool 嵌套调用 | Spawn Lock / Agent 编排 | 中 | 3-5天 |
| L0/L1/L2 分层上下文加载 | LanceDB 经验库检索优化 | 中 | 3天 |
| Agent manifest 标准化 | Agent 市场 MVP 升级 | 中 | 2天 |
| Docker 沙箱隔离执行 | LowSuccess_Agent 重生执行 | 中 | 5天 |
| AFlow 自动化 workflow 生成 | 64卦决策系统扩展 | 低 | 2周+ |
| Composio Toolkit 分组 | Agent 市场 ToolHub | 低 | 1周+ |

---

## 结论

**做（近期执行）**:
- **Agent Skills 标准化**: 将 AGENTS.md/TOOLS.md 升级为 SKILL.md 格式，1天，低风险
- **Debate vs Vote 切换器**: 增强 Adversarial Validation，引入开放/收敛问题的模式选择，2-3天
- **memory_blocks 分块**: 参考 Letta，LanceDB 经验库增加 human/persona/task 分块结构，2天
- **AgentTool 嵌套调用**: 参考 AutoGen，Spawn Lock 支持 agent-as-tool 调用模式，3-5天

**延后（Agent 市场稳定后）**:
- **L0/L1/L2 分层加载**: 等 LanceDB 经验库数据量达到 1000+ 条后再优化检索层
- **Docker 沙箱隔离**: 等 Agent 市场开放外部 agent 上传时引入
- **DeerFlow SuperAgent Harness**: 持续跟踪，选择性吸收 subagent 调度模式
- **Composio ToolHub**: Agent 市场 MVP v2 阶段引入

**不做**:
- **完整复制 AIOS Kernel**: 定位重叠，我们走差异化路线（64卦决策 + 失败重生 + 本地优先）
- **moeru-ai/airi**: VTuber 方向，与 AIOS 定位无关

---

---

## Roadmap 决策摘要（2026-03-06）

### Go Now（本周立即做）

| 项目 | effort | 理由 | 状态 |
|------|--------|------|------|
| SKILL.md 标准化 | 1 | 生态接入门槛票，低风险高兼容 | ✅ 已落地 `aios/skills/bull_bear_debate_decision/SKILL.md` |
| Debate ↔ Vote 动态切换 | 2 | 直接增强现有 Bull/Bear 决策质量 | ⏳ D3-D4 |
| AgentHub manifest 兼容层 | 2 | 低成本换分发能力 | ⏳ D5 |

### Go Next（1–2 个迭代后）

| 项目 | effort | 备注 |
|------|--------|------|
| memory_blocks 分块记忆 | 2 | 先做轻量版（按主题/会话切块） |
| AgentTool 嵌套调用 | 3 | 先限制 1 层嵌套，避免复杂度失控 |
| L0/L1/L2 分层上下文 | 3 | 等样本量 1000+ 再上，当前先预埋接口 |

### Later / Guarded（延后）

| 项目 | effort | 触发条件 |
|------|--------|---------|
| Docker 沙箱隔离 | 4 | 外部 agent 执行需求明确后启动 |
| 全面 Agent Marketplace 化 | — | manifest 兼容验证分发效果后再决定 |

### 优先级

- **P0**: SKILL.md、Debate/Vote、manifest 兼容
- **P1**: memory_blocks、AgentTool 嵌套
- **P2**: L0/L1/L2（数据门槛达标后）
- **P3**: Docker 沙箱

---

## 未来 2 周执行序列

### Week 1

| 天 | 任务 |
|----|------|
| D1-D2 | 落地 SKILL.md 规范 + 3 个示例技能 |
| D3-D4 | 实现 Debate/Vote 策略切换（阈值+状态机） |
| D5 | 接入 manifest 兼容层，完成最小可发布包 |
| D6-D7 | 联调与回归，补充指标看板（命中率、切换次数、决策延迟） |

### Week 2

| 天 | 任务 |
|----|------|
| D8-D9 | 上线轻量 memory_blocks（主题分块 + TTL） |
| D10-D11 | 实现 AgentTool 单层嵌套 + 熔断保护 |
| D12 | 预埋 L0/L1/L2 接口与数据采样埋点 |
| D13-D14 | 复盘与优先级重排，决定是否进入沙箱 PoC |

---

*决策摘要由珊瑚海提供 · 2026-03-06*

SCAN_COMPLETE
