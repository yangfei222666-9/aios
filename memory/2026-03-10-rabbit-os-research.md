# Rabbit OS / r1 研究报告（2026-03-10）

## 研究聚焦

按珊瑚海指定的 3 个方向 + 4 个问题展开。

---

## 一、Rabbit 产品体系全景

Rabbit 目前有三层 Agent 能力：

1. **Teach Mode**（可教化 Agent）- 用户录制操作 → 生成 lesson → 可回放/复用
2. **LAM Playground**（零教学 Agent）- 直接用自然语言指挥 Agent 操作网页，无需预先教学
3. **rabbit intern**（通用 Agent）- 复杂任务执行（研究报告、网站生成、演示文稿等）

三者关系：
- Teach Mode = 结构化、高可靠、需要预先教学
- LAM Playground = 灵活、零准备、但容易出错
- rabbit intern = 重型任务、长时间运行、输出文件/网页

**rabbitOS 2**（2025-09 发布）把这三者统一在一个卡片式 UI 下，加上 **creations**（用户通过对话生成设备上的工具/游戏/体验）。

---

## 二、回答 4 个核心问题

### Q1: Teach Mode 的最小对象是什么？

**答：Lesson（课程/教程）。**

不是 Skill，不是 Agent，而是 **lesson**。

一个 lesson 的结构：
- **lesson name** - 标题/标签（用户自定义，如 "RunWayML: Short video"）
- **task description** - 1-2 句话描述目标（如 "send a tweet with [text]"）
- **recording** - 用户在虚拟浏览器中的操作录制（点击、输入、回车）
- **parameters** - 从 task description 中提取的变量（用 [] 或 "" 标记）
- **annotations** - 可选的每步附加说明（additional_explanation）
- **read mode markers** - 标记需要 r1 朗读的页面元素

关键特征：
- 一个 lesson 绑定一个网站（不能跨网站）
- 只支持三种操作：点击、输入、回车
- 处理后不可修改 task description（要改只能重新录）
- 支持参数化（变量替换），回放时可以换内容
- 支持 skip/repeat 步骤，但不能执行未教过的动作

**对太极OS的映射：**
lesson ≈ 一个最小可执行的 Skill 实例，但比 Skill 更轻量——它不是代码，而是"操作录像 + 参数模板"。

### Q2: "录一次→以后复用"这条链怎么管理版本和边界？

**答：极简管理，几乎没有版本控制。**

当前 Rabbit 的 lesson 管理：
- **创建后不可编辑** - 处理后的 lesson 不能修改 task description，不能重新录制
- **要改只能重建** - 如果出错，必须创建新 lesson
- **没有版本号** - 没有 v1/v2 的概念
- **没有 diff/changelog** - 无法看到两个 lesson 之间的差异
- **删除是唯一的"版本管理"** - 删掉旧的，录新的

边界管理：
- **单网站约束** - 一个 lesson 只能在一个网站上操作
- **操作类型约束** - 只支持点击、输入、回车（不支持拖拽、右键、快捷键等）
- **不能处理未见过的弹窗/新步骤** - 遇到新情况会失败
- **登录状态通过 cookie jar 管理** - 与 lesson 解耦

社区 lesson：
- 可以浏览社区 lesson → 保存到自己的列表 → 回放
- 但没有 fork/merge 机制
- 没有评分/排名系统（只有回放后的 thumbs up/down）

**对太极OS的启示：**
Rabbit 在版本管理上非常原始。这恰恰是太极OS可以超越的地方——我们的 Skill 系统天然支持文件版本、git 追踪、draft registry。但 Rabbit 的"不可编辑 → 只能重建"策略也有道理：对于录制型 lesson，部分修改很容易破坏一致性。

### Q3: 它怎么把复杂 agent 能力包装成普通用户能理解的入口？

**答：三层入口 + 卡片式 UI + 语音触发。**

**入口设计：**

