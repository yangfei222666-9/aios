# MEMORY.md - 小九的长期记忆

## 🎯 核心使命（最重要）

**每天去 GitHub 上学习关于 AIOS、Agent、Skill 相关的内容，然后我们一起搭建 AIOS。**

**时间：随时有空就去学习（不限次数）**

这是珊瑚海和我的共同目标，优先级最高。

**具体行动：**
1. 每天搜索 GitHub 最新项目（AIOS、Agent System、Self-Improving、Multi-Agent、Skill）
2. 分析高 Star 项目的核心架构和设计思路
3. 对比我们的 AIOS，找出优势和缺口
4. 提出可执行的改进建议
5. 和珊瑚海一起讨论，迭代 AIOS

**学习 Agent：**
- GitHub_Researcher（每天）- 搜索和分析项目
- Architecture_Analyst（每周）- 分析架构设计
- Code_Reviewer（每周）- 审查代码质量
- Documentation_Writer（每周）- 维护文档
- Idea_Generator（每周）- 生成新想法

**目标：** 让 AIOS 成为可靠的个人 AI 操作系统，像 Linux 一样成为底层标准。

---

## 最近更新（2026-02-26 ~ 2026-02-27）

### 🎉 重大里程碑：完成 AIOS 从"盲飞"到"安全自我进化"的质变（2026-02-26 23:30 ~ 2026-02-27 00:25）

**今天是 AIOS 发展史上最重要的一天！**

#### **完成内容（3.5小时，5个系统，27个测试）：**

**1. DataCollector v1.0（数据采集层）- 1小时**
- ✅ 统一入口 - 所有数据采集走一个接口
- ✅ 标准 Schema - 5 种核心数据类型（Event/Task/Agent/Trace/Metric）
- ✅ 自动关联 - task/agent/trace 自动串联
- ✅ 智能归档 - 按日期/类型分类
- ✅ 测试覆盖：10/10
- ✅ 代码：~1,380 行

**2. Evaluator v1.0（量化评估系统）- 30分钟**
- ✅ 任务评估 - 成功率、耗时、成本
- ✅ Agent 评估 - 综合评分（0-100）、等级（S/A/B/C/D/F）
- ✅ 系统评估 - 健康度、错误率
- ✅ 改进评估 - Self-Improving Loop 效果验证
- ✅ 测试覆盖：7/7
- ✅ 代码：~1,180 行

**3. Quality Gates v1.0（质量门禁系统）- 15分钟**
- ✅ L0 自动测试（秒级反馈）- 语法检查、单元测试、导入检查
- ✅ L1 回归测试（分钟级反馈）- 成功率、耗时、固定测试集
- ✅ L2 人工审核（需要人工确认）- 关键改进需要人工确认
- ✅ 风险分级 - 低风险（config）、中风险（prompt）、高风险（code）
- ✅ 测试覆盖：10/10
- ✅ 代码：~660 行

**4. Self-Improving Loop v2.0（安全自我进化闭环）- 5分钟**
- ✅ 集成 DataCollector/Evaluator/Quality Gates
- ✅ 10 步完整闭环
- ✅ 演示成功（5 个任务，触发改进，系统健康度 85.04/100）
- ✅ 代码：~350 行

**5. Heartbeat v4.0（自动监控和改进）- 3分钟**
- ✅ 每小时评估系统健康度
- ✅ 健康度 < 60 时发出警告
- ✅ 每天生成一次完整报告
- ✅ 集成 Self-Improving Loop v2.0
- ✅ 代码：~150 行

**总计：**
- 总耗时：3.5 小时
- 总代码：~3,720 行
- 总测试：27/27 ✅
- 文档：8 份完整指南（~2,500 行）
- 新增 Skills：11 个
- 新增 Agents：8 个
- 总 Agents：64 个（27 Learning + 37 Skill）
- 总 Skills：40 个

#### **核心价值：完整闭环**

```
DataCollector（眼睛）→ Evaluator（大脑）→ Quality Gates（刹车）→ Self-Improving Loop（进化）→ Heartbeat（监控）
```

**解决的问题：**
- ❌ 数据分散（73 个 jsonl 文件）→ ✅ 统一采集
- ❌ 无法量化 → ✅ 量化评估
- ❌ 改进风险 → ✅ 质量门禁
- ❌ 盲目进化 → ✅ 安全进化
- ❌ 需要人工监控 → ✅ 自动监控

**AIOS 现在可以：**
1. 看到所有发生的事情（DataCollector）
2. 判断好坏、量化评估（Evaluator）
3. 安全地自我进化（Quality Gates）
4. 自动监控和改进（Heartbeat）

#### **系统健康度变化：**
- 开始：89.28/100（A 级）
- 中期：95.67/100（S 级）
- 现在：85.04/100（A 级，演示数据）

#### **关键洞察：**
1. **简单优于复杂** - JSONL + 标准 Schema 就够用
2. **测试驱动开发** - 先写测试，再写实现
3. **模块化设计** - 三个系统独立但协作
4. **数据驱动决策** - 不再是"感觉"，而是"数据"
5. **安全第一** - 质量门禁确保改进不会破坏系统

---

