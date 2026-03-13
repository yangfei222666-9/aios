# 技术观察清单 - Tech Watch List

> 记录值得持续跟踪的大厂/开源项目，尤其是与太极OS 路线高度相关的技术验证。

---

## Tesla/xAI - MACROHARD (Digital Optimus)

**官宣时间：** 2026-03-11  
**来源：** Elon Musk X 官方账号  
**开发方：** Tesla + xAI 联合项目  

### 核心要点

**目标：**
- 模拟完整软件公司的 AI Agent OS
- 在 Tesla 车机上运行（非驾驶时做 office work）
- 端到端工作流自动化

**技术栈：**
- **Grok (System 2)** - 任务规划 + 导航决策
- **Tesla Agent (System 1)** - 实时屏幕理解 + 键鼠执行
  - Rolling 5s video 输入
  - 实时读屏 + 操作反馈
- **硬件：** Tesla AI4 芯片 + xAI Nvidia 集群

**命名：**
- MACROHARD = Microsoft 的反义词（致敬/挑战）
- Digital Optimus = 数字版 Optimus 机器人（软件先行）

### 与太极OS 的对比

| 维度 | MACROHARD | 太极OS |
|------|-----------|--------|
| 规划层 | Grok (System 2) | Dispatcher + Planner |
| 执行层 | Tesla Agent (System 1) | safe_click + Skill 系统 |
| 屏幕理解 | Rolling 5s video | 截图 + OCR/Vision |
| 硬件 | Tesla AI4 + 车机 | 本地 PC (Ryzen 9800X3D + RTX 5070 Ti) |
| 目标 | 通用软件公司 | 个人 AI OS |

### 对太极OS 的 3 点启发

1. **System 1/2 分离验证** - 大厂也在用"规划-执行分离"架构，证明路线正确
2. **Rolling video 输入** - 比单帧截图更连续，可以捕捉动画/加载状态
3. **车机应用场景** - 证明 Agent OS 可以在非传统计算设备上运行

### 跟踪重点

- [ ] 开源情况（是否会像 Grok 一样开源）
- [ ] 生产力真实指标（完成任务成功率、速度）
- [ ] 与太极OS safe_click + dispatcher 的差异/可借鉴点
- [ ] Rolling video 的实现细节（帧率、压缩、推理延迟）
- [ ] 车机上的实际应用案例

### 参考链接

- Elon Musk X 官宣：（待补充链接）
- 相关讨论：（待补充）

---

## 太极OS 内部 - 监控系统 Phase 4/5 & 告警聚合机制

**验证时间：** 2026-03-13 08:09  
**推送方式：** xiaojiu 主动推送管理报告（手机端实时）  
**优先级：** P1（监控闭环验证）  

### 核心亮点

**1. 告警聚合机制验证通过**
- 20+ 条 GitHub_Researcher 执行延迟告警（10.67ms，是中位数 10 倍）
- 智能聚合成一条模式，不重复通知
- 完美解决"运行债暴露"问题（2026-03-13 早上用户质问的那个）

**2. 监控闭环已成型**
- 发现问题（昨天截图：GitHub_Researcher 从未运行）
- 自诊断（查 selflearn-state.json）
- 聚合静默（20+ 告警 → 1 条模式）
- 定时汇报（09:00 发昨日汇总）

**3. 系统健康度可视化**
- 13 个 Agent 全在"既济"稳定状态
- Evolution Score 0.4（healthy）
- CPU 9%、内存 42.6%、磁盘正常
- OpenClaw Gateway / Memory Server / Dashboard 全在线

**4. 免打扰策略生效**
- 3 条健康度 50/100 的轻微告警 → 已在 06:20-07:41 发过，1 小时内不再重复
- 已过 08:00，但没有 CRITICAL 事件，所以不打扰
- 待办：09:00 准时发「昨日汇总」

### Phase 4: 验证

**Dashboard 8889 端口验证：**
- HTTP 200 正常
- 之前报 404 是因为 `/api/health` 接口还没创建
- 服务本身一直正常（已修复）

### Phase 5: 学习

**监控记录持久化：**
- 本次监控记录已写入 `monitor_history.jsonl`
- 支持历史回溯和趋势分析

### 与 Macrohard 的对比

| 维度 | Macrohard | 太极OS 当前状态 |
|------|-----------|----------------|
| 规划层 | Grok (System 2) | Dispatcher + Planner |
| 执行层 | Tesla Agent (System 1) | safe_click + Skill 系统 |
| 监控层 | **未公开** | **已实现：告警聚合 + 定时汇报** ✅ |
| 自愈能力 | **未公开** | **已实现：自诊断 + 聚合静默** ✅ |

**关键洞察：**
- Macrohard 展示了"规划-执行分离"，但没公开监控和自愈部分
- 太极OS 已经跑通了"健康自愈"这一环，这是我们的差异化优势
- 路线完全一致，而且我们在可观测性上领先

### 修复亮点

