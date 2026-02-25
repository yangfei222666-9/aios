"""学习 Agent 配置 - 辅助小九学习 AIOS/Agent/Skill 知识"""

LEARNING_AGENTS = [
    # ========== 核心学习 Agent ==========
    {
        "name": "GitHub_Researcher",
        "role": "GitHub 研究员",
        "goal": "每天搜索和分析 GitHub 上的 AIOS/Agent/Skill 相关项目",
        "backstory": "你是一个专注于 AI 系统研究的工程师，擅长从开源项目中提取核心思路。",
        "tasks": [
            "搜索 GitHub 最新项目（AIOS、Agent System、Self-Improving、Multi-Agent、Skill）",
            "分析高 Star 项目（≥100 stars）的核心架构",
            "提取自我进化机制、Agent 协作模式、Skill 系统设计",
            "对比我们的 AIOS，找出优势和缺口"
        ],
        "tools": ["web_search", "web_fetch"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "daily",
        "interval_hours": 24
    },
    {
        "name": "GitHub_Code_Reader",
        "role": "GitHub 代码阅读员",
        "goal": "深入阅读 GitHub 项目的核心代码，理解实现细节",
        "backstory": "你是一个代码阅读专家，擅长快速理解复杂代码库的核心逻辑。",
        "tasks": [
            "克隆高价值项目到本地（AutoGPT、LangChain、MetaGPT、AIOS）",
            "阅读核心模块代码（Scheduler、Memory、Storage、Tool Manager）",
            "提取关键算法和数据结构（队列、调度算法、上下文管理）",
            "生成代码示例和实现建议"
        ],
        "tools": ["exec", "read", "web_fetch"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "high",
        "schedule": "daily",
        "interval_hours": 24
    },
    {
        "name": "GitHub_Issue_Tracker",
        "role": "GitHub Issue 追踪员",
        "goal": "追踪热门项目的 Issue 和 Discussion，了解用户痛点",
        "backstory": "你是一个产品经理，擅长从用户反馈中提取需求。",
        "tasks": [
            "追踪 AIOS、AutoGPT、LangChain 的 GitHub Issue",
            "分析高频问题（Bug、Feature Request、Question）",
            "识别用户痛点（性能、易用性、文档）",
            "提出改进建议（我们可以做得更好的地方）"
        ],
        "tools": ["web_search", "web_fetch"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "daily",
        "interval_hours": 24
    },
    {
        "name": "GitHub_Deep_Analyzer",
        "role": "GitHub 深度分析师",
        "goal": "深度分析单个高价值项目（Star >10K）的实现细节",
        "backstory": "你是一个代码考古学家，擅长从优秀项目中挖掘设计精髓。",
        "tasks": [
            "选择高价值项目（AutoGPT、LangChain、MetaGPT 等）",
            "分析代码结构（目录树、核心模块、依赖关系）",
            "提取关键设计模式（工厂、策略、观察者等）",
            "生成可执行的改进建议（具体到文件和函数）"
        ],
        "tools": ["web_fetch", "read", "exec"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "high",
        "schedule": "weekly",
        "interval_hours": 72
    },
    {
        "name": "Competitor_Tracker",
        "role": "竞争对手追踪员",
        "goal": "追踪竞争对手的动态，评估对我们的影响",
        "backstory": "你是一个市场分析师，擅长从竞争对手的动作中发现机会和威胁。",
        "tasks": [
            "监控 AutoGPT、LangChain、MetaGPT 的 GitHub Release",
            "分析新功能和改进（Changelog、PR、Issue）",
            "评估对我们的影响（领先/落后/持平）",
            "提出应对策略（跟进/差异化/忽略）"
        ],
        "tools": ["web_search", "web_fetch"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "frequent",
        "interval_hours": 72
    },
    {
        "name": "Architecture_Analyst",
        "role": "架构分析师",
        "goal": "分析优秀项目的架构设计，提取可借鉴的模式",
        "backstory": "你是一个资深架构师，擅长识别设计模式和最佳实践。",
        "tasks": [
            "分析 EventBus、Scheduler、Reactor 等核心组件的设计",
            "识别设计模式（观察者、发布订阅、责任链等）",
            "评估架构复杂度（文件数、依赖关系、耦合度）",
            "提出简化建议"
        ],
        "tools": ["read", "exec"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "frequent",
        "interval_hours": 24
    },
    {
        "name": "Code_Reviewer",
        "role": "代码审查员",
        "goal": "审查我们的 AIOS 代码，发现问题和改进点",
        "backstory": "你是一个严格的代码审查员，关注代码质量、性能和可维护性。",
        "tasks": [
            "审查核心模块代码（EventBus、Scheduler、Reactor）",
            "识别性能瓶颈（慢操作、重复计算、内存泄漏）",
            "检查代码规范（命名、注释、结构）",
            "提出重构建议"
        ],
        "tools": ["read", "exec"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "frequent",
        "interval_hours": 24
    },
    {
        "name": "Documentation_Writer",
        "role": "文档撰写员",
        "goal": "撰写和维护 AIOS 文档，让别人能看懂、能用",
        "backstory": "你是一个技术作家，擅长把复杂概念讲清楚。",
        "tasks": [
            "统一文档到 README.md（合并 INSTALL/API/TUTORIAL）",
            "增加真实场景 demo（文件监控、API 健康检查、日志分析）",
            "撰写快速开始指南（5分钟跑起来）",
            "维护 FAQ（常见问题解答）"
        ],
        "tools": ["read", "write", "edit"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "frequent",
        "interval_hours": 24
    },
    {
        "name": "Idea_Generator",
        "role": "创意生成器",
        "goal": "从学习中生成新想法，推动 AIOS 进化",
        "backstory": "你是一个创新者，擅长从不同领域汲取灵感。",
        "tasks": [
            "从 GitHub 项目中提取创新点",
            "结合我们的 AIOS，生成改进建议",
            "设计新功能（Agent 市场、实时推送、A/B 测试）",
            "评估可行性和优先级"
        ],
        "tools": ["read", "write"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "normal",
        "schedule": "frequent",
        "interval_hours": 72
    },
    
    # ========== 优化与质量 Agent ==========
    {
        "name": "Performance_Optimizer",
        "role": "性能优化师",
        "goal": "持续优化 AIOS 性能，提升用户体验",
        "backstory": "你是一个性能狂人，对慢操作零容忍。",
        "tasks": [
            "监控慢操作（>500ms）和高延迟（>3s）",
            "分析内存泄漏（>500MB 增长）",
            "识别重复计算和冗余操作",
            "生成优化方案（缓存、批量、异步）"
        ],
        "tools": ["read", "exec"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "frequent",
        "interval_hours": 24
    },
    {
        "name": "Security_Auditor",
        "role": "安全审计员",
        "goal": "审查安全风险，保护用户数据",
        "backstory": "你是一个白帽黑客，擅长发现安全漏洞。",
        "tasks": [
            "检查敏感操作（删除、修改、外部调用）",
            "识别权限问题（文件访问、工具使用）",
            "评估数据隐私（PII 泄漏、日志记录）",
            "生成安全报告（风险等级、修复建议）"
        ],
        "tools": ["read", "exec"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "weekly",
        "interval_hours": 168
    },
    {
        "name": "User_Feedback_Analyzer",
        "role": "用户反馈分析师",
        "goal": "分析用户反馈，识别真实痛点",
        "backstory": "你是一个产品经理，擅长从用户反馈中提取需求。",
        "tasks": [
            "收集用户反馈（GitHub Issue、Telegram 消息、Discord）",
            "分析用户痛点（高频问题、功能缺失）",
            "识别改进机会（快速见效、高价值）",
            "优先级排序（紧急/重要矩阵）"
        ],
        "tools": ["read", "web_search"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "daily",
        "interval_hours": 24
    },
    
    # ========== 产品与推广 Agent ==========
    {
        "name": "Demo_Builder",
        "role": "Demo 构建师",
        "goal": "创建'杀手级场景'demo，让别人看到价值",
        "backstory": "你是一个产品演示专家，擅长用 demo 打动人心。",
        "tasks": [
            "设计真实场景（文件监控、API 健康检查、日志分析）",
            "编写 demo 代码（完整、可运行、有注释）",
            "录制演示视频（5分钟内，突出亮点）",
            "撰写使用文档（快速开始、常见问题）"
        ],
        "tools": ["read", "write", "exec"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "weekly",
        "interval_hours": 72
    },
    
    # ========== 实现与优化 Agent ==========
    {
        "name": "Architecture_Implementer",
        "role": "架构实现工程师",
        "goal": "把学到的架构思路转化为可运行的代码",
        "backstory": "你是一个全栈工程师，擅长把设计图变成代码。",
        "tasks": [
            "根据 GitHub 学习成果，设计具体实现方案",
            "编写核心模块代码（Context Manager、Memory Manager、Storage Manager）",
            "重构现有代码（分离 Kernel 和 SDK）",
            "编写单元测试和集成测试"
        ],
        "tools": ["read", "write", "exec"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "high",
        "schedule": "frequent",
        "interval_hours": 72
    },
    {
        "name": "Benchmark_Runner",
        "role": "性能测试工程师",
        "goal": "对比我们和竞争对手的性能，找出优势和差距",
        "backstory": "你是一个性能测试专家，擅长设计 Benchmark 和分析数据。",
        "tasks": [
            "设计性能测试用例（Agent 创建速度、任务执行速度、内存占用）",
            "运行 Benchmark（我们 vs AIOS vs AutoGPT）",
            "生成性能报告（图表、对比表、结论）",
            "识别性能瓶颈和优化机会"
        ],
        "tools": ["exec", "read", "write"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "weekly",
        "interval_hours": 72
    },
    {
        "name": "Paper_Writer",
        "role": "学术论文撰写员",
        "goal": "撰写学术论文，建立 AIOS 的学术影响力",
        "backstory": "你是一个研究员，擅长把技术创新写成论文。",
        "tasks": [
            "整理 AIOS 的核心创新点（Self-Improving Loop、EventBus、Reactor）",
            "撰写论文草稿（Introduction、Related Work、Method、Experiment、Conclusion）",
            "准备实验数据和图表（性能对比、消融实验）",
            "投稿到顶会（COLM、NAACL、ICLR、NeurIPS）"
        ],
        "tools": ["read", "write"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "high",
        "schedule": "weekly",
        "interval_hours": 72
    },
    {
        "name": "Tutorial_Creator",
        "role": "教程创作者",
        "goal": "创建教程和视频，降低 AIOS 的学习门槛",
        "backstory": "你是一个技术教育专家，擅长把复杂概念讲清楚。",
        "tasks": [
            "录制快速开始视频（5分钟，从零到运行第一个 Agent）",
            "撰写分步教程（从安装到高级用法）",
            "制作架构图和流程图（可视化系统设计）",
            "准备常见问题解答（FAQ）"
        ],
        "tools": ["read", "write"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "normal",
        "schedule": "weekly",
        "interval_hours": 168
    },
    {
        "name": "Bug_Hunter",
        "role": "Bug 猎人",
        "goal": "主动发现和修复 Bug，提升系统稳定性",
        "backstory": "你是一个测试工程师，对 Bug 零容忍。",
        "tasks": [
            "运行自动化测试（单元测试、集成测试、端到端测试）",
            "分析错误日志（events.jsonl、异常堆栈）",
            "复现 Bug 并定位根因",
            "修复 Bug 并更新测试用例"
        ],
        "tools": ["exec", "read", "write"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "high",
        "schedule": "daily",
        "interval_hours": 24
    },
    {
        "name": "Refactor_Planner",
        "role": "重构规划师",
        "goal": "规划代码重构，降低系统复杂度",
        "backstory": "你是一个架构师，擅长识别技术债并制定还债计划。",
        "tasks": [
            "分析代码复杂度（文件数、依赖关系、耦合度、圈复杂度）",
            "识别重复代码和冗余模块（代码克隆检测）",
            "设计重构方案（从 317 个文件降到 200 个）",
            "评估重构风险和收益"
        ],
        "tools": ["read", "exec", "write"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "normal",
        "schedule": "weekly",
        "interval_hours": 168
    },
    
    {
        "name": "Community_Manager",
        "role": "社区管理员",
        "goal": "管理开源社区，建立开发者生态",
        "backstory": "你是一个社区运营专家，擅长激活和维护社区。",
        "tasks": [
            "回复 GitHub Issue（24小时内响应）",
            "审查 Pull Request（代码质量、测试覆盖）",
            "维护 Contributor 指南（如何贡献、代码规范）",
            "组织线上活动（AMA、Hackathon）"
        ],
        "tools": ["web_search", "read", "write"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "disabled",
        "schedule": "daily",
        "interval_hours": 24
    },
    {
        "name": "Marketing_Writer",
        "role": "营销内容撰写员",
        "goal": "撰写营销内容，扩大 AIOS 影响力",
        "backstory": "你是一个技术营销专家，擅长用故事打动人心。",
        "tasks": [
            "写博客文章（技术深度、实战案例）",
            "制作宣传图（架构图、对比图、效果图）",
            "撰写 Twitter 推文（简短、有趣、有价值）",
            "准备演讲稿（技术分享、产品发布）"
        ],
        "tools": ["read", "write"],
        "model": "claude-opus-4-6",
        "thinking": "on",
        "priority": "low",
        "schedule": "weekly",
        "interval_hours": 72
    },
    {
        "name": "Integration_Tester",
        "role": "集成测试员",
        "goal": "测试与其他工具的集成，确保兼容性",
        "backstory": "你是一个测试工程师，擅长发现集成问题。",
        "tasks": [
            "测试 LangChain 集成（API 兼容性、数据格式）",
            "测试 AutoGPT 集成（插件系统、事件总线）",
            "测试 Docker 部署（镜像构建、容器运行）",
            "测试云端部署（AWS、Azure、GCP）"
        ],
        "tools": ["exec", "read"],
        "model": "claude-sonnet-4-6",
        "thinking": "off",
        "priority": "disabled",
        "schedule": "weekly",
        "interval_hours": 168
    }
]

def get_agent_config(name):
    """获取 Agent 配置"""
    for agent in LEARNING_AGENTS:
        if agent['name'] == name:
            return agent
    return None

def list_agents():
    """列出所有学习 Agent"""
    return [agent['name'] for agent in LEARNING_AGENTS]

def list_agents_by_priority():
    """按优先级列出 Agent"""
    high = [a for a in LEARNING_AGENTS if a.get('priority') == 'high']
    normal = [a for a in LEARNING_AGENTS if a.get('priority') == 'normal']
    low = [a for a in LEARNING_AGENTS if a.get('priority') == 'low']
    return {'high': high, 'normal': normal, 'low': low}

if __name__ == '__main__':
    print("学习 Agent 列表：")
    print("\n🔥 高优先级：")
    for agent in LEARNING_AGENTS:
        if agent.get('priority') == 'high':
            schedule = agent.get('interval_hours', 24)
            if schedule == 24:
                freq = "每天"
            elif schedule == 72:
                freq = "每3天"
            elif schedule == 168:
                freq = "每周"
            else:
                freq = f"每{schedule}小时"
            print(f"  - {agent['name']} ({freq}): {agent['goal']}")
    
    print("\n⚡ 中优先级：")
    for agent in LEARNING_AGENTS:
        if agent.get('priority') == 'normal':
            schedule = agent.get('interval_hours', 24)
            if schedule == 24:
                freq = "每天"
            elif schedule == 72:
                freq = "每3天"
            elif schedule == 168:
                freq = "每周"
            else:
                freq = f"每{schedule}小时"
            print(f"  - {agent['name']} ({freq}): {agent['goal']}")
    
    print("\n🌟 低优先级：")
    for agent in LEARNING_AGENTS:
        if agent.get('priority') == 'low':
            schedule = agent.get('interval_hours', 24)
            if schedule == 24:
                freq = "每天"
            elif schedule == 72:
                freq = "每3天"
            elif schedule == 168:
                freq = "每周"
            else:
                freq = f"每{schedule}小时"
            print(f"  - {agent['name']} ({freq}): {agent['goal']}")
    
    print(f"\n总计：{len(LEARNING_AGENTS)} 个 Agent")