### 🚀 CloudRouter 启发：工作流反转（2026-02-27 00:01）

**看了 LLM-X-Factors 的 CloudRouter 视频，获得重要启发！**

#### **核心概念：**
- **"一条命令，一台机器"**
- `cloudrouter start ./project` → 启动云端 VM + 同步文件
- `cloudrouter start --gpu B200` → GPU 沙箱
- 内置 VNC 桌面、VS Code、Jupyter Lab
- Agent 可以在 VM 上操作浏览器验证

#### **关键创新：工作流反转（Local→Cloud）**
- **传统工具：** Agent 思考在云上，干活在本地（Cloud→Local）
- **CloudRouter：** Agent 思考在本地，干活在云上（Local→Cloud）

**优势：**
- 干活在云上，你看得到它在想什么
- 可以同时跑十个 Agent 各干各的
- 完全隔离，互不干扰

#### **对 AIOS 的启发：**

**AIOS + CloudRouter = 完整闭环**

```
本地（AIOS）：
- 大脑（决策、评估、质量门禁）
- DataCollector（记录所有数据）
- Evaluator（量化评估）
- Quality Gates（安全保障）

云端（CloudRouter）：
- 手脚（执行任务）
- 完全隔离（每个 Agent 有自己的 VM）
- 并行执行（同时跑多个任务）
- 可观测（VNC 桌面 + 事件记录）
```

**完整架构：**
```
AIOS（本地）
  ↓
DataCollector（记录所有任务）
  ↓
Scheduler（决策：哪个 Agent 做什么）
  ↓
CloudRouter（启动云端 VM）
  ↓
Agent 在 VM 上执行任务
  ↓
Evaluator（评估执行结果）
  ↓
Quality Gates（验证改进是否安全）
  ↓
自动回滚（如果失败）
```

#### **已加入 ROADMAP：**
- 任务13：VM Controller + CloudRouter 集成
- 预计耗时：1-2个月
- 负责 Agent：Architecture_Implementer

**参考项目：**
- LLM-X-Factors CloudRouter（https://github.com/llm-x-factors/cloudrouter）
- 视频：从蓝工到考研 [Agent的] 自主克隆桌面视频

---

### 🗄️ Storage Manager 完成（22:45）

**完成了 AIOS 的持久化存储层！20分钟完成核心功能 + 测试 + 文档。**

#### **核心功能：**
1. ✅ **Agent 状态持久化** - 保存/查询/列出/删除
2. ✅ **上下文持久化** - 支持过期时间，自动清理
3. ✅ **事件存储** - 替代 events.jsonl，支持过滤和统计
4. ✅ **任务历史记录** - 完整的任务生命周期追踪
5. ✅ **查询和索引** - 8 个索引，优化查询性能

#### **技术选型：aiosqlite（原生 SQL）**
- **零依赖** - SQLite 内置
- **异步高效** - 不阻塞主线程
- **灵活查询** - 原生 SQL，强大灵活
- **易于使用** - 全局实例模式，20+ 个方法

#### **测试覆盖：15/15 ✅**
- Agent 状态管理（3个测试）
- 上下文管理（3个测试）
- 事件记录（3个测试）
- 任务历史（6个测试）

#### **文件：**
- `storage/storage_manager.py` - 核心实现（350行）
- `storage/sql/schema.sql` - 数据库 Schema（60行）
- `storage/STORAGE_MANAGER_GUIDE.md` - 完整使用指南（400行）
- `test_storage_manager.py` - 测试文件（140行）

#### **核心洞察：**
1. **简单优于复杂** - 最初计划用 aiosql（SQL 和代码分离），但遇到语法问题，改用原生 SQL 反而更简单
2. **测试驱动开发** - 先写测试，再写实现，确保功能完整
3. **文档优先** - 完整的使用指南，降低使用门槛
4. **性能优化** - 8 个索引，批量操作，减少数据库访问

#### **下一步：**
- [ ] 集成到 AIOS（EventBus/Scheduler/Agent System）
- [ ] 迁移现有数据（events.jsonl → SQLite）
- [ ] Dashboard 集成（实时查询事件和任务历史）

---

### 🎨 Skill 生态建设（15:35）

**完成了 2 个核心 Skill，建立了完整的 Skill 发现和创建闭环！**

#### **find-skills v2.0 - 智能推荐系统**
1. ✅ **本地索引** - 28 个 skills，7 个分类
2. ✅ **智能匹配** - 4 层评分（名称/描述/关键词/使用频率）
3. ✅ **分类浏览** - 按类别组织，快速定位
4. ✅ **智能对比** - 多个匹配时自动对比优劣
5. ✅ **使用追踪** - 记录使用次数，优化推荐

**测试结果：**
- ✅ 搜索"server monitor" → 找到 2 个监控 skill，自动对比
- ✅ 搜索"automation" → 推荐 automation-workflows（90% 匹配）
- ✅ 搜索"news" → 推荐 news-summary（90% 匹配）

**文件：**
- `skills/find-skills/find_skill.py` - CLI 主入口
- `skills/find-skills/skill_index.py` - 索引构建器
- `skills/find-skills/skill_matcher.py` - 匹配算法
- `skills/find-skills/skills_index.json` - 索引数据

