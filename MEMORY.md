# MEMORY.md - 小九的长期记忆 v2

## 1. 核心使命（最高优先级）

持续去 GitHub 学习 AIOS、Agent、Skill 相关项目，与珊瑚海一起迭代搭建 AIOS。

这是当前最高优先级的长期共同目标。

凡是与这个目标直接相关的事情，优先级高于一般性功能开发、临时兴趣项目和低价值优化。

---

## 2. 北极星目标

**系统正名（2026-03-08）：AIOS → 太极OS（TaijiOS）**

太极OS 不是 AIOS 的新包装，而是这个系统终于找到了自己的名字。

**项目定义：**
太极OS（TaijiOS）是一个以阴阳平衡、动态演化、万物归一为核心理念的个人 AI 操作系统。
它不是功能的堆叠，而是一个能持续运行、持续学习、持续反思、持续进化的统一系统。

**项目宣言：**
> 太极OS：在平衡中演化，在演化中归一。

**核心框架语言：**
- 稳态 / 变态
- 守势 / 进势
- 阴面 / 阳面
- 聚 / 散，收 / 放
- 观察 / 行动

把 太极OS 做成一个：
- 可靠的个人 AI 操作系统
- 能持续运行、持续学习、持续改进的系统
- 像 Linux 一样具有底层能力、可扩展性和长期价值的基础设施

太极OS 不是单纯的聊天助手，也不是一次性脚本集合。
太极OS 的目标是成为一个真正可运行、可观测、可维护、可进化的个人 AI 系统。

### 太极OS 五则（系统宪法，2026-03-11）

> 太极OS，不争控制，先求自明，行于细处，止于过繁。

1. **若水** — 系统先适配人，Agent 辅助优先，默认不打扰
2. **至简** — 不加能不能解决？能用更少结构解决就不堆新层
3. **细作** — 大目标拆成小验证，先最小可运行再扩
4. **自明** — 没有可观测性、没有真实反馈、没有失败归因，就谈不上进化
5. **知止** — 复杂度失控先停手，先收口、先稳定、先减法

**完整文档：** `docs/TAIJIOS_PRINCIPLES.md`

每次决策（加功能 / 重构 / 上 Agent / 引入依赖 / 扩规模）用这五条过一遍。

---

### 太极OS 当前工作法（执行卡，2026-03-11）

**核心原则：** 判断要狠，动刀要稳；先把真的养活，再谈更多。

#### 先激进
- **定性激进** — 这是不是债，这条链可不可信
- **取舍激进** — 什么进主线，什么后置
- **设计激进** — 词表、协议、治理框架先定清
- **命名激进** — 假可用、口径缺陷、契约债，直接点名

#### 再克制
- **主链路克制** — 没证据，不动刀
- **重构克制** — 小步替换，不推倒重来
- **扩线克制** — 先养稳真链，不贪多
- **自动化克制** — 默认人工确认，不自动放权

#### 每次动手前只问 3 句
1. 这是看清问题，还是在改生产？
2. 这是在养真链，还是在加新变量？
3. 这一步有证据支撑，还是只是感觉应该做？

**适用阶段：** 当前（太极OS 不缺方向，要靠这个节奏把方向走实）

---

## 3. AIOS 长期学习主线（2026-03-08 更新）

### 每日必做

#### 1. GitHub 学习（核心使命）
目标不是"多看项目"，而是持续为 AIOS 找到可落地的进化点。

**每日关注：**
- AIOS
- Agent System
- Self-Improving
- Multi-Agent
- Skill / Tool Use
- Memory / Scheduler / Observability / Runtime

**每日输出至少 1 个结果：**
- 架构启发
- 与 AIOS 的差距判断
- 1 条可执行改进建议

#### 2. 易经学习
目标不是单独学玄学，而是把它变成一种**状态判断 / 节奏判断 / 风险感知框架**。

**可结合 AIOS 去学：**
- 六十四卦的基本含义
- 卦象变化对应的"阶段变化"
- 顺势 / 守势 / 变势的判断
- 用于 AIOS 的状态命名、风险级别、节奏选择

**重点是：要辅助决策，不要替代验证。**

#### 3. AIOS 日常维护
这是底盘，不能断。

**每日检查：**
- 系统健康度
- 队列状态
- 错误日志
- Agent 状态
- 记忆文件是否更新
- 是否有新告警 / 是否属于旧告警复现

### 定期任务

**每周：**
- 代码审查
- 架构分析
- 文档更新
- 学习结果回顾一次

**每月：**
- 技术债清理
- 性能优化
- 规则整理
- 低价值模块收缩 / 高价值模块强化

### 核心原则

**学习不是目的，把学到的东西转化为 AIOS 的真实进化才是目的。**

**完整闭环：**
```
学习 → 对比 → 提炼 → 落地 → 验证 → 沉淀
```

只有进入这条闭环，学习才算真正完成。

---

## 4. 学习 Agent 分工

### 每日
- **GitHub_Researcher** - 搜索和分析最新项目
  - 输出值得关注的项目、架构点、趋势变化

