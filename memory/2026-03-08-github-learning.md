# GitHub 学习报告 - 2026-03-08

## 今日学习目标
搜索 Agent Runtime / Orchestration / Self-Improving 方向的高质量项目，拆解架构，对比 AIOS，输出可执行改进建议。

---

## 项目 1: OpenFang - Agent Operating System

### 核心价值
- **定位：** 真正的 Agent OS，不是聊天框架
- **核心创新：** Hands（自主能力包）- 预构建的自主 Agent，按计划运行，无需人工触发
- **语言：** Rust（137K LOC，14 crates，1767+ 测试）
- **特点：** 单二进制（32MB），冷启动 <200ms，内存占用 40MB

### 架构亮点

#### 1. Hands 系统（最值得学习）
- **概念：** 不是等你输入的聊天机器人，而是主动为你工作的 Agent
- **7 个内置 Hands：**
  - Clip - YouTube 视频自动剪辑成短视频
  - Lead - 每日自动发现潜在客户
  - Collector - OSINT 级情报收集
  - Predictor - 超级预测引擎
  - Researcher - 深度研究 Agent
  - Twitter - 自主 Twitter 账号管理
  - Browser - Web 自动化 Agent

- **每个 Hand 包含：**
  - HAND.toml - 清单（工具、设置、要求、指标）
  - System Prompt - 多阶段操作手册（500+ 字专家流程）
  - SKILL.md - 领域专业知识
  - Guardrails - 敏感操作审批门

#### 2. 16 层安全系统（Defense in Depth）
1. WASM Dual-Metered Sandbox - 工具代码在 WebAssembly 中运行
2. Merkle Hash-Chain Audit Trail - 每个操作加密链接
3. Information Flow Taint Tracking - 秘密从源到汇的追踪
4. Ed25519 Signed Agent Manifests - 加密签名的 Agent 身份
5. SSRF Protection - 阻止私有 IP、云元数据端点
6. Secret Zeroization - API 密钥自动从内存擦除
7. OFP Mutual Authentication - HMAC-SHA256 P2P 认证
8. Capability Gates - 基于角色的访问控制
9. Security Headers - CSP, X-Frame-Options, HSTS
10. Health Endpoint Redaction - 公共健康检查最小化信息
11. Subprocess Sandbox - 进程树隔离
12. Prompt Injection Scanner - 检测覆盖尝试
13. Loop Guard - SHA256 工具调用循环检测
14. Session Repair - 7 阶段消息历史验证
15. Path Traversal Prevention - 规范化防止符号链接逃逸
16. GCRA Rate Limiter - 成本感知令牌桶限流

#### 3. 架构模块（14 个 Rust crates）
- openfang-kernel - 编排、工作流、计量、RBAC、调度器
- openfang-runtime - Agent 循环、3 个 LLM 驱动、53 工具、WASM 沙箱
- openfang-api - 140+ REST/WS/SSE 端点
- openfang-channels - 40 消息适配器
- openfang-memory - SQLite 持久化、向量嵌入
- openfang-skills - 60 个捆绑技能
- openfang-hands - 7 个自主 Hands
- openfang-wire - OFP P2P 协议

#### 4. 性能指标
- 冷启动：180ms（vs OpenClaw 5.98s）
- 内存占用：40MB（vs OpenClaw 394MB）
- 安装大小：32MB（vs OpenClaw 500MB）
- 安全系统：16 层（vs OpenClaw 3 层）
- 通道适配器：40（vs OpenClaw 13）

### AIOS 对比

#### AIOS 优势
1. **已有的自学习闭环** - Self-Improving Loop 已经在运行
2. **任务队列系统** - task_queue.jsonl + heartbeat 自动处理
3. **Learning Agents** - 已有 GitHub_Researcher 等学习 Agent
4. **Dashboard** - 可视化观测界面
5. **中文生态** - 更适合中文用户

#### AIOS 缺口
1. **没有 Hands 概念** - 所有 Agent 都是被动触发，没有主动工作的 Agent
2. **安全层薄弱** - 只有基础的日志和状态检查，没有沙箱、审计链、污点追踪
3. **性能差距** - 启动慢、内存占用大（虽然不是主要问题）
4. **没有 WASM 沙箱** - 工具执行没有隔离
5. **没有审计链** - 操作记录可以被篡改
6. **没有 Capability Gates** - Agent 权限控制不够细粒度

### 可执行改进建议