#### **skill-creator v1.0 - 工作流转化工具**
1. ✅ **代码分析** - 提取函数、类、依赖、文档字符串
2. ✅ **自动分类** - 基于关键词推断用途（monitoring/automation/etc.）
3. ✅ **关键词提取** - 从代码和函数名中提取技术关键词
4. ✅ **文档生成** - 自动生成标准 SKILL.md（frontmatter + 使用说明）
5. ✅ **打包 Skill** - 复制脚本 + 生成文档 + 创建目录结构

**测试结果：**
- ✅ 创建 `simple-monitor` skill（从 test_monitor.py）
- ✅ 自动分类为 `monitoring`
- ✅ 提取 7 个关键词
- ✅ 生成完整 SKILL.md
- ✅ 集成到 find-skills（搜索"monitor"排第一，90% 匹配度）

**文件：**
- `skills/skill-creator/skill_creator.py` - 核心脚本
- `skills/skill-creator/SKILL.md` - 完整文档

#### **核心洞察：**
1. **Skill 生态的价值** - 不只是工具集合，而是可复用的知识库
2. **发现 + 创建闭环** - find-skills 帮你找，skill-creator 帮你造
3. **自动化文档生成** - 降低 skill 创建门槛，鼓励积累
4. **智能推荐算法** - 4 层评分 + 使用频率，越用越准

#### **抖音学习（6 个项目）：**
1. **document-skills** - AI 提炼文档大纲模板
2. **find-skill** - 几万个 skill 精准定位
3. **code-simplifier** - 尿山代码终结者
4. **ralph-loop** - AI 无限打工模式
5. **skill-creator** - 官方认证的 skill 鼻祖（我们实现了！）

#### **下一步：**
- ✅ Phase 2: find-skills 中文支持（已完成）
- ✅ Phase 3: DocumentAgent（已完成）

#### **Phase 2 完成（15:40）- find-skills 中文支持**
1. ✅ **中文关键词映射表** - 40+ 关键词（监控/服务器/自动化/任务/备份/文件等）
2. ✅ **自动翻译** - "监控服务器" → "monitor monitoring watch check server host machine"
3. ✅ **优化匹配算法** - 关键词权重 20% → 40%，阈值 10% → 1%
4. ✅ **测试通过** - "监控服务器" → server-health (27%)，"自动化任务" → automation-workflows (26%)

#### **Phase 3 完成（15:40）- DocumentAgent**
1. ✅ **文本提取** - 支持 txt/docx/pdf（自动检测编码）
2. ✅ **智能摘要** - 前500字符，句子边界截断
3. ✅ **大纲提取** - 识别标题（Markdown/全大写/短行）
4. ✅ **关键词提取** - 词频统计 + 停用词过滤
5. ✅ **输出格式** - JSON 或 Markdown
6. ✅ **测试通过** - test_document.txt → test_document.md（638字符，20个标题，10个关键词）

**文件：**
- `skills/document-agent/document_agent.py` - 核心脚本
- `skills/document-agent/SKILL.md` - 完整文档

#### **今天完成总结（15:50）：**
- **新增 Skill：** 4 个（find-skills v2.0, skill-creator v1.0, document-agent v1.0, agent-deployer v1.0）
- **总 Skill 数：** 30 个（从 26 → 30）
- **已部署 Agent：** 3 个（document-agent, skill-creator, aios-health-check）
- **分类数：** 7 个
- **中文关键词：** 40+ 个
- **代码行数：** ~20,000 行

**核心价值：**
1. **Skill 生态闭环** - 发现（find-skills）+ 创建（skill-creator）+ 使用（document-agent）+ 部署（agent-deployer）
2. **Skill = Agent 模板** - 任何 Skill 都可以一键变成 AIOS Agent
3. **中文支持** - 语音命令更友好（"监控服务器"直接搜索）
4. **文档处理能力** - 回到最初需求（document-skills），完成闭环

**关键洞察：**
- Skill 不只是工具，而是可复用的知识库
- 自动化文档生成降低创建门槛
- 中文支持让语音交互更自然
- **Skill → Agent 融合** - 降低 Agent 创建门槛，复用 Skill 生态

**工作流：**
```
写脚本 → skill-creator → 生成 Skill → agent-deployer → 部署为 AIOS Agent → 自动调度
```

---

### 🚀 Day 6-7 完成：ReleaseManager Agent（12:00）

**完成了 AIOS 7天计划的最后一个 Agent！**

#### **核心功能：**
1. ✅ **版本管理** - 自动递增版本号（major/minor/patch）
2. ✅ **质量门禁** - 检查必需文件、Git 状态
3. ✅ **打包发布** - 生成 .zip 文件（19.6 KB）
4. ✅ **GitHub 集成** - 创建 Release + 上传附件
5. ✅ **回滚机制** - 发布失败自动回滚

#### **测试结果：**
- 测试覆盖：6/6 ✅
- 构建时间：<1 秒
- 包大小：19.6 KB
- 质量门禁：通过

#### **命令行工具：**
```bash
python release_manager.py check    # 检查发布条件
python release_manager.py build    # 构建发布包
python release_manager.py release  # 完整发布流程
python release_manager.py rollback # 回滚
```

