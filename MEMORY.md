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

**下一步：** 编写 Skill 自动创建 MVP 规格书

---

## 13. 最终提醒

AIOS 的主线不是"做更多"，而是"做得更稳、更真、更能长期运行"。

所有学习、设计、开发、讨论，都应服务于这个目标。