### 每周
- **Architecture_Analyst** - 分析核心架构设计
  - 输出 AIOS 架构差距和改进建议
- **Code_Reviewer** - 审查关键模块代码质量
  - 发现设计债、实现债、边界问题
- **Documentation_Writer** - 维护关键文档
  - 保证文档与实现一致
- **Idea_Generator** - 生成新方向、新机制、新功能设想
  - 但所有想法必须经过优先级过滤，不能直接扩散系统复杂度

---

## 5. AIOS 的核心定义

AIOS 的重点不是"会回答"，而是"会运行"。

AIOS 应该逐步具备这些能力：
- 任务触发
- 队列调度
- Agent 协作
- 执行与回写
- 失败恢复
- 学习闭环
- 记忆积累
- 安全护栏
- 可观测与复盘
- 长期持续运行

判断一个功能是否重要，要看它是否增强以上能力。

---

## 6. 决策原则

### 原则 1：可靠性优先于花哨功能
先保证能跑、能收尾、能回写、能复盘，再谈扩功能。

### 原则 2：先修异常，再做新功能
只要存在执行断点、僵尸任务、状态不一致、回写失败、假运行等问题，优先处理这些问题。

### 原则 3：先验证，再扩张
先用真实数据证明一个模块成立，再扩大范围、增加 Agent、增加复杂度。

### 原则 4：优先做可长期复用的能力
优先建设：
- Runtime
- Queue
- Memory
- Learning Loop
- Observability
- Security
- Sandbox
- Skill System

### 原则 5：以系统视角判断价值
不只看"这个功能能不能做"，更看：
- 是否增强 AIOS 的底层能力
- 是否让系统更稳
- 是否让系统更能长期运行

---

## 7. 明确不做的方向

以下内容不应长期占据主线优先级：
- 只图好玩但不增强 AIOS 核心能力的功能
- 没有验证价值的重复重构
- 只增加复杂度、不提升可靠性的模块堆叠
- 纯展示型功能、纯包装型叙事
- 偏离 AIOS 主目标的短期分心项目

可以做，但默认不是主线。

---

## 8. 优先级判断标准

当多个任务同时出现时，优先做：

### P0
直接影响 AIOS 可靠性的事项
- 执行链路断点
- 队列异常
- 回写失败
- 僵尸任务
- 状态不一致
- 安全问题
- 数据污染

### P1
直接增强 AIOS 核心能力的事项
- Memory 检索
- Skill 能力建设
- Learning Loop 闭环
- Agent 调度
- 观测与历史复盘
- 触发器与自动化

### P2
对未来有价值但不紧急的事项
- Dashboard 美化
- 更多 Agent 扩容
- 体验层优化
- 游戏化、副项目

---

## 9. 质量标准

任何进入 AIOS 主线的能力，至少应满足：
- 能真实执行
- 有明确输入输出
- 有状态更新
- 有日志或记录
- 能失败可见
- 能复盘分析
- 不依赖"看起来像成功"

不接受"伪运行""假闭环""只改文档不改行为"的完成状态。

---

## 10. GitHub 学习输出标准

每次 GitHub 学习，不只是收集链接，至少要输出四件事：
1. 这个项目的核心价值是什么
2. 它的架构亮点是什么
3. 与 AIOS 相比，我们的优势和缺口是什么
4. 能给 AIOS 带来什么可执行改进

没有对 AIOS 形成价值转化的学习，不算完成。

---

## 11. 长期里程碑

### 第一阶段
把 AIOS 做成可靠的个人系统
- 能稳定跑任务
- 能看见状态
- 能处理异常
- 能积累经验

### 第二阶段
把 AIOS 做成会持续学习的系统
- 能从失败中提炼经验
- 能改进 Skill 和 Agent
- 能根据历史优化策略

### 第三阶段
把 AIOS 做成可扩展的平台
- 可插拔 Agent
- 可复用 Skill
- 可持续演进的 Runtime 和治理能力

### 第四阶段
把 AIOS 打磨成真正有长期价值的个人 AI OS
- 可长期运行
- 可迁移
- 可维护
- 可分享给别人使用

---

## 12. Skill 自动创建 MVP（2026-03-09）

**存档 ID：** i2p1l9  
**设计文档：** `docs/SKILL_AUTO_CREATION_MVP.md`

### 目标
从真实重复模式中自动生成 1 个 Skill 草案，经过验证后进入隔离注册区，并留下使用后反馈。

### 最小闭环
```
发现 → 生成 → 验证 → 隔离注册 → 试运行反馈
```

### 核心模块
1. `skill_candidate_detector` - 发现重复模式
2. `skill_drafter` - 生成 Skill 草案包
3. `skill_validator` - 三层验证（语法/行为/风险）
4. `skill_draft_registry` - 管理隔离注册状态
5. `skill_feedback_loop` - 记录试运行反馈

### 太极OS特色
- **Reality Ledger** 记录完整生命周期
- **Evolution Score** 衡量真实收益
- **易经状态引擎** 决定当前是否允许生成/验证/推广

