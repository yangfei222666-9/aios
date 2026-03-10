# 项目分析报告：DeerFlow / OpenSandbox / IronClaw
**时间：** 2026-03-07 20:55 GMT+8

---

## 1. ByteDance DeerFlow ⭐⭐⭐⭐⭐
**仓库：** https://github.com/bytedance/deer-flow  
**状态：** 2026-02-28 登上 GitHub Trending #1，v2.0 全面重写

### 核心架构
- **基础：** LangGraph + LangChain
- **沙盒：** Docker 容器（本地/Docker/K8s 三种模式）
- **技能系统：** SKILL.md 文件驱动，按需加载（节省 context window）
- **子 Agent：** 主 Agent 动态 spawn，并行执行，结构化汇报
- **记忆：** 跨会话持久化，本地存储用户偏好/知识
- **文件系统：** 每任务独立沙盒容器，/mnt/user-data/{uploads,workspace,outputs}

### 与 AIOS 对比
| 特性 | DeerFlow | AIOS |
|------|----------|------|
| 技能系统 | SKILL.md 按需加载 | ✅ 已有（更完整） |
| 子 Agent | 动态 spawn + 并行 | ✅ sessions_spawn |
| 沙盒 | Docker 容器 | ❌ 缺少隔离 |
| 记忆 | 跨会话持久化 | ✅ LanceDB + MEMORY.md |
| 任务编排 | LangGraph 状态机 | ✅ Heartbeat + TaskQueue |
| 自我改进 | ❌ 无 | ✅ Self-Improving Loop |
| 64卦决策 | ❌ 无 | ✅ 独有 |

### 可借鉴
1. **沙盒隔离** - 每个 Agent 任务跑在独立 Docker 容器，零污染
2. **技能按需加载** - 只在需要时加载 SKILL.md，节省 token
3. **Context Engineering** - 子任务完成后自动摘要，压缩 context
4. **Python 嵌入式客户端** - DeerFlowClient 可直接 in-process 调用，无需 HTTP

---

## 2. Alibaba OpenSandbox ⭐⭐⭐⭐⭐
**状态：** GitHub 上未找到公开仓库（可能是内部项目或名称有误）

**替代参考：** 阿里云的 E2B / Daytona 类沙盒方案
- 可搜索：alibaba/agentscope（已开源，有沙盒执行）
- 或参考 E2B.dev（通用代码沙盒 API）

---

## 3. IronClaw（安全版 OpenClaw）⭐⭐⭐⭐
**仓库：** https://github.com/nearai/ironclaw  
**状态：** 6.5k stars，Rust 实现，NEAR AI 出品

### 核心安全特性
- **WASM 沙盒：** 所有工具在 WebAssembly 容器中运行，capability-based 权限
- **凭证保护：** 密钥在 host 边界注入，永远不暴露给 WASM 代码
- **泄露检测：** 扫描请求/响应中的密钥泄露
- **Prompt Injection 防御：** 模式检测 + 内容净化 + 策略规则
- **端点白名单：** HTTP 请求只允许访问预批准的 host/path
- **AES-256-GCM 加密：** 本地数据全加密

### 架构亮点
```
WASM → Allowlist → Leak Scan → Credential Injector → Execute → Leak Scan → WASM
```

### 与 AIOS 对比
| 特性 | IronClaw | AIOS |
|------|----------|------|
| 凭证保护 | ✅ WASM 边界注入 | ❌ 直接传给 LLM |
| Prompt Injection | ✅ 多层防御 | ❌ 无 |
| 工具沙盒 | ✅ WASM | ❌ 无 |
| 记忆 | PostgreSQL + pgvector | ✅ LanceDB |
| 自我改进 | ❌ 无 | ✅ 独有 |
| 语言 | Rust（性能强） | Python（灵活） |

### 可借鉴
1. **凭证注入模式** - 密钥不传给 LLM，在执行层注入
2. **Prompt Injection 防御** - 外部内容包装 + 策略规则
3. **端点白名单** - 限制 Agent 可访问的 HTTP 端点
4. **泄露检测** - 扫描 LLM 输出中的敏感信息

---

## 综合建议：AIOS 下一步

### 优先级 P0（安全补强）
1. **凭证保护** - 参考 IronClaw，密钥不传给 LLM
2. **Prompt Injection 防御** - 外部内容（Telegram/邮件）先过滤再给 LLM

### 优先级 P1（执行隔离）
3. **Docker 沙盒** - 参考 DeerFlow，Agent 任务跑在独立容器
4. **Context 压缩** - 子任务完成后自动摘要，节省 token

### 优先级 P2（生态扩展）
5. **Python 嵌入式客户端** - 参考 DeerFlow，无需 HTTP 直接调用
6. **技能按需加载** - 只在需要时加载 SKILL.md

---

*分析人：小九 | 来源：GitHub 实时数据*
