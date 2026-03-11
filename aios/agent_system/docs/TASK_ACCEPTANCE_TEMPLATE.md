# 太极OS 最小验收模板 v1.0

**创建时间：** 2026-03-11  
**版本：** v1.0  
**状态：** 生产标准

---

## 核心原则

太极OS 任务推进原则：
- 先做小而真、可验证、可写回的任务
- 先稳定一条闭环，再扩第二条
- 先建议型，再执行型，最后才是自主型

---

## 最小验收模板（6 项）

每个任务必须能回答这 6 个问题：

### 1. Trigger
**什么触发了这个任务？**
- 定时触发？
- 事件触发？
- 手动触发？
- 依赖触发？

### 2. Input
**输入是什么？从哪来？**
- 输入数据的格式
- 输入数据的来源
- 输入数据的验证方式

### 3. Execution
**执行了什么？怎么执行的？**
- 执行的具体步骤
- 使用的工具/模块
- 执行的环境（隔离/生产）

### 4. Output
**输出是什么？格式是什么？**
- 输出数据的格式
- 输出数据的内容
- 输出数据的验证方式

### 5. Writeback
**写回到哪里？状态如何更新？**
- 写回的目标位置
- 状态更新的方式
- 失败时的回滚机制

### 6. Outcome
**最终结果是什么？如何验证？**
- 成功的标准
- 失败的标准
- 验证的方式

---

## 验收标准

**通过标准：**
- 6 项全部有明确答案
- 每项答案可验证
- 有明确的成功/失败判断

**不通过标准：**
- 任何一项答案模糊
- 无法验证执行结果
- 没有明确的成功/失败标准

---

## 当前重点任务验收（3 条）

### 任务 1：GitHub 每日学习稳定运行

#### 1. Trigger
- 定时触发（每日 Heartbeat）
- 手动触发（`python learning_agents.py run GitHub_Researcher`）

#### 2. Input
- 搜索关键词：AIOS, Agent System, Self-Improving, Multi-Agent, Skill, Tool Use, Memory, Scheduler, Observability, Runtime
- 时间范围：最近 7 天
- 数量限制：每次最多 10 个项目

#### 3. Execution
- 调用 GitHub API 搜索
- 提取项目信息（名称、描述、星标、语言、最近更新）
- 生成结构化报告

#### 4. Output
- 格式：Markdown 报告
- 内容：项目列表 + 核心价值 + 架构亮点 + 与太极OS对比 + 可执行改进
- 位置：`memory/YYYY-MM-DD-github-learning.md`

#### 5. Writeback
- 写入 daily log：`memory/YYYY-MM-DD.md`
- 更新 Agent 状态：`data/agents.json` (last_run, tasks_completed)
- 更新学习状态：`memory/selflearn-state.json`

#### 6. Outcome
- 成功：生成完整报告 + 至少 1 条可执行改进建议
- 失败：报告不完整 / 无改进建议 / 写回失败
- 验证：检查文件存在 + 内容完整性 + 状态更新

**当前状态：** ✅ 已通过验收

---

### 任务 2：告警去重进入试运行

#### 1. Trigger
- Heartbeat 检测到新告警
- 手动触发（`python heartbeat_alert_deduper.py`）

#### 2. Input
- 告警源：`data/skill_health.jsonl`
- 历史告警：`data/alert_history.jsonl`
- 去重规则：连续失败次数、错误类型、等级

#### 3. Execution
- 读取当前告警
- 对比历史告警
- 判断是否需要通知
- 生成去重报告

#### 4. Output
- 格式：JSON 报告
- 内容：新告警列表 + 抑制告警列表 + 去重原因
- 位置：`data/alert_dedup_report.jsonl`

#### 5. Writeback
- 更新告警历史：`data/alert_history.jsonl`
- 记录去重决策：`data/alert_dedup_log.jsonl`
- 更新 Skill 状态（如果需要）

#### 6. Outcome
- 成功：正确识别新告警 + 正确抑制旧告警 + 无误报
- 失败：漏报新告警 / 误报旧告警 / 写回失败
- 验证：对比人工判断 + 检查去重逻辑 + 验证写回完整性

**当前状态：** 🔄 进入试运行（观察期 7 天）

---

### 任务 3：Skill 草案生成可复用

#### 1. Trigger
- 手动触发（`python skill_drafter.py --candidate <name>`）
- 未来：自动触发（从 pattern detector 输出）

#### 2. Input
- 候选名称：`heartbeat_alert_deduper`
- 候选描述：从 `data/skill_candidates.jsonl` 读取
- 模式数据：重复执行记录、参数模式、输出格式

#### 3. Execution
- 生成 SKILL.md（frontmatter + body）
- 生成主脚本（Python）
- 生成触发条件（trigger spec）
- 生成测试用例（可选）

#### 4. Output
- 格式：完整 Skill 包（目录结构）
- 内容：SKILL.md + 主脚本 + 触发条件 + README
- 位置：`skills/draft/<skill_name>/`

#### 5. Writeback
- 写入 draft registry：`data/skill_draft_registry.jsonl`
- 记录生成日志：`data/skill_generation_log.jsonl`
- 更新候选状态：`data/skill_candidates.jsonl` (status: drafted)

#### 6. Outcome
- 成功：生成完整 Skill 包 + 通过格式验证 + 通过安全扫描
- 失败：生成不完整 / 格式错误 / 安全风险 / 写回失败
- 验证：三层验证（格式/行为/风险）+ 检查文件完整性 + 验证注册状态

**当前状态：** 🔄 首个样板已完成（`heartbeat_alert_deduper`）

---

## 使用方式

### 新任务验收
1. 复制模板
2. 填写 6 项内容
3. 验证每项答案
4. 确认通过标准

### 现有任务审查
1. 对照模板检查
2. 找出缺失项
3. 补全缺失项
4. 重新验收

### 失败任务分析
1. 检查哪一项失败
2. 分析失败原因
3. 修复失败项
4. 重新验收

---

## 版本历史

- **v1.0** (2026-03-11) - 初始版本，定义 6 项验收标准