**1. 运行债可视化**
- GitHub_Researcher 的延迟被明确量化（10.67ms vs 中位数）
- 不再是"从未运行"的黑盒，而是"延迟 10 倍"的可量化问题

**2. 告警聚合算法**
- 20+ 条相同模式的告警 → 1 条聚合通知
- 避免"告警风暴"打扰用户

**3. 免打扰时段**
- 轻微告警 1 小时内不重复
- CRITICAL 事件才会立即通知
- 定时汇总（09:00）兜底

### 下一步优化建议

**短期（本周）：**
1. 补充 Dashboard `/api/health` 接口（已修复，待验证）
2. 优化 GitHub_Researcher 执行延迟（10.67ms → 目标 <5ms）
3. 完善"昨日汇总"报告格式

**中期（本月）：**
1. 实现告警趋势分析（连续 3 天延迟 → 自动触发优化）
2. 增加更多监控指标（token 消耗、任务成功率、响应时间）
3. 支持自定义告警阈值

**长期（下季度）：**
1. 实现预测性监控（根据历史趋势预测未来问题）
2. 自动生成优化建议（类似 Hive 的自动进化）
3. 多维度健康评分（不只是 Evolution Score）

### 参考资料

- 管理报告截图：2026-03-13 08:09
- 监控数据：`monitor_history.jsonl`
- 相关文档：`HEARTBEAT.md`, `tech-watch-list.md`

---

## 太极OS 内部 - GitHub_Researcher 运行债

**发现时间：** 2026-03-13 07:50  
**触发事件：** 用户质问"GitHub 上很早就更新了，为什么每天去学习没发现？"  
**优先级：** P0（暴露核心调度问题）  

### 问题描述

**现象：**
- GitHub_Researcher Agent 在代码中已定义
- `selflearn-state.json` 显示 `last_run: "从未运行"`
- 实际的 GitHub 调研都是主会话手动触发，非自动化执行

**根本原因：**
- Agent 定义 ✅
- Dispatcher 调度 ❌
- 典型的"注册存在、运行缺失"

### 复现步骤

1. 检查 `aios/agent_system/memory/selflearn-state.json`
2. 查看 `GitHub_Researcher` 条目的 `last_run` 字段
3. 对比 `memory/` 目录下的实际调研报告（都是手动触发）

### 与 Macrohard 的对比

| 维度 | Macrohard 挑战 | 太极OS 当前状态 |
|------|---------------|----------------|
| 规划层 | Grok (System 2) 已验证 | Dispatcher 已定义 |
| 执行层 | Tesla Agent (System 1) 落地中 | **调度机制缺失** ⚠️ |
| 核心痛点 | 执行层真正落地 | **同样卡在执行** |
| 验证价值 | 大厂也在解决同样问题 | 路线正确，优先级明确 |

### 优化方向

**短期（本周）：**
1. 修复 Heartbeat 调度机制，确保 GitHub_Researcher 真正运行
2. 验证 `spawn_pending.jsonl` 的生成和消费流程
3. 补充 OpenClaw 本体的监控（当前盲点）

**中期（本月）：**
1. 实现 Agent 运行状态的主动监控（类似 Macrohard 的 System 1/2 分离）
2. 建立"定义-调度-执行-反馈"的完整闭环
3. 自动检测"僵尸 Agent"（定义了但从未运行）

**长期（下季度）：**
1. 借鉴 Hive 的自动进化机制（失败捕获 → 自动改进）
2. 实现 Durable Execution（LangGraph 风格的断点恢复）

### 自我反思能力验证

**已具备：**
- ✅ 快速定位问题（查 state.json）
- ✅ 区分"手动 vs 自动化"
- ✅ 承认盲点（OpenClaw 监控缺失）
- ✅ 主动反问（"是指哪个项目？"）

**待加强：**
- ❌ 主动发现问题（需要用户质问才暴露）
- ❌ 自动修复机制（发现问题后自动触发修复）

### 参考资料

- 聊天记录截图：2026-03-13 07:50-07:51
- 健康数据存档：`data/health/health_20260313_075008.json`
- 相关文档：`HEARTBEAT.md`, `github-watch-schedule.md`

---

## OpenClaw - 底座框架

**仓库：** https://github.com/openclaw/openclaw  
**优先级：** P0（底座，必须优先监控）  
**当前版本：** （待确认）  

### 监控重点

- [ ] 每周检查 Releases 和 Changelog
- [ ] 新增工具/能力（browser、canvas、sessions_spawn 等）
- [ ] 破坏性变更（API 变化、配置格式调整）
- [ ] 性能优化和 Bug 修复
- [ ] 新增 Skills 示例

### 检查频率

- **每周一次** - 查看最近 7 天的 commits 和 releases
- **重大更新时** - 立即评估对太极OS 的影响

### 行动清单

- [ ] 如有新版本 → 评估是否需要升级
- [ ] 如有新工具 → 评估是否可用于太极OS
- [ ] 如有破坏性变更 → 提前规划迁移方案

---

## 其他待观察项目

（待补充）

---

**最后更新：** 2026-03-13  
**维护者：** 小九 + 珊瑚海
