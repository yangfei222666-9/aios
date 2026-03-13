# GitHub 监控清单 - Weekly Check

> 每周一次，检查关键仓库的更新情况

---

## P0 - 底座（必须监控）

### OpenClaw
- **仓库：** https://github.com/openclaw/openclaw
- **检查内容：** Releases, Changelog, 新工具, 破坏性变更
- **上次检查：** 2026-03-13
- **当前版本：** （待确认）
- **待办：** 首次全面检查，确认当前版本和最近更新

---

## P1 - 核心参考项目

### DeerFlow 2.0 (ByteDance)
- **仓库：** https://github.com/bytedance/deer-flow
- **关注点：** Skills 系统、Memory 机制、Sub-Agent 编排
- **上次检查：** 2026-03-12（调研报告）

### Mem0
- **仓库：** https://github.com/mem0ai/mem0
- **关注点：** 自动记忆提取、三层记忆架构
- **上次检查：** 2026-03-12（调研报告）

### Hive (Aden)
- **仓库：** https://github.com/aden-hive/hive
- **关注点：** 自动进化闭环、失败捕获机制
- **上次检查：** 2026-03-12（调研报告）

### Agents (aiwaves-cn)
- **仓库：** https://github.com/aiwaves-cn/agents
- **关注点：** 符号学习、语言梯度
- **上次检查：** 2026-03-12（调研报告）

---

## P2 - 行业观察

### MetaGPT
- **仓库：** https://github.com/FoundationAgents/MetaGPT
- **关注点：** AFlow 工作流生成

### LangGraph
- **仓库：** https://github.com/langchain-ai/langgraph
- **关注点：** Durable Execution、Checkpoint 机制

### CrewAI
- **仓库：** https://github.com/crewAIInc/crewAI
- **关注点：** Crews + Flows 双模式

---

## 检查流程

1. **每周一** - 运行 GitHub_Researcher Agent（自动化）
2. **检查内容：**
   - 最近 7 天的 commits
   - 新的 Releases
   - Issues 中的重要讨论
   - README/文档的重大变更
3. **输出：** 周报（`memory/YYYY-MM-DD-github-weekly.md`）
4. **行动：** 如有重要更新 → 更新 tech-watch-list.md + 评估对太极OS 的影响

---

**最后更新：** 2026-03-13  
**下次检查：** 2026-03-17（周一）