#### P0 - 立刻可做
1. **引入 Hands 概念到 AIOS**
   - 在 `aios/agent_system/learning_agents.py` 中增加 `autonomous=True` 标记
   - 让 GitHub_Researcher、Bug_Hunter 等 Agent 变成 Hands
   - 修改 heartbeat 逻辑，让 Hands 主动运行，不等触发

2. **增加操作审计日志**
   - 在 `aios/agent_system/events.jsonl` 中增加操作链
   - 每个操作记录前一个操作的哈希（简化版 Merkle Chain）
   - 防止日志被篡改

#### P1 - 近期可做
3. **增加 Agent 权限控制**
   - 在 `agents.json` 中增加 `capabilities` 字段
   - 定义每个 Agent 可以使用的工具
   - 在执行前检查权限

4. **增加敏感操作审批门**
   - 在 `aios/agent_system/` 中增加 `approval_gates.py`
   - 定义哪些操作需要人工审批（删除文件、发送消息、执行命令）
   - 在执行前暂停，等待审批

#### P2 - 长期可做
5. **引入 WASM 沙箱**
   - 研究 wasmtime-py 或 wasmer-python
   - 让高风险工具在 WASM 中运行
   - 限制资源使用（CPU、内存、时间）

6. **增加污点追踪**
   - 标记敏感数据（API 密钥、密码）
   - 追踪数据流动
   - 防止泄露

---

## 项目 2: Microsoft Agent Framework

### 核心价值
- **定位：** 企业级多语言 Agent 框架（Python + .NET）
- **核心创新：** Graph-based Workflows + DevUI + Observability
- **背景：** 微软官方出品，从 Semantic Kernel 和 AutoGen 演进而来

### 架构亮点

#### 1. Graph-based Workflows
- **概念：** 用数据流连接 Agent 和确定性函数
- **特性：**
  - Streaming - 流式输出
  - Checkpointing - 检查点恢复
  - Human-in-the-loop - 人工介入
  - Time-travel - 时间旅行调试

#### 2. DevUI（开发者 UI）
- **功能：** 交互式开发、测试、调试工作流
- **价值：** 可视化 Agent 执行过程

#### 3. Observability（可观测性）
- **集成：** 内置 OpenTelemetry
- **功能：** 分布式追踪、监控、调试

#### 4. Middleware（中间件）
- **功能：** 请求/响应处理、异常处理、自定义管道
- **灵活性：** 可插拔架构

### AIOS 对比

#### AIOS 优势
1. **更轻量** - 不需要 .NET 运行时
2. **更专注** - 专注个人 AI OS，不是企业通用框架
3. **已有自学习** - Self-Improving Loop 已经在运行

#### AIOS 缺口
1. **没有 Graph 可视化** - Dashboard 只显示状态，不显示执行流
2. **没有 Checkpointing** - Agent 执行失败后无法从中间恢复
3. **没有 Time-travel** - 无法回溯调试
4. **没有 OpenTelemetry** - 观测性依赖日志，不够结构化

### 可执行改进建议

#### P0 - 立刻可做
1. **增加 Checkpointing**
   - 在 Agent 执行过程中定期保存状态
   - 失败后从最近的检查点恢复
   - 避免重复执行已完成的步骤

#### P1 - 近期可做
2. **增强 Dashboard 可视化**
   - 显示 Agent 执行流程图
   - 显示节点之间的数据流
   - 实时更新执行状态

3. **引入结构化日志**
   - 使用 structlog 或类似库
   - 统一日志格式
   - 方便后续分析

---

## 项目 3: Hive - Outcome-Driven Agent Framework

### 核心价值
- **定位：** 目标驱动、自适应、自我改进的 Agent 框架
- **核心创新：** 用自然语言描述目标，框架自动生成 Agent Graph
- **特点：** 失败时自动演进 Graph 并重新部署

### 架构亮点

#### 1. Goal-Driven Generation
- **概念：** 不手写工作流，用自然语言描述目标
- **流程：**
  1. 用户描述目标
  2. Coding Agent（Queen）生成 Agent Graph
  3. 生成连接代码
  4. 生成测试用例

#### 2. Adaptiveness（自适应）
- **概念：** 失败时自动演进
- **流程：**
  1. 捕获失败数据
  2. 根据目标校准
  3. 演进 Agent Graph
  4. 重新部署

#### 3. Dynamic Node Connections
- **概念：** 没有预定义边，连接代码由 LLM 生成
- **价值：** 灵活性高，适应性强

#### 4. Human-in-the-Loop
- **概念：** 介入节点暂停执行，等待人工输入
- **特性：** 可配置超时和升级策略