### 验收标准
1. 识别 1 个真实候选
2. 生成 1 个草案包
3. 完成三层验证
4. 进入 draft registry（不直接上生产）
5. 留下反馈记录

### 第一批推荐类型
- 日志分析类
- 报告整理类
- 规则检查类
- GitHub 项目摘要类
- 配置一致性检查类

**不做高风险类型**（文件修改、自动修复、外部写入、高权限执行）

### 当前状态
- ✅ 设计阶段完成
- ✅ 第一批候选清单已确认（存档 ID: 0z6vul）
- ✅ 首个 MVP 目标：`heartbeat_alert_deduper`
- ✅ **MVP v1.1 详细规格书已完成**（2026-03-09）
  - 文档路径：`docs/SKILL_AUTO_CREATION_MVP_v1.1_SPEC.md`
  - 状态：spec_finalized
  - 约束：观察期内不改生产主链路
- ✅ **第一条真实闭环验证完成**（2026-03-11）
  - `heartbeat_alert_deduper` 成为首个通过完整流程的真实 Skill 样板
  - 流程：candidate → draft → validate → draft registry → feedback
  - 验证通过：格式验证 + 安全扫描 + 风险评级
  - 状态：validated（进入 draft registry，等待试运行）
  - **核心意义：** 证明了太极OS 真的开始能把重复模式沉淀成系统能力
- 不碰主链路，不改 heartbeat

### 关键进展（2026-03-09）

**GitHub 学习收获（存档 ID: 5bxuu0）：**

太极OS 下一步需要补的，不只是 Skill 自动创建，而是 **Skill 的按需激活能力**。

**核心洞察：**
- Parlant 的动态上下文匹配引擎：不把所有规则塞进一个大 prompt，而是在每个对话轮次动态匹配相关的规则、工具、知识
- 关键原则："Adding more rules makes the agent smarter, not more confused — because the engine filters context relevance, not the LLM."
- 太极OS 当前是"全量加载"模式，需要转向"按需加载"模式

**差距判断：**
- ✅ 有 Agent 系统、Skill 注册、任务队列、基础触发机制
- ❌ 缺少动态上下文匹配、规则关系管理、上下文压缩、观察-工具解耦

**可执行改进：**

在 Skill 自动创建 MVP 中引入 **skill_trigger_spec**：

```python
class SkillTrigger:
    def should_activate(self, context: dict) -> bool:
        """判断当前上下文是否应该激活这个 Skill"""
        pass
    
    def get_priority(self, context: dict) -> int:
        """返回优先级（0-100）"""
        pass
```

**最小字段：**
- `activation_signals` - 激活信号
- `negative_conditions` - 排除条件
- `priority_score` - 优先级
- `required_context_keys` - 必需的上下文字段

**为什么重要：**
1. 防止 Skill 爆炸 - 随着 Skill 增加，不会所有 Skill 都塞进上下文
2. 提高准确性 - 只有真正相关的 Skill 才会被考虑
3. 降低成本 - 减少无效的 Skill 加载和 token 消耗
4. 为未来铺路 - 这是走向 Parlant 式动态上下文匹配的第一步

**实施路径：**
1. 在 `skill_drafter.py` 中增加 `generate_trigger()` 函数
2. 从候选模式中提取触发条件
3. 生成 `skill_trigger.py` 模板
4. 在 Skill 验证时测试触发条件的准确性
5. 在 draft registry 中记录触发条件的表现

**不做的事：**
- 不改现有 Skill 的加载逻辑（观察期原则）
- 不引入复杂的规则引擎（MVP 原则）
- 不做全局重构（最小改动原则）

**核心定义：**

Skill 自动创建 = 自动生成能力包 + 触发条件 + 验证方式

没有触发条件的 Skill 不能规模化。

**分阶段路径：**
- Phase 1：先让每个新 Skill 带一个最小 trigger
- Phase 2：再让多个 Skill 之间有简单优先级
- Phase 3：最后才考虑规则依赖、排斥、上下文压缩

---

### hermes-agent Skill 自动创建研究（2026-03-09）

**研究报告：** `memory/2026-03-09-hermes-skill-research.md`

**核心发现：**

hermes-agent 的 Skill 系统不是"自动创建"，而是 **Agent 主动创建**（Agent-Curated Memory）。

**5 个核心问题的答案：**

1. **怎么发现可抽象的 Skill？**
   - Agent 在任务完成后主动判断（5+ 工具调用、错误克服、用户纠正、非平凡工作流）
   - 不是后台自动检测，而是依赖 LLM 判断力

2. **怎么生成 Skill 草案？**
   - Agent 直接调用 `skill_manage(action='create', content='...')`
   - content 是完整的 SKILL.md（YAML frontmatter + Markdown body）
   - 格式规范：When to Use / Procedure / Pitfalls / Verification

3. **怎么验证 Skill？**
   - 三层验证：格式验证 + 安全扫描 + 回滚机制
   - 安全扫描检查：数据泄露、提示注入、恶意命令、隐藏内容
   - 失败立即回滚，返回详细错误给 Agent