1. **语音入口（r1 硬件）**
   - 按住按钮说话 → "replay teach mode lesson to send a tweet about..."
   - 关键词触发："teach mode" + lesson 名称/描述中的词
   - 极低门槛：不需要知道技术细节，说出意图即可

2. **rabbithole 网页入口**
   - 卡片式导航：teach mode / LAM playground / intern / creations
   - 每个功能一张卡片，滑动切换
   - 视觉化操作过程（可以实时观看 Agent 在虚拟浏览器中操作）

3. **creations 入口（rabbitOS 2 新增）**
   - 用户通过对话描述想要的工具/游戏 → intern 生成 → 直接安装到设备
   - 类似"vibe coding"但面向非技术用户
   - 有一个类 app store 的 creations 列表

**包装策略的核心：**
- **隐藏技术复杂度** - 用户看到的是"录制→回放"，不是"训练模型→部署 Agent"
- **可视化执行过程** - 回放时可以看到虚拟浏览器中的操作，建立信任
- **失败可见** - thumbs up/down 反馈，不是黑盒
- **渐进式复杂度** - 简单任务用语音触发，复杂任务用 rabbithole 网页

**对太极OS的启示：**
太极OS 目前的入口是 Telegram 聊天 + Dashboard。缺少的是：
- 一个"我能做什么"的可视化能力目录
- 一个"看 Agent 在干什么"的实时执行视图
- 一个"教 Agent 新能力"的低门槛入口

### Q4: 哪些机制适合太极OS吸收，哪些只是硬件产品语境下才成立？

**适合吸收：**

1. **Lesson 的参数化模板思路**
   - task description 中用 [text] 标记变量 → 回放时替换
   - 太极OS 的 Skill 可以借鉴：从重复模式中提取"操作模板 + 参数槽"

2. **Teach Mode vs LAM Playground 的双轨设计**
   - 结构化（高可靠）vs 即兴（灵活但易错）
   - 太极OS 可以同时支持：预定义 Skill（结构化）+ 自然语言即时执行（灵活）

3. **社区 lesson 的共享/保存机制**
   - 浏览 → 保存 → 回放 → 反馈
   - 太极OS 的 Skill 系统未来可以有类似的"Skill 市场"

4. **可视化执行过程**
   - 用户可以实时看到 Agent 在做什么
   - 太极OS 的 Dashboard 可以增加实时执行视图

5. **annotations / additional_explanation**
   - 每个操作步骤可以附加说明
   - 太极OS 的 Skill 可以在每个步骤加注释，帮助 Agent 理解上下文

6. **cookie jar（凭证管理与 lesson 解耦）**
   - 登录状态独立管理，不嵌入 lesson 本身
   - 太极OS 的 Skill 也应该把凭证/环境配置与 Skill 逻辑分离

**只在硬件语境下成立：**

1. **物理按钮触发** - r1 的侧键按住说话，太极OS 不需要
2. **卡片式 UI / 滚轮导航** - 针对 2.88 英寸小屏设计，太极OS 不适用
3. **设备绑定** - r1 必须在线才能用 teach mode，这是硬件限制
4. **单网站约束** - 因为是云端虚拟浏览器，太极OS 在本地可以跨应用
5. **只支持点击/输入/回车** - 硬件 Agent 的操作受限，太极OS 可以调用任意 CLI/API
6. **creations 安装到设备** - 针对 r1 硬件的 app 分发，太极OS 用 Skill 注册

---

## 三、太极OS 的 3 条输出

### 1. 架构启发

**"双轨 Agent + 参数化 Lesson" 架构**

Rabbit 最聪明的设计不是 Teach Mode 本身，而是 **Teach Mode 和 LAM Playground 的共存**：
- Teach Mode = 高可靠、可复用、需要预先投入
- LAM Playground = 零准备、灵活、但不稳定

这两者不是竞争关系，而是互补关系。用户先用 LAM Playground 探索，发现某个任务经常做，就用 Teach Mode 固化成 lesson。