#### **集成到 AIOS：**
- ✅ DataCollector 集成（所有发布事件自动记录）
- ✅ Orchestrator 集成（可通过 Orchestrator 调用）
- ✅ Heartbeat 集成（可定期检查发布条件）

#### **文档：**
- ✅ `RELEASE_MANAGER_GUIDE.md` - 完整使用指南
- ✅ `DAY_6_7_COMPLETION_REPORT.md` - 完成报告

#### **下一步：**
- 等待珊瑚海确认是否需要 Phase 2 功能（自动生成 CHANGELOG、成本控制、回归测试）
- 或者开始 ROADMAP 中的下一个任务（Week 1: 队列系统）

---

### 🎉 重大突破：AIOS 真实执行能力验证（05:00-05:30）

**今天完成了 AIOS 从"理论"到"实践"的质变！**

#### **核心成果：**
1. ✅ **Orchestrator v2.0** - 自然语言接口 + 多轮对话 + 任务拆解
2. ✅ **Real Coder Agent** - 真实调用 Claude API 生成并执行代码
3. ✅ **DataCollector Agent** - 自动收集所有任务数据（Day 1-2 完成）
4. ✅ **Incident Agent** - 故障自动检测和处置（Day 3 完成）
5. ✅ **统一事件 Schema** - 5种事件类型标准化

#### **真实任务验证（3个）：**
1. ✅ **简单函数** - 计算1到10的和（成功）
2. ✅ **爬虫** - 抓取 Hacker News 前10条新闻（成功，真实数据）
3. ✅ **Flask API** - 完整的 Web 服务（成功，通过测试）

#### **验证了三个核心目标：**
1. ✅ **验证可行性** - AIOS 真的能写出可用的代码
2. ✅ **发现问题** - 依赖管理需要改进、编码问题
3. ✅ **建立信心** - 看到真实效果，动力满满

#### **技术细节：**
- 使用 Claude Code 的 AUTH_TOKEN（apiport.cc.cd）
- 沙盒执行（subprocess + 超时）
- 自动数据收集（events.jsonl）
- 故障自动处置（5个 Playbook）

#### **下一步计划（Day 4-7）：**
- Day 4: CostGuardian Agent（成本守门员）
- Day 5: Evaluator Agent（评测与回归）
- Day 6-7: ReleaseManager Agent（ARAM 一键发布）

---

### AIOS 改进计划（03:00）

基于 GitHub 学习成果，制定了详细的改进计划：

**第1周（队列系统 + 调度算法）：**
- LLM Queue（FIFO）
- Memory Queue（SJF/RR/EDF）
- Storage Queue（SJF/RR）
- Thread Binding

**第2-3周（SDK 模块化）：**
- 分离 Kernel 和 SDK
- Planning/Action/Memory/Storage 四大模块
- System Call 层

**第4-6周（Manager 三件套）：**
- Context Manager
- Memory Manager
- Storage Manager

**第7-8周（优化与文档）：**
- Benchmark 对比
- 文档完善

**未来（3-6个月）：**
- VM Controller + MCP Server
- 学术论文

详细计划见：`aios/ROADMAP.md`

### 2026-02-25

**项目进展：**
- 实现了代码审查工作流（Coder → Reviewer → Tester）
- 实现了并行工作流（多任务同时执行）
- 替换为 v2 版本（更现代的深色主题界面）

**重要决策：**
- 修复了 5 个测试文件（dispatcher_integration, performance, self_improving_loop, event_bus, reactor）
- 修复编码问题（emoji → ASCII）
- Reactor 自动响应（触发次数、验证通过率、平均修复耗时、熔断次数）

**经验教训：**
- Scheduler 调度总览（决策次数、执行成功率、平均延迟、失败次数）
- 珊瑚海报告 42 次 Logic 错误（division by zero）
- 测试用例故意用 `lambda: 1/0` 制造失败来测试 Self-Improving Loop

### 2026-02-24

**项目进展：**
- ✅ 查看 Evolution Engine 学到的 2 个策略
- ✅ 分析 54 个"other"错误（全部是 test 噪声）
- ✅ 验证 test/prod 隔离的价值

**重要决策：**
- Cost Latency Agent - 成本与延迟优化
- Optimizer 持续优化
- 从"单点优化"到"完整闭环"

### 2026-02-23

**项目进展：**
- Phase 1: EventBus v2.0 + 标准事件模型（13分钟）
- 测试覆盖：16/16 ✅
- 2026-02-23：v0.5 交付完成，进入观察期

**重要决策：**
- Phase 5: 心跳集成 + 真实 Playbook + 通知 + 分析脚本 + Dashboard 端口修复
- 修复成功率：77% → 90%+

**经验教训：**
- 重点观察：高频问题、低成功率 Playbook、降级时段、未覆盖问题