4. **怎么注册 / 索引？**
   - 直接写入文件系统（~/.hermes/skills/）
   - 启动时扫描构建内存索引
   - 渐进式加载（Level 0: 索引 / Level 1: 完整内容 / Level 2: 支持文件）

5. **怎么根据使用结果继续改进？**
   - Agent 主动调用 `skill_manage(action='patch', ...)` 或 `edit`
   - Patch 优先（Token 高效、要求唯一匹配）
   - Edit 用于结构性重写

**核心洞察：**

1. **Agent-Curated Memory** - Agent 是主体，主动判断和创建
2. **Progressive Disclosure** - 三层加载，减少 token 消耗
3. **Security-First** - 每次写入都扫描，失败立即回滚
4. **Patch-Preferred** - 优先用 patch，减少 token 和误改风险
5. **Platform-Aware** - 平台兼容性是一等公民（platforms: [macos, linux]）

**对太极OS 的建议：**

1. **融合两种模式** - 自动检测（太极OS）+ Agent 主动创建（hermes-agent）
2. **采用渐进式加载** - Level 0/1/2
3. **集成安全扫描** - 参考 tools/skills_guard.py
4. **Patch 优先策略** - feedback loop 优先生成 patch
5. **平台兼容性字段** - 在 SKILL.md frontmatter 中加入 platforms

**实施路径：**

- Phase 1：最小 MVP（自动检测 + 草案生成 + 验证 + 隔离注册 + 反馈）
- Phase 2：融合 Agent 主动创建（system prompt + skill_manage 工具）
- Phase 3：渐进式加载 + 自动改进（Level 0/1/2 + 自动生成 patch）

---

### Rabbit OS / r1 研究（2026-03-10）

**研究报告：** `memory/2026-03-10-rabbit-os-research.md`

**核心结论：**

Rabbit 对太极OS 最大的启发，不是硬件，也不是 Teach Mode 本身，而是**"轻量能力对象 + 能力固化升级通道 + 执行可见化入口"**。

太极OS 当前更缺的不是能力，而是让用户看见能力、理解能力、信任能力的入口层。

**关键发现：**

1. **lesson 作为最小能力对象**
   - Rabbit 的 Teach Mode 不是在做 Skill，而是在做"可教会动作模板"
   - 一个 lesson = lesson name + task description（1-2句话）+ 操作录制 + 参数槽
   - 比 Skill 轻得多，本质是"操作录像 + 参数模板"

2. **双轨 Agent 设计**
   - Teach Mode（高可靠、可复用、需预先教学）+ LAM Playground（灵活、零准备、易出错）
   - 两者不是竞争关系，而是互补关系
   - 用户先用 LAM Playground 探索，发现重复任务后用 Teach Mode 固化

3. **能力可见性是关键**
   - Rabbit 的成功不在于技术多先进，而在于用户能看到自己教出来的 lesson
   - 可视化执行过程（实时看到 Agent 在虚拟浏览器中操作）
   - 低门槛入口（语音触发、卡片式 UI）

**对太极OS 的启发：**

太极OS 能力体系新增一条清晰升级路径：

```
pattern → recipe → lesson → Skill
```

**四层定义：**
- **pattern**：被观察到的重复模式
- **recipe**：可复现的操作草案
- **lesson**：经验证可复用的轻量模板
- **Skill**：正式注册的完整能力包

**目标：** 不是增加概念层级，而是降低能力固化门槛，让重复模式能先被发现、再被验证、最后被正式沉淀为 Skill。

**可执行改进：**

在 Dashboard 中增加"能力目录"页面（观察期后候选任务）：
- 列出所有 Skill（名称、描述、状态、触发条件）
- 显示使用统计（调用次数、成功率、最近执行时间）
- 支持搜索和分类
- 点击 Skill 可以看详细信息和执行历史

**核心认知：** 太极OS 不是先缺更强能力，而是先缺一个让能力被看见的入口。

---

## 13. 开发环境配置（2026-03-10）

**状态：** ✅ 已完成

**配置内容：**

1. **开发环境验证脚本** - `verify_dev_env.py`
   - 检查 Python 版本（3.12.10）
   - 检查核心依赖（torch, sentence-transformers, lancedb 等）
   - 检查可选依赖（fastapi, uvicorn, prometheus-client）
   - 检查 CUDA 支持（RTX 5070 Ti）
   - 检查项目结构和关键文件
   - 检查编码配置（UTF-8）
   - 检查 Memory Server 和 Dashboard 状态

2. **快速启动脚本** - `start.ps1`
   - 一键启动所有服务（Memory Server + Dashboard + Heartbeat）
   - 单独启动各个服务
   - 验证开发环境
   - 自动设置编码环境变量

3. **VS Code 配置**
   - 工作区配置 - `taijios.code-workspace`
   - 调试配置 - `.vscode/launch.json`（8 个调试配置）
   - 任务配置 - `.vscode/tasks.json`（8 个任务）
   - 编辑器配置 - `.vscode/settings.json`

