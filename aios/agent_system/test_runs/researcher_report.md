# AIOS / Agent OS 领域 GitHub 热门项目研究报告

> 调研时间：2026-02-26
> 数据来源：GitHub 仓库页面实时抓取

---

## 概述

本报告调研了 GitHub 上与 AIOS（AI Agent Operating System）相关的开源项目，按 Star 数排序筛选出 Top 3，并分析其核心架构与特点。

---

## Top 3 项目一览

| 排名 | 项目 | Star 数 | 语言 | 最近更新 |
|------|------|---------|------|----------|
| 1 | [agiresearch/AIOS](https://github.com/agiresearch/AIOS) | ⭐ 5.2k | Python | 2025-01 (持续活跃) |
| 2 | [OS-Copilot/OS-Copilot](https://github.com/OS-Copilot/OS-Copilot) | ⭐ 1.8k | Python | 2024-09 |
| 3 | [BAI-LAB/MemoryOS](https://github.com/BAI-LAB/MemoryOS) | ⭐ 1.2k | Python | 2026-02 (持续活跃) |

> 备注：Nuwax Agent OS（681 stars）作为新兴项目值得关注，但未进入 Top 3。

---

## 1. agiresearch/AIOS — AI Agent Operating System

**⭐ 5.2k** | 论文被 COLM 2025 接收 | Rutgers 大学团队

### 核心架构

AIOS 采用经典的 **内核 + SDK 双层架构**：

- **AIOS Kernel**（本仓库）：作为 OS 内核的抽象层，管理 Agent 所需的各类资源
  - LLM Core(s)：统一接入 OpenAI / Anthropic / DeepSeek / Ollama / vLLM 等
  - Context Manager：上下文切换与管理
  - Memory Manager：Agent 记忆管理
  - Storage Manager：持久化存储
  - Tool Manager：工具调用管理
  - Scheduler：Agent 任务调度（FIFO / RR 等策略）

- **AIOS SDK (Cerebrum)**（独立仓库）：面向 Agent 开发者和用户
  - Agent 开发、部署、分发、发现平台
  - 通过 syscall 链与 Kernel 交互

### 关键特点

1. **多部署模式**：支持 5 种部署模式（本地内核 → 远程内核 → 个人远程内核 → 虚拟化内核），从单机到分布式逐步演进
2. **Computer-Use Agent 支持**：通过 LiteCUA 架构，将 VM 作为 MCP Server，Agent 可安全操作虚拟机
3. **语义文件系统**：LLM-based Terminal UI，用自然语言操作文件系统（ICLR 2025 论文）
4. **广泛框架兼容**：支持 ReAct、AutoGen、MetaGPT、Open Interpreter 等主流 Agent 框架
5. **Rust 重写计划**：`aios-rs/` 目录已有 trait 脚手架，面向性能优化
6. **学术背景深厚**：多篇顶会论文（COLM 2025, NAACL 2025, ICLR 2025）

### 架构亮点

```
Agent App (via Cerebrum SDK)
        ↓ syscall
   ┌─────────────────────────┐
   │      AIOS Kernel        │
   │  ┌───────┐ ┌─────────┐  │
   │  │Scheduler│ │LLM Core│  │
   │  └───────┘ └─────────┘  │
   │  ┌───────┐ ┌─────────┐  │
   │  │Memory │ │ Storage │  │
   │  └───────┘ └─────────┘  │
   │  ┌───────┐ ┌─────────┐  │
   │  │Context│ │  Tool   │  │
   │  └───────┘ └─────────┘  │
   └─────────────────────────┘
        ↓
   Host Operating System
```

---

## 2. OS-Copilot — Generalist Computer Agent with Self-Improvement

**⭐ 1.8k** | ICLR 2024 LLM Agents Workshop | 上海 AI Lab 团队

### 核心架构

OS-Copilot 的核心 Agent 名为 **FRIDAY**，采用 **自我改进的具身对话代理** 架构：

- **Planner**：将用户自然语言指令分解为可执行的子任务
- **Configurator**：为每个子任务配置合适的工具或生成新工具
- **Actor**：执行具体操作（代码执行、API 调用、GUI 操作）
- **Self-Learning Module**：从执行经验中学习，自动积累工具库

### 关键特点

1. **全面 OS 交互**：可操作 Web、终端、文件系统、多媒体、第三方应用
2. **自我改进能力**：Agent 能从失败中学习，自动创建和改进工具
3. **视觉能力**：2024.9 新增 `friday_vision`，支持 GUI 视觉理解
4. **工具可扩展**：支持自定义 API 工具和本地工具注册
5. **前端界面**：提供 Web UI 进行交互控制
6. **面向通用性**：目标是成为通用计算机代理，而非特定领域

### 与 AIOS 的区别

| 维度 | AIOS | OS-Copilot |
|------|------|------------|
| 定位 | Agent 操作系统（平台） | 通用计算机代理（单 Agent） |
| 核心思路 | LLM as OS, Agents as Apps | Self-improving embodied agent |
| 多 Agent | ✅ 多 Agent 调度 | ❌ 单 Agent (FRIDAY) |
| 自我改进 | ❌ | ✅ 核心特性 |

---

## 3. BAI-LAB/MemoryOS — Memory Operating System for AI Agents

**⭐ 1.2k** | EMNLP 2025 Oral | 北京邮电大学百家 AI 团队

### 核心架构

MemoryOS 专注于为 AI Agent 提供 **分层记忆管理系统**，模拟人类记忆机制：

- **Short-Term Memory（短期记忆）**：容量有限的近期对话缓存
- **Mid-Term Memory（中期记忆）**：基于热度阈值的中期记忆，频繁访问的信息会被保留
- **Long-Term Knowledge（长期知识）**：持久化的用户画像和知识库
- **Retrieval Queue（检索队列）**：智能检索机制，跨层级查找相关记忆

### 关键特点

1. **三层记忆架构**：短期 → 中期 → 长期，模拟人类记忆的遗忘与巩固
2. **用户画像生成**：自动从对话历史中分析用户性格、偏好、知识背景
3. **MCP 协议支持**：提供 `memoryos-mcp` 服务，可被任意 MCP 客户端（如 Cline）调用
4. **多种嵌入模型**：支持 Qwen3-Embedding、BGE-M3、MiniLM 等
5. **ChromaDB 版本**：提供基于 ChromaDB 的向量存储实现
6. **Docker 部署**：官方镜像，一键启动
7. **Playground**：提供可视化交互界面

### 架构亮点

```
User Query
    ↓
┌──────────────────────────────┐
│         MemoryOS             │
│                              │
│  ┌────────────────────────┐  │
│  │  Short-Term Memory     │  │  ← 最近对话（容量限制）
│  │  (capacity=7)          │  │
│  └──────────┬─────────────┘  │
│             ↓ 热度升级        │
│  ┌────────────────────────┐  │
│  │  Mid-Term Memory       │  │  ← 热度 > 阈值的记忆
│  │  (heat_threshold=5)    │  │
│  └──────────┬─────────────┘  │
│             ↓ 知识沉淀        │
│  ┌────────────────────────┐  │
│  │  Long-Term Knowledge   │  │  ← 用户画像 + 持久知识
│  │  (capacity=100)        │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │  Retrieval Queue       │  │  ← 跨层智能检索
│  └────────────────────────┘  │
└──────────────────────────────┘
    ↓
Agent Response (with context)
```

---

## 横向对比总结

| 维度 | AIOS (5.2k⭐) | OS-Copilot (1.8k⭐) | MemoryOS (1.2k⭐) |
|------|---------------|---------------------|-------------------|
| 核心定位 | Agent 操作系统平台 | 自我改进的通用计算机代理 | Agent 记忆管理系统 |
| 解决的问题 | Agent 调度、资源管理、部署 | 自动化日常 OS 操作 | Agent 个性化记忆与上下文 |
| 架构层级 | Kernel + SDK 双层 | Planner-Configurator-Actor | 短期-中期-长期三层记忆 |
| 多 Agent 支持 | ✅ | ❌ | ✅（作为组件嵌入） |
| 学术论文 | COLM/NAACL/ICLR 2025 | ICLR 2024 Workshop | EMNLP 2025 Oral |
| 活跃度 | 🟢 非常活跃 | 🟡 中等 | 🟢 非常活跃 |
| 适用场景 | 构建多 Agent 平台 | 桌面自动化 | 为任意 Agent 添加记忆能力 |

---

## 趋势观察

1. **OS 隐喻成为主流**：越来越多项目用操作系统的概念（调度、内存、存储）来组织 Agent 系统
2. **MCP 协议普及**：MemoryOS 和 AIOS 都在拥抱 MCP，成为 Agent 互操作的标准
3. **记忆管理独立化**：MemoryOS 的成功说明 Agent 记忆是一个独立且重要的子领域
4. **学术驱动**：Top 3 项目全部有顶会论文支撑，学术界在 Agent OS 领域非常活跃
5. **中国团队主导**：三个项目分别来自 Rutgers（华人团队）、上海 AI Lab、北邮，中国研究者在该领域贡献突出