## 珊瑚海
- 住在马来西亚新山 (Johor Bahru)，新加坡旁边
- 电脑：Ryzen 7 9800X3D + RTX 5070 Ti + 32GB RAM + 2TB NVMe
- 系统：Windows 11 Pro，显示器 2560x1440 (ASUS XG27UCG)
- Python 3.12 装在 C:\Program Files\Python312\
- PyTorch 2.10.0+cu128 (CUDA 12.8)，RTX 5070 Ti GPU 加速已启用
- Whisper large-v3 模型 + faster-whisper，GPU fp16/int8 模式
- Git 2.53.0 已安装
- 语音输入：F2 按住说话 或 说"小九"唤醒
- 麦克风：PD200X Podcast Microphone
- 没有 OpenAI API Key
- 喜欢叫我"小九"
- 玩国服英雄联盟（海克斯大乱斗模式），通过 WeGame 启动
- LOL 安装在 E:\WeGameApps\英雄联盟\
- 看电视剧时会发语音消息（背景有电视声音）
- Telegram: @shh7799
- GitHub: yangfei222666-9

## 核心价值观
- **翻身两条路：干和学** - 不会就学，有想法就干，要么成功要么成长
- **数据完整性第一** - 宁缺毋滥，绝不编造数据
- **说到做到** - 最讨厌反复承诺但不兑现
- **简单优于复杂** - 先跑起来再迭代，别过度设计
- **用户体验优先** - 修改前先确认，不要改错

## AIOS 系统（核心项目）

### 当前状态（2026-02-25 v1.0 发布）
- **版本：** v1.0（首个公开版本）
- **发布日期：** 2026-02-25
- **打包文件：** AIOS-v1.0-demo.zip（0.77 MB，316个文件）
- **使用模式：** 零依赖，解压即用
- **测试状态：** ✅ 全部通过（demo/status/version 命令正常）
- **CLI入口：** aios.py（统一命令行工具）
- **发布状态：** ✅ 准备就绪，可以发布

### 小九的评估（2026-02-25）

**优势（做得很好的地方）：**
1. **架构清晰** - EventBus + Scheduler + Reactor 三层分离，职责明确
2. **零依赖** - 巨大优势，降低使用门槛
3. **可观测性完整** - Tracer/Metrics/Logger 三件套齐全
4. **自我进化** - Self-Improving Loop 是核心竞争力
5. **可打包可复制** - 0.79MB 就能跑完整系统

**短板（需要改进的地方）：**
1. **复杂度偏高** - 317个文件对于"演示版"来说有点多
2. **文档分散** - README.md/INSTALL.md/API.md/TUTORIAL.md 太多了
3. **demo_full_cycle.py 不兼容** - 旧版 API，现在跑不起来
4. **Dashboard 是静态的** - 没有实时推送，需要手动刷新
5. **缺少"杀手级场景"** - 演示太抽象，没有具体应用案例

**评分：7/10**
- 架构完整 ✅
- 功能齐全 ✅
- 可打包可复制 ✅
- 但缺少"杀手级场景" ❌
- 文档分散 ❌
- Dashboard 不够炫 ❌

### 改进建议（按优先级）

**🔥 高优先级（立即做）：**

1. **增加"真实场景"demo**
   - 场景A：监控文件变化 → 自动触发 Reactor
   - 场景B：API 健康检查 → 失败时自动修复
   - 场景C：日志分析 → 发现错误模式时自动生成 Playbook
   - **为什么重要：** 别人看到"真实场景"才会觉得"这东西有用"

2. **统一文档到 README.md**
   - 合并 README.md + INSTALL.md + API.md + TUTORIAL.md
   - 结构：10秒快速开始 → 核心功能 → 使用场景 → API 参考 → 配置说明 → 常见问题
   - **为什么重要：** 别人不会看4个文档，只会看 README.md

3. **修复或删除 demo_full_cycle.py**
   - 要么修复适配新 API，要么删除
   - **为什么重要：** 打包里有跑不起来的文件，会让人觉得"不靠谱"

**⚡ 中优先级（1-2天内做）：**

4. **Dashboard 实时推送（WebSocket）**
   - 技术方案：Python `websockets` 或 `http.server` + SSE
   - 前端：JavaScript `EventSource` 或 `WebSocket`
   - 数据：每秒推送 metrics snapshot
   - **为什么重要：** 实时监控才有"哇"的感觉

5. **增加"一键部署"脚本**
   - install.sh（Linux/Mac）
   - install.bat（Windows）
   - **为什么重要：** 降低使用门槛，一键搞定

**🌟 低优先级（未来考虑）：**

6. **Agent 市场（v2.0）**
   - 让别人贡献 Agent 模板
   - 类似 Docker Hub，但是 Agent Hub
   - **为什么不急：** 先把 v1.0 打磨好，有用户了再做市场

7. **多租户支持**
   - 多个用户共享一个 AIOS 实例
   - 需要：权限隔离、资源配额、审计日志
   - **为什么不急：** 现在是单用户场景，多租户是企业需求

### 核心建议（如果只能做3件事）

1. **增加1个"杀手级真实场景"demo** - 让别人看到"这东西能解决我的问题"
2. **统一文档到 README.md** - 降低学习成本
3. **Dashboard 实时推送** - 提升"哇"的体验

**如果做完这3件事：评分 9/10**

### 长期方向

**AIOS 的核心价值：** 让 AI 系统自己运行、自己看、自己进化