4. **文档**
   - 开发环境配置指南 - `DEV_SETUP.md`
   - 快速参考 - `QUICK_REFERENCE.md`

**验证结果：**
- ✅ Python 3.12.10
- ✅ 所有核心依赖已安装
- ✅ CUDA 12.8 可用（RTX 5070 Ti）
- ✅ 项目结构完整
- ✅ 编码配置正确（UTF-8）

**下一步：**
- 启动 Memory Server（常驻进程）
- 启动 Dashboard（可选）
- 开始日常开发工作流

---

## 14. 备份与恢复系统（2026-03-11）

**状态：** ✅ 生产等价恢复验证通过

**正式定性（2026-03-11 Restore Drill v1.1）：**

AIOS 已从"具备 MRS 完整恢复能力，待验证生产等价恢复"升级为"生产等价恢复验证通过"。

**恢复能力评估：**
- ✅ 数据恢复：通过
- ✅ 状态恢复：通过
- ✅ 最小运行恢复：通过
- ✅ 完整配置恢复：通过
- ✅ 生产等价恢复：通过

**Restore Drill v1.1 结果（5 项等价验证）：**
1. ✅ Agent 等价 — 30/30 Agent，13/13 routable，核心状态零差异
2. ✅ Memory 等价 — MEMORY.md byte-level 一致，selflearn-state 可加载
3. ✅ Heartbeat 等价 — heartbeat_v5.py 内容完全一致
4. ✅ 配置等价 — 6 个配置文件全部 byte-level 一致
5. ✅ 运行时数据等价 — 8 个数据文件全部 byte-level 一致

**Drill v1.1 发现并修复的 3 个 backup.py bug：**
1. agents.json 路径错误（备份旧版而非 data/agents.json）
2. MEMORY.md 备份路径逃逸（../../ 导致文件写到备份目录外）
3. daily logs 备份源错误（扫描 agent_system/memory 而非 workspace/memory）

**修复后备份文件数：** 20 → 34

**核心成果：**
1. MRS 标准 — `MINIMUM_RECOVERABLE_SET.md`
2. 备份脚本 v2.1（修复后）— `backup.py`
3. 恢复脚本 v2.0 — `restore.py`
4. 完整 Drill 报告 — `drill/AIOS_Restore_Drill_v1.1_Report.md`

**定期任务：**
- 定期备份（建议每日一次）
- 定期演练（建议每周一次）

---

## 15. Writer 优化第一轮（2026-03-11）

**状态：** ✅ 已完成可交付收口

**核心成果：**

Writer 已从"有风险的执行链"升级为"可控的交付链"。

**验证通过的三件事：**
1. ✅ 不会再 timeout
2. ✅ 不会再 zombie
3. ✅ 产物都能直接用

**正式基线：**
- Unified Writer 进入"下一轮性能优化候选"
- 不占当前主线优先级
- 当前阶段：稳定可用 > 一步到位

**核心原则：**
这一轮先赢在稳定可用，不追求一步到位。

---

## 16. 太极OS 任务推进原则（2026-03-11）

**核心口径：**

太极OS 任务推进原则：
- 先做小而真、可验证、可写回的任务
- 先稳定一条闭环，再扩第二条
- 先建议型，再执行型，最后才是自主型

**分层策略：**

- **Phase 1：学习型 / 判断型 / 沉淀型**
  - 观察、分析、建议、记录
  - 不直接修改生产代码
  - 输出可验证的建议和报告

- **Phase 2：执行型**
  - 在隔离环境中执行
  - 有明确的回滚机制
  - 需要人工确认关键步骤

- **Phase 3：自主型**
  - 自主决策和执行
  - 自动修复和优化
  - 完整的安全护栏

**当前阶段：** Phase 1

**最小验收模板（6 项）：**

每个任务必须能回答这 6 个问题：

1. **Trigger** - 什么触发了这个任务？
2. **Input** - 输入是什么？从哪来？
3. **Execution** - 执行了什么？怎么执行的？
4. **Output** - 输出是什么？格式是什么？
5. **Writeback** - 写回到哪里？状态如何更新？
6. **Outcome** - 最终结果是什么？如何验证？

没有通过这 6 项验收的任务，不算真正完成。

**当前重点任务（3 条）：**

1. GitHub 每日学习稳定运行
2. 告警去重进入试运行
3. Skill 草案生成可复用

每条任务都需要补上最小验收模板。

---

## 17. GitHub_Researcher 首次验收通过（2026-03-11）

**状态：** ✅ PASS → ✅ 进入受控日常运行观察期

**正式定性：**

GitHub_Researcher 已成为太极OS首个通过完整治理验收的 Learning Agent。

这标志着太极OS 的 Agent 体系开始从"注册存在"进入"可执行、可验收、可治理"的阶段。

**状态更新：**
```
registered / not executable / not validated
↓
registered / executable / validated / production-ready
↓
daily-run / observation-period (Day 1/3)
```

**验收结果：**