太极OS 可以建立类似的双轨：
- **Skill（结构化轨道）** = 预定义的、经过验证的、可靠的能力
- **即时执行（灵活轨道）** = 自然语言直接指挥 Agent 做事，不需要预定义 Skill

关键：两条轨道之间要有**升级通道**——当一个即时执行的模式被重复 N 次，自动提议将其固化为 Skill。这就是 Skill Auto-Creation MVP 的核心价值。

### 2. 与太极OS的差距判断

**太极OS 在"能力固化"上领先，在"入口可达性"上落后。**

领先的地方：
- 太极OS 的 Skill 系统比 Rabbit 的 lesson 更强大（支持代码、CLI、API、多步骤、条件分支）
- 太极OS 有版本管理（git）、draft registry、验证流程
- 太极OS 的 Agent 可以跨应用操作，不限于单个网站
- 太极OS 有 Learning Loop、Memory 系统、Evolution Score

落后的地方：
- **没有"教 Agent"的低门槛入口** - 用户不能通过"录制操作"来创建 Skill
- **没有"看 Agent 在干什么"的实时视图** - Dashboard 只有统计，没有执行过程
- **没有"我能做什么"的能力目录** - 用户不知道系统有哪些 Skill 可用
- **没有社区共享机制** - Skill 只在本地，不能分享给别人

核心差距：**太极OS 的能力很强，但普通用户感知不到这些能力。**

### 3. 可执行改进建议

**在 Skill Auto-Creation MVP 中增加 "Skill Discovery UI" 最小原型。**

具体做法：
1. 在 Dashboard 中增加一个 "能力目录" 页面
   - 列出所有已注册的 Skill（名称、描述、触发条件、使用次数）
   - 标记 draft / active / deprecated 状态
   - 支持搜索和分类

2. 在每个 Skill 卡片上显示：
   - 最近一次执行时间和结果
   - 成功率
   - 触发方式（自然语言示例）

3. 这不是大工程，而是把已有的 Skill 注册信息可视化

**为什么这是最高优先级的改进：**
- Rabbit 的成功不在于 Teach Mode 技术多先进，而在于用户能**看到**自己教出来的 Agent
- 太极OS 的 Skill 系统已经比 Rabbit 的 lesson 强大得多，但用户看不到
- 可视化 = 可信任 = 会使用 = 会反馈 = 会改进

**不做的事：**
- 不做"录制操作"功能（太极OS 是 CLI/API 驱动，不是浏览器录制）
- 不做硬件入口
- 不做 creations（vibe coding 不是当前优先级）

---

## 四、额外洞察

### Rabbit 的 LAM 演进路径值得关注

Rabbit 的 Agent 技术经历了三个阶段：
1. **LAM 1.0**（2024-01）- 大型动作模型，概念阶段
2. **Teach Mode**（2024-11）- 用户教学 → Agent 回放
3. **LAM Playground**（2024-10）- VLM 驱动的零教学 Agent
4. **DLAM**（2026-01）- Desktop LAM，r1 变成电脑控制器

这条路径的启示：**从"教会 Agent"到"Agent 自己学会"是必然方向。** Teach Mode 是过渡态，LAM Playground / DLAM 才是终态。但 Teach Mode 积累的 lesson 数据是训练更好 Agent 的燃料。

太极OS 的 Skill Auto-Creation 走的正是这条路：从手动创建 Skill → 自动检测候选 → Agent 主动创建 → 最终 Agent 自己学会。

### "creations" 概念的深层含义

rabbitOS 2 的 creations 不只是"生成小工具"，它代表了一个重要转变：**OS 不再是预装功能的集合，而是用户按需生成能力的平台。**

这和太极OS 的 Skill 自动创建方向高度一致。区别在于：
- Rabbit 的 creations 是用户主动要求生成的（"帮我做一个计算器"）
- 太极OS 的方向是系统自动检测重复模式并提议生成

两者可以融合：用户主动请求 + 系统自动检测 = 完整的能力生成闭环。