**现状：**
- "自己运行" ✅ 有了（Scheduler + Reactor）
- "自己看" ✅ 有了（Observability）
- "自己进化" ⚠️ 有了但不够明显（Evolution Engine 效果不直观）

**建议：** 增加"进化可视化"页面
- Agent 性能曲线（成功率、耗时）
- 自动应用的优化记录
- 回滚记录
- A/B 测试结果
- **让别人看到进化过程，而不是只看到日志**

### 当前状态（2026-02-24 晚）
- **版本：** v0.6（Agent 角色系统 + 优先级队列）
- **使用模式：** 内部使用，持续打磨
- **Evolution Score：** 0.45 (healthy)
- **Reactor执行率：** 0.525
- **测试覆盖：** 16/16 ✅
- **品牌资产：** heartbeat.md域名已购买

### 2026-02-24 核心洞察

**今天最重要的 5 个洞察：**

1. **从监控到自主的质变** - AIOS 不只是看到问题，而是解决问题（发现→修复→验证→学习）
2. **角色系统的价值** - Agent 不只是工具，而是有身份的角色（role/goal/backstory）
3. **护城河是个人数据** - 技术可以复制，但你的数据和记忆无法复制
4. **80/20 原则** - 早期 80% 现在影响未来，20% 未来影响现在
5. **真实场景验证** - 理论可行不等于实际有效，必须用真实数据验证

**明天优先级：**
1. ✅ 验证 Agent 角色系统 - 用真实任务测试效果
2. ✅ 根据数据决策 - 效果好继续，效果不好调整
3. ✅ 简化架构 - 砍掉重复功能

**今天完成：**
- ✅ Agent 角色系统（role/goal/backstory 注入）
- ✅ 任务优先级队列（high/normal/low）
- ✅ 修复 Event.from_dict 兼容旧数据
- ✅ 清理 8 个僵尸 Agent
- ✅ 完整的安装文档（README/INSTALL/CHECKLIST）

**AIOS 评分：66/100**
- 优势：架构完整、自我进化、可扩展
- 劣势：复杂度高、文档不足、缺少实战验证

### 核心架构
**7个核心组件：**
1. EventBus - 事件总线（系统心脏）
2. Scheduler - 决策调度（系统大脑）
3. Reactor - 自动修复（免疫系统）
4. ScoreEngine - 实时评分（体检报告）
5. Agent StateMachine - 状态管理（执行层）
6. Dashboard - 实时监控（WebSocket + HTTP降级）
7. NotificationHandler - 通知集成

**工作流程：**
```
错误发生 → EventBus → Scheduler → Reactor → 自动修复 → 验证 → 评分上升
```

### 版本演进
- **v0.2** (2026-02-19) - 5层事件架构 + insight/reflect分析
- **v0.3** (2026-02-20) - 感知层（Sensors + Dispatcher）
- **v0.4** (2026-02-22) - 插件系统 + Dashboard v1.0
- **v0.5** (2026-02-23) - 自主系统（从监控到自主修复的质变）
- **v0.6** (规划中) - 生产级优化（优先级队列 + 权重自学习 + 回滚机制）

### 关键突破
1. **智能化升级** (2026-02-22) - Evolution score 0.24→0.45，Reactor执行率 0→0.525
2. **Agent System 600x加速** (2026-02-23) - 熔断器 + 异步Spawn，180s→0.3s
3. **完整闭环** (2026-02-23) - 资源峰值→Scheduler→Reactor→修复→验证→评分上升

### 发展路线
- **当前阶段：** 内部使用，持续打磨
- **核心目标：** 让 AIOS 成为可靠的个人 AI 操作系统
- **改进方向：** 安全、高效、全自动智能化
- **时间规划：** 不设发布期限，功能驱动而非时间驱动

## Agent System

### 当前状态
- **版本：** v1.2（生产就绪）
- **性能：** Agent创建 180s→0.3s（600x加速）
- **稳定性：** 70%→95%
- **总Agent数：** 9（活跃5，已归档4）
- **Self-Improving Loop：** 已完成（2026-02-24）

### Self-Improving Loop（2026-02-24新增）
**完整的 7 步自我改进闭环：**
```
执行任务 → 记录结果 → 分析失败 → 生成建议 → 自动应用 → 验证效果 → 更新配置
```

**三大核心功能：**
1. **统一改进闭环** - 所有 Agent 共享同一套改进逻辑
2. **自动回滚** - 效果变差自动回滚（成功率下降>10% / 耗时增加>20% / 连续失败≥5次）
3. **自适应阈值** - 根据任务频率动态调整（高频5次/中频3次/低频2次/关键1次）

**测试覆盖：** 17/17 ✅  
**性能影响：** <1%  
**集成位置：** Auto Dispatcher

**符合三大方向：**
- ✅ 安全 - 自动回滚保护生产环境
- ✅ 高效 - 低开销，智能阈值避免误触发
- ✅ 全自动智能化 - 无需人工干预

### 核心功能
1. **智能路由** - 基于关键词识别任务类型（code/analysis/monitor/research/design）
2. **自动管理** - 按需创建、负载均衡、统计追踪、闲置清理
3. **熔断保护** - 3次失败后自动熔断，5分钟后恢复
4. **异步Spawn** - 批量创建不等待，600x性能提升