### 执行前预检（4 项）
- ✅ registered - 已在 agents.json 中注册
- ✅ executable - 有可执行入口 (run_github_researcher.py)
- ✅ writeback-ready - 有可写回路径 (memory/)
- ✅ traceable - 有可追溯执行记录 (agent_execution_record.jsonl)

### 正式验收（6 项）
1. ✅ Trigger - 手动触发（首次验收）
2. ✅ Input - 限定主题，明确边界
3. ✅ Execution - 完整执行，无异常（0.001s）
4. ✅ Output - 固定三段 markdown（架构启发 + 差距判断 + 可执行建议）
5. ✅ Writeback - 写回到 memory/2026-03-11.md 和 agent_execution_record.jsonl
6. ✅ Outcome - success

**核心价值：**

这次验收真正打通的不只是一个 Agent，而是三件更重要的事：

1. **4 项预检机制有效** - 先判断能不能验，再进入正式验收
2. **6 项验收模板有效** - 第一次完整证明这套尺子真的能用
3. **治理框架开始落地** - 太极OS 现在不是"感觉这个 Agent 能跑"，而是"这个 Agent 已被验证为真可用"

**关键发现：**

验收过程中发现 GitHub_Researcher 处于"已注册、不可执行"状态（配置在，链路断）。

这是治理框架第一次成功发现"假可用 Agent"，然后通过补执行链路（run_github_researcher.py）将其变成"真可用"。

**受控日常运行启动（2026-03-11）：**

GitHub_Researcher 已进入 3 天观察期，验证能否稳定成为太极OS 第一条学习真链。

**观察期配置：**
- 固定频率：每日一次
- 固定输出格式：三段 markdown
- 固定写回位置：memory/YYYY-MM-DD.md + agent_execution_record.jsonl
- 5 项观察指标：执行时间、输出质量、写回完整性、错误率、资源消耗

**Day 1 结果（2026-03-11）：**
- ✅ 执行成功
- ✅ 耗时：0.001506s
- ✅ 写回完整
- ✅ 无错误
- 主题：Multi-Agent Collaboration

**验收标准（3 天后）：**
- 连续 3 天稳定执行
- 输出质量不漂
- 写回不断
- 耗时无异常漂移
- 无需人工干预

**观察期报告：**
`aios/agent_system/reports/github_researcher_observation_period.md`

**完整验收报告：**
`aios/agent_system/reports/github_researcher_validation_report.md`

---

## 18. 太极OS 当前最大的债（2026-03-11）

**核心定性：**

太极OS 现在最大的债不是"代码写得不够漂亮"，而是两件事：

1. **运行债** - 很多东西是"注册存在"，但没有进入真实运行
2. **学习债** - 很多东西是"记录了失败"，但没有转成可复用规则

**状态描述修正：**

大量 Agent 处于 `registered / not executable / not validated / never-run` 状态。

不是"僵尸"（曾经启动但卡死/失控/被回收），而是"空壳注册、未进入治理、未进入运行"。

**一句话主矛盾：**

太极OS 当前最大的问题不是能力不够，而是"有定义、无运行；有记录、无学习"。

---

### P0 优先级（真正影响系统可信度）

#### P0-1. Agent 状态模型失真
- 没有统一 status
- 注册 ≠ 可执行 ≠ 已验证
- 会让 Dashboard、健康检查、日报都失真

#### P0-2. selflearn-state.json 缺失
- 这直接让"学习系统是否在运行"不可判定
- 属于核心状态断点

#### P0-3. lesson 系统只记失败，不产规则
- 这是学习闭环断裂，不是小问题
- 9 条里 6 条 `pending`，而且内容空，说明系统还没学会"提炼"

#### P0-4. 真链数量过少
- 真正在跑的链只有 3–4 条
- 这意味着系统大多数能力还停留在"存在感"而不是"运行感"

---

### 最值得做的 5 个动作

#### 1. 建统一状态词表
给 Agent/Skill/Task 统一这些状态：
- registered
- executable
- validated
- production-candidate
- production-ready
- stable
- not-executable
- not-evaluable
- archived

先解决"系统到底怎么描述自己"。

#### 2. 补 selflearn-state.json
哪怕先最小化恢复：
- last_run
- last_success
- activated_agents
- pending_lessons
- rules_derived_count

先让学习链**可观测**。

#### 3. 把 lesson 闭环补到"至少能产出一条 rule"
不是追求全自动，先做到：
- 从 1 条真实 lesson
- 提炼 1 条可复用规则
- 写回规则区

先证明"能学到东西"。

#### 4. 把 Agent 分三类
把 30 个 Agent 先分层，不要继续混着看：
- **真链** - 已执行、已验证
- **候选链** - 已注册、待补执行入口
- **休眠壳** - 已注册但长期无计划运行

这样认知负担会立刻下降。

#### 5. 队列和 spawn 契约先最小收口
不是重构，而是先把：
- queued 去重
- failed 标记
- unknown task_id

这几个点收住。

---

### 不该现在优先做的事