#### 5. Real-time Observability
- **技术：** WebSocket 流式传输
- **功能：** 实时监控 Agent 执行、决策、节点间通信

#### 6. 架构组件
- **Queen Bee** - 编码 Agent，生成和演进 Graph
- **Worker Bees** - 执行 Agent，运行 Graph 节点
- **Judge** - 评估 Agent 输出是否符合目标
- **Event Loop Node** - 事件驱动节点
- **Shared Memory** - 共享状态
- **Event Bus** - 发布/订阅通信

### AIOS 对比

#### AIOS 优势
1. **已有 Self-Improving Loop** - 类似 Hive 的 Adaptiveness
2. **已有 Coder Agent** - 可以生成和修改代码
3. **已有 Task Queue** - 任务调度系统
4. **已有 Learning Agents** - 持续学习机制

#### AIOS 缺口
1. **没有 Goal-Driven Generation** - Agent 是手写的，不是生成的
2. **没有 Dynamic Graph** - Agent 之间的连接是固定的
3. **没有 Judge 机制** - 没有自动评估 Agent 输出是否符合目标
4. **没有 Event Bus** - Agent 之间通信依赖文件，不是事件驱动
5. **没有 WebSocket 实时观测** - Dashboard 是轮询刷新，不是实时推送

### 可执行改进建议

#### P0 - 立刻可做
1. **增加 Judge 机制**
   - 在 `aios/agent_system/` 中增加 `judge.py`
   - 定义评估标准（Criteria）
   - 在 Agent 执行后自动评估输出
   - 不符合标准时触发重试或演进

#### P1 - 近期可做
2. **引入 Event Bus**
   - 在 `aios/agent_system/` 中增加 `event_bus.py`
   - Agent 发布事件到 Bus
   - 其他 Agent 订阅感兴趣的事件
   - 减少文件 I/O，提高响应速度

3. **增强 Dashboard 实时性**
   - 用 WebSocket 替代轮询
   - Agent 执行时实时推送状态更新
   - 用户可以实时看到 Agent 在做什么

#### P2 - 长期可做
4. **引入 Goal-Driven Generation**
   - 让 Coder Agent 根据用户目标自动生成新 Agent
   - 生成 Agent 的 system prompt、工具列表、连接代码
   - 自动测试生成的 Agent

5. **引入 Dynamic Graph**
   - Agent 之间的连接不再固定
   - 根据任务动态生成连接
   - 更灵活的协作模式

---

## 总结：今日最值得做的 3 件事

### 1. 引入 Hands 概念（来自 OpenFang）
**为什么：** 这是 AIOS 从"被动助手"到"主动伙伴"的关键一步

**怎么做：**
- 在 `learning_agents.py` 中标记哪些 Agent 是 Hands
- 修改 heartbeat，让 Hands 主动运行
- 让 GitHub_Researcher 每天自动学习，不等你问

**预期效果：**
- AIOS 变成真正会主动工作的系统
- 你早上醒来，AIOS 已经学完今天的 GitHub 项目
- 你不需要每次都说"去学习"

### 2. 增加 Judge 机制（来自 Hive）
**为什么：** 现在 AIOS 不知道自己做得好不好，需要自动评估

**怎么做：**
- 创建 `judge.py`
- 定义评估标准（任务是否完成、输出是否符合要求）
- 在 Agent 执行后自动评估
- 不合格时触发重试或改进

**预期效果：**
- AIOS 知道自己做得好不好
- 失败时自动重试或改进
- 减少人工检查

### 3. 增加操作审计链（来自 OpenFang）
**为什么：** 现在 AIOS 的日志可以被篡改，需要防篡改机制

**怎么做：**
- 在 `events.jsonl` 中增加前一个操作的哈希
- 每个操作记录时计算哈希
- 验证时检查链是否完整

**预期效果：**
- 操作记录不可篡改
- 可以追溯所有历史操作
- 增强系统可信度

---

## 下一步行动

1. **今天下午：** 实现 Hands 概念（预计 2-3 小时）
2. **明天：** 实现 Judge 机制（预计 3-4 小时）
3. **后天：** 实现审计链（预计 2-3 小时）

**一周后，AIOS 将具备：**
- 主动工作的 Hands
- 自动评估的 Judge
- 防篡改的审计链

**这三个改进都是 P0 级别，直接增强 AIOS 的核心能力。**

---

## 附录：项目链接

- OpenFang: https://github.com/RightNow-AI/openfang
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- Hive: https://github.com/aden-hive/hive