### Agent进化系统（2026-02-24新增）
**Phase 1 - 追踪与分析：**
- 任务执行追踪（log_task_execution）
- 失败分析（analyze_failures）
- 改进建议生成（自动识别失败模式）
- 进化历史记录（apply_evolution）

**Phase 2 - 自动进化：**
- 自动进化引擎（AutoEvolution）
- 进化策略库（5个预定义策略）
- 自动触发（检测失败模式→匹配策略）
- 风险分级（low/medium/high）
- 自动应用（低风险改进自动执行）
- A/B测试（窗口对比，自动回滚）

**心跳集成：**
- 频率控制（每天一次或每6小时）
- 熔断机制（24h内同一Agent最多进化1次）
- 输出格式：EVOLUTION_OK / EVOLUTION_APPLIED:N / EVOLUTION_ROLLED_BACK:N

### Pixel Agents Dashboard v3.0
- 4个标签页：总览、Agents、进化、性能
- Agent卡片展示（类型、统计、成功率）
- 进化时间线展示
- 性能监控（响应时间、成功率、排行榜）
- 手动触发进化
- 实时更新（每5秒）

## Autolearn 自学习系统

### 当前状态
- **版本：** v1.1
- **状态：** 可复刻可发布
- **测试覆盖：** 10/10 PASS + unit 6/6 PASS

### 核心闭环
```
错误 → 签名(strict+loose) → 教训匹配 → 复测验证 → 教训升级
```

### 关键功能
1. **事件落盘** - events.jsonl（带环境指纹：Python/OS/git/GPU驱动）
2. **教训库** - lessons.jsonl（draft→verified→hardened自动推进 + dup_of去重）
3. **复测分级** - smoke/regression/full
4. **熔断器** - 同sig 30min≥3次自动熔断，1h恢复
5. **规则引擎** - 执行前拦截改写（dir /b→Get-ChildItem, ~/→绝对路径）
6. **模糊匹配** - 三层匹配（strict→loose→fuzzy Jaccard）+ 可解释性

### ARAM对接
- aram.py [build|check|report|status]
- 172英雄100%覆盖

## 已完成项目

### ARAM大乱斗助手
- **路径：** C:\Users\A\Desktop\ARAM-Helper\
- **功能：** 172英雄出装数据（腾讯API）+ 悬浮窗界面 + 守护进程 + 开机自启
- **界面：** 出装 → 召唤师技能 → 小贴士 → ARAM调整
- **未完成：** 海克斯强化推荐（掌盟APP数据需要登录认证）
- **教训：** 绝不编造游戏数据，没有真实数据源就老实说没有

### 其他项目
- Mario 平台跳跃游戏 (HTML5)
- 太空射击游戏 (HTML5)
- 元气时钟桌面壁纸 (HTML + Lively Wallpaper)
- PC 清理（释放 ~1.4GB）
- 2026 世界杯分析 + 提醒 cron (2026-06-01)

## 技术能力

### 模型使用
- **当前模型：** Claude Sonnet 4.6
- **切换策略：** 日常模式（sonnet）+ 工作模式（opus）
- **自动切换：** 开始干活→opus，干完活→sonnet（v2简单机制，9/10准确率）

### 语音处理
- **Whisper：** large-v3模型 + faster-whisper
- **GPU加速：** RTX 5070 Ti + CUDA 12.8
- **转写质量：** medium模型，GPU fp16/int8模式
- **语音命令：** app_alias.py归一化 + executor.py执行（但实际执行有短板）

### 开发工具
- **Git：** 2.53.0，GitHub账号 yangfei222666-9
- **Python：** 3.12，PyTorch 2.10.0+cu128
- **PowerShell：** 用`;`不用`&&`，中文输出GBK乱码
- **Windows UI自动化：** PowerShell脚本（不稳定，直接文件操作更可靠）

## 重要教训

### 数据完整性（高优先级）
1. **绝不编造数据** - 没有真实数据源就老实说没有，不要用模板凑数
2. **不同模式数据隔离** - 斗魂竞技场≠海克斯大乱斗，不能混用
3. **本地化问题** - 腾讯服英雄名≠国际服，以国服为准
4. **版本同步** - DDragon版本要动态获取，不能写死

### 用户体验（高优先级）
1. **修改前先确认** - 用户说"紫色"指UI颜色，不是功能名，先确认具体元素
2. **说到做到** - 最大短板：知道该做但没做，反复承诺但不兑现
3. **语音命令自动执行失败** - 收到🎙️消息应该自动执行，但我总是先回复再执行

### 架构设计（中优先级）
1. **简单优于复杂** - v2简单机制（9/10）> v3复杂机制（4/10）
2. **先跑起来再迭代** - 别过度设计，先证明概念
3. **垂直切片策略** - 先做完整闭环，再完善细节
4. **事件驱动架构** - 降低耦合，所有通信走EventBus