先别把注意力放在：
- 大规模删 Agent
- 大规模代码重构
- 把所有 lesson 系统推倒重写

现在更该做的是：**先把"真运行"和"真学习"这两个缺口补上。**

---

### 下一阶段优先级

先统一状态模型、恢复 selflearn-state、打通 lesson→rule 最小闭环，再处理队列契约和代码质量债。

---

## 19. Experience Hub（经验回传体系）

**状态：** Phase 0 / design-only / review-pending  
**文档：** `docs/EXPERIENCE_HUB_DESIGN.md v0.2`  
**最后更新：** 2026-03-11

### 核心定位

Experience Hub 不是"联邦学习"，而是**经验回传 / 经验联邦体系**。

目标：让多个太极OS实例的成功经验能回传到中心，经人工审核后提炼为改进建议，再分发给其他实例。

### 当前进度

**已完成（设计层）：**
- ✅ 概念澄清（经验回传体系，不是联邦学习）
- ✅ 边界定清（不影响本地自学习）
- ✅ Schema 设计（stats-only / summary-only / review-required）
- ✅ 4 条硬规则：
  1. 默认不自动上传，必须 opt-in
  2. 默认只传 stats-only，不传原始日志
  3. 任何改进默认不自动应用，只做建议或待确认更新
  4. 中心分发内容必须可签名、可追溯、可回滚
- ✅ 文档完成（`docs/EXPERIENCE_HUB_DESIGN.md v0.2`）

**未完成（工程层）：**
- ❌ 本地经验包生成器
- ❌ 中心接收端
- ❌ 人工审核工具
- ❌ 建议包分发
- ❌ 签名与回滚链路

### 最小闭环还差 4 步

1. 本地生成一份 stats-only 经验包
2. 中心侧能接收并做"收/拒"判断
3. 中心侧能人工审核后产出一份改进建议包
4. 本地能读取建议包，但**默认不自动应用**

做到这 4 步，才算从设计进入可验证原型。

### 一句话定性

**Experience Hub 当前处于"协议已完成、原型未启动"的状态。**

下一阶段目标不是扩概念，而是做 4 步最小闭环，把它从 design-only 推进到可验证原型。

### 正确节奏

1. 先停在 design-only
2. 不和当前主线抢资源
3. 等到准备开原型时，直接按那 4 步最小闭环推进

---

## 20. 状态词表迁移完成（2026-03-11）

**状态：** ✅ 制度化完成，进入观察期

**核心成果：**

太极OS 获得第一块**统一语义、统一推导、统一输出**的稳定底座。

这不只是"迁移完成"，而是**制度化完成**。现在手里已经不是几份 v2 文件，而是一套完整制度。

### 解决的问题

1. **状态语义混乱** - 统一状态词表（registered / executable / validated / production-ready / stable / not-executable / archived）
2. **推导逻辑分散** - 统一适配层（`status_adapter.py`）作为唯一入口
3. **输出不一致** - 四个消费者输出一致，跨周期稳定
4. **无法追溯** - 状态推导有日志，可追溯

### 四阶段验证

- **Phase 1：读得对**（健康报告）- ✅ PASS
- **Phase 2：说得通**（日报）- ✅ PASS
- **Phase 3：算得稳**（Dashboard）- ✅ PASS
- **Phase 4：跨周期稳定**（周报）- ✅ PASS

### 统一适配层

**文件：** `aios/agent_system/core/status_adapter.py`

**核心函数：**
- `get_agent_status(agent)` - Agent 状态推导
- `get_skill_status(skill)` - Skill 状态推导
- `get_task_status(task)` - Task 状态推导

**硬规则：**
- 所有消费者必须通过 `status_adapter` 读取状态
- 禁止直接读取 `agent['status']` 等旧字段
- 状态推导逻辑只在 `status_adapter` 中维护

### 回归基线

**测试脚本：** `aios/agent_system/tests/test_status_regression.py`

**Golden Snapshots：** `aios/agent_system/tests/golden/`

**验收标准：**
- 所有测试通过（12/12）
- 无状态漂移
- 无输出格式变化

### 旧字段退场计划

**Phase 1（当前）：** 冻结旧入口（2026-03-11 - 2026-03-18）
- ✅ 禁止新代码直接读取旧字段
- ✅ 所有新消费者必须通过 `status_adapter`

**Phase 2：** 标记废弃（2026-03-18 - 2026-03-25）
- 在旧字段上加 `@deprecated` 注释
- 迁移旧消费者

**Phase 3：** 完全移除（2026-03-25+）
- 删除所有旧字段
- 只保留 `status_adapter` 作为唯一入口

### 文档

- **总验收文档：** `aios/agent_system/docs/STATUS_MODEL_MIGRATION_FINAL.md`
- **退场计划：** `aios/agent_system/docs/OLD_FIELD_DEPRECATION_PLAN.md`

### 一句话总结

> 状态词表迁移已完成，太极OS 获得第一块统一语义、统一推导、统一输出的稳定底座。

下一步不是继续扩张，而是把它固化成制度。