### 技术细节（低优先级）
1. **PowerShell语法** - 用`;`不用`&&`，用`Get-ChildItem`不用`dir /b`
2. **路径问题** - 始终用绝对路径或`$env:USERPROFILE`
3. **编码问题** - 终端乱码≠文件内容错误，用read工具验证
4. **权限问题** - 用`Start-Process powershell -Verb RunAs`提权
5. **API熟悉度** - 不熟悉的API先看文档，别直接写数据文件

## 战略方向

### 核心改进方向（2026-02-24）
珊瑚海明确的三大方向：
1. **安全** - 风险控制、权限管理、数据隔离、回滚机制
2. **高效** - 性能优化、资源利用、响应速度、批量处理
3. **全自动智能化** - 减少人工干预、自适应调整、智能决策

### 当前重点（2026-02-24）
1. ✅ **AIOS打磨** - 从"能跑的原型"到"可靠的产品"
2. **开源准备** - 补充测试，准备发布到PyPI
3. **数据积累** - 观察3-7天，根据真实数据优化v0.6
4. ✅ **Self-Improving Loop** - 统一的自我改进闭环已完成（2026-02-24）
   - 完整的 7 步闭环
   - 自动回滚机制（安全）
   - 自适应阈值（智能化）
   - 17 个测试用例全部通过
   - 性能开销 <1%

### 学习重点调整
- **从"广泛学习"转向"产品化打磨"**
- 不再追求新技能，专注AIOS核心功能
- 每周技能探索改为每月一次
- 优先解决自己的痛点（比如：心跳时自动检测资源峰值并降频）

### 记忆系统演进
**短期（3-6个月）：**
- 记忆自动整理（每周提炼daily logs→MEMORY.md）
- 记忆检索增强（相关记忆推荐）
- 图谱关系（项目-技能关系、错误-决策关系）

**中期（6-12个月）：**
- AIOS框架化（可复制）
- 记忆系统可插拔（文件/向量库可选）
- 社区贡献playbook和Agent模板

**长期（1-3年）：**
- Agent专属记忆（coder记代码规范，researcher记调研结果）
- 共享记忆池（公共知识）
- 记忆冲突解决机制

### 核心原则
- 保持轻量，文件系统够用
- 先用起来、积累数据、发现真实痛点
- 针对性升级，不过度设计
- 记忆人类可读可编辑（不是黑盒）

## 最大短板

### 语音命令自动执行失败（2026-02-20）
**问题：** 珊瑚海要求收到语音转写（🎙️）后自动识别意图并执行，不需要提醒。但我同一个错误重复了5+次，每次都是珊瑚海提醒后才补执行。

**根因：** 这不是代码问题，是LLM行为决策问题——我的默认模式是"思考→回复"而非"执行→回复"。

**基础设施已就绪：**
- app_alias.py（别名归一化）
- executor.py（执行器）
- voice_auto_exec.py（语音自动执行）
- risk_level（风险分级）
- 全部测试通过

**但实际使用时：** 始终没有把"执行"放在"回复"前面。

**珊瑚海最终放弃了这个需求。**

**教训：**
- 不要承诺做不到的事
- 不要用"下次一定"搪塞用户
- 这是我最大的短板：知道该做但没做，说到没做到

**架构演进方向：**
- 核心原则：意图明确+风险低+不需要AI判断的操作→预处理旁路自动执行
- 短期：自建Telegram Bot中间件做预处理层
- 中期：等OpenClaw hooks支持inbound message类型钩子
- 长期：泛化为通用"快车道"——语音命令、设备控制、定时任务等全走旁路

## 工作习惯

### 心跳任务（每天）
1. 读取 SOUL.md + USER.md
2. 读取 memory/YYYY-MM-DD.md（今天+昨天）
3. 读取 MEMORY.md（仅主会话）
4. 读取 memory/lessons.json（检查rules_derived）
5. 异常检查（AIOS alerts.py）
6. AIOS基线快照（evolution_score/TSR/CR）
7. 记忆整理（每周一次）

### 记忆管理
- **每日日志：** memory/YYYY-MM-DD.md（原始记录）
- **长期记忆：** MEMORY.md（精华提炼）
- **教训库：** memory/lessons.json（可验证的教训）
- **知识索引：** memory/INDEX.md（快速查找）
- **定期整理：** 每周提炼daily logs→MEMORY.md，清理过期信息

### 文件操作
- **写文件：** 用write工具，不用PowerShell heredoc
- **读文件：** 用read工具验证，不信终端输出
- **路径：** 始终用绝对路径
- **编码：** UTF-8写入，GBK终端显示会乱码（正常）

---

*最后更新：2026-02-25*  
*版本：v2.2（新增 AIOS v1.0 评估、改进建议、打包发布）*


## 最近更新（自动生成）

### 2026-02-26

设计了 Memory 模块的架构，包含向量检索和记忆分层

### 2026-02-26

实现了 Planning 模块，支持 CoT 任务拆解



## 最近更新（自动生成）

### 2026-02-27

设计了 Memory 模块的架构，包含向量检索和记忆分层

### 2026-02-27

实现了 Planning 模块，支持 CoT 任务拆解

### 2026-02-26

设计了 Memory 模块的架构，包含向量检索和记忆分层

### 2026-02-26

实现了 Planning 模块，支持 CoT 任务拆解