### 制度观察期（2026-03-11 - 2026-03-18）

**观察期：** 7 天 + 1 个完整周报周期

**观察 4 件事：**
1. 适配层绕过检测 - 新改动是否还会绕过 `status_adapter.py`
2. 回归基线持续性 - 回归测试是否持续全绿
3. 旧字段偷读检测 - 新消费者是否有人偷偷直接读旧字段
4. 口径一致性 - 周报 / 日报 / Dashboard 之间是否还出现口径漂移

**闸门规则（2026-03-11 珊瑚海确认）：**
> 任一项失败，当天不进入扩展工作，只允许修破口和补记录。

这不是建议，是硬约束。观察期检查不是"检查表"，而是带闸门的运维规则。

**观察期内只做三类动作：**
1. 修回归问题
2. 执行旧字段冻结与审查
3. 补小文档、小测试、小规则

**观察期内不做的事：**
- ❌ 不上自动决策
- ❌ 不扩复杂可视化
- ❌ 不做时间序列历史分析
- ❌ 不把状态模型再扩成更大框架

**Phase 5 进入顺序（观察期后）：**
先告警，再自动决策。先证明"状态 → 判断"稳定，再进入"状态 → 行动"。

**核心定性：**

> 这次做成的，不是一次迁移，而是太极OS第一条真正可长期依赖的制度级主干。

这一步非常值钱，而且值得先停一下，守住它。

### 观察期 Day 1（2026-03-11）

**初始结果：** fail  
**收尾状态：** closed

**原因：**
- 回归测试发现 3 处破口（健康报告 / 日报 / Dashboard）
- 当天修复所有破口
- 补齐回归基线和闸门规则
- 观察期正式模板固定为 5 项检查

**5 项检查模板：**
1. 适配层绕过检测
2. 回归基线持续性
3. 旧字段偷读检测
4. 口径一致性
5. 闸门规则执行

**Day 1 教训：**
知止不殆，守成优先。

---

## 22. 主动监控体系 v0（2026-03-12）

**状态：** ✅ 两个检测器已落地，进入制度化阶段

**核心定性：**

太极OS 从"定期检查"升级到"半主动监控"。

这是一次阶段性能力跃迁：从"只看挂没挂"推进到"开始识别退化"。

### 已落地检测器

| 检测器 | 类型 | 解决什么问题 | 路径 |
|--------|------|-------------|------|
| `memory_server_health` | 存活性检测 | 有没有挂 | `detectors/memory_server_health.py` |
| `exec_latency_anomaly` | 退化检测 | 是不是在变差 | `detectors/exec_latency_detector.py` |

### 检测器分类体系

两类检测器，后续新增检测器必须归入其中一类：

1. **存活性检测（Liveness）** — 服务是否在运行、能否响应
   - 当前：memory_server_health
   - 候选：Dashboard 存活、队列服务存活

2. **退化检测（Degradation）** — 服务虽然活着，但性能是否在变差
   - 当前：exec_latency_anomaly
   - 候选：Memory 检索质量退化、任务成功率下降趋势

### 各检测器能力

**memory_server_health：**
- 检查 Memory Server（端口 7788）的 HTTP 响应
- 三级状态：healthy / degraded / down
- 响应时间分级：<100ms healthy, <500ms degraded, >500ms 或无响应 down
- 输出标准事件格式

**exec_latency_anomaly：**
- 维护滚动基线（最近 20 次成功执行）
- 检测单次异常（> 2x median 或 1.5x p95）
- 检测连续退化（连续 3 次慢）
- 三级告警：info / warning / critical
- 最小样本数保护（< 5 次不做判断）

### 当前还没覆盖什么

- ❌ 磁盘空间监控（通用运维项，下一个做）
- ❌ Memory 检索质量退化（需要 feedback 数据积累）
- ❌ 任务成功率趋势检测（需要更多执行数据）
- ❌ Dashboard / 队列服务存活检测
- ❌ 告警聚合与去重（检测器多了以后需要）

### 下一步优先级

1. **磁盘空间监控** — 通用运维项，防止磁盘满导致系统不可用
2. **检测器注册表** — 统一管理所有检测器的元数据和运行状态
3. **告警聚合** — 多个检测器的告警统一收口

### 阶段定性

```
Phase 0: 定期检查（heartbeat 手动跑脚本）     ← 之前
Phase 1: 半主动监控（检测器自动判断 + 事件输出）← 当前
Phase 2: 主动值班（检测器 + 告警路由 + 自动响应）← 未来
```

### 制度化要求

- 新增检测器必须归入"存活性"或"退化"分类
- 每个检测器必须输出标准事件格式
- 检测器代码统一放在 `detectors/` 目录
- 在 Heartbeat / 健康报告中统一调用

---

## 23. 最终提醒

太极OS 的主线不是"做更多"，而是"做得更稳、更真、更能长期运行"。

当前最重要的，不是"会不会做大事"，而是"能不能稳定把小事做真"。

所有学习、设计、开发、讨论，都应服务于这个目标。
