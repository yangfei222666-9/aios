# hermes-agent Skill 自动创建机制研究报告

**研究日期：** 2026-03-09  
**研究目标：** 回答 5 个核心问题，为太极OS Skill 自动创建 MVP 提供设计参考

---

## 核心发现

hermes-agent 的 Skill 系统不是"自动创建"，而是 **Agent 主动创建**。

关键区别：
- 不是后台自动检测 → 自动生成
- 而是 Agent 在执行任务后，**主动判断是否值得保存为 Skill**，然后调用 `skill_manage` 工具创建

这是一种 **Agent-Curated Memory（Agent 策展的记忆）** 模式。

---

## 问题 1：它怎么发现可抽象的 Skill？

### 触发条件（写在 skill_manage 工具的 description 中）

```python
"Create when: complex task succeeded (5+ calls), errors overcome, "
"user-corrected approach worked, non-trivial workflow discovered, "
"or user asks you to remember a procedure."
```

**具体场景：**
1. **复杂任务成功**（5+ 工具调用）
2. **错误克服**（遇到错误但找到了解决方案）
3. **用户纠正**（用户纠正了 Agent 的方法，新方法有效）
4. **非平凡工作流**（发现了一个不明显的流程）
5. **用户明确要求**（"记住这个流程"）

### 判断逻辑（在 Agent 的 System Prompt 中）

```python
SKILLS_GUIDANCE = (
    "After completing a complex task (5+ tool calls), fixing a tricky error, "
    "or discovering a non-trivial workflow, consider saving the approach as a "
    "skill with skill_manage so you can reuse it next time."
)
```

**关键点：**
- 不是自动检测，而是 **Agent 自己判断**
- Agent 在任务完成后，根据任务复杂度、是否遇到困难、是否有价值复用，**主动决定是否创建 Skill**
- 这依赖于 LLM 的判断能力

### 太极OS 对比

**hermes-agent：** Agent 主动判断 → 调用 skill_manage  
**太极OS 当前设计：** 后台自动检测重复模式 → 生成候选

**差异分析：**
- hermes-agent 更依赖 LLM 的判断力，更灵活，但可能漏掉一些模式
- 太极OS 的自动检测更机械，但能捕获 Agent 没意识到的重复模式

**可能的融合方案：**
1. **双轨制：** 自动检测 + Agent 主动创建
2. **自动检测 → 提示 Agent：** 检测到重复模式后，不直接生成，而是提示 Agent："你最近做了 3 次类似的任务，要不要保存为 Skill？"

---

## 问题 2：它怎么生成 Skill 草案？

### 生成方式

**Agent 直接调用 `skill_manage(action='create', name='...', content='...')`**

`content` 参数是完整的 SKILL.md 文本，包括：
- YAML frontmatter（name, description, version, platforms, tags, category）
- Markdown body（When to Use, Procedure, Pitfalls, Verification）

### SKILL.md 格式规范

```markdown
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
platforms: [macos, linux]  # Optional — restrict to specific OS platforms
metadata:
  hermes:
    tags: [python, automation]
    category: devops
---

# Skill Title

## When to Use
Trigger conditions for this skill.

## Procedure
1. Step one
2. Step two

## Pitfalls
- Known failure modes and fixes

## Verification
How to confirm it worked.
```

### 生成流程

1. **Agent 完成任务**
2. **Agent 判断值得保存**
3. **Agent 构造 SKILL.md 内容**（基于刚才的执行经验）
4. **Agent 调用 skill_manage(action='create', ...)**
5. **系统验证 frontmatter 格式**
6. **系统运行安全扫描**（检查是否有恶意代码、数据泄露、提示注入）
7. **通过 → 写入 ~/.hermes/skills/**
8. **失败 → 回滚，返回错误**

### 太极OS 对比

**hermes-agent：** Agent 直接生成完整 SKILL.md  
**太极OS 当前设计：** skill_drafter 模块生成草案

**差异分析：**
- hermes-agent 完全依赖 LLM 生成质量
- 太极OS 的 skill_drafter 可以有模板、规则、质量检查

**可借鉴：**
- SKILL.md 格式规范（frontmatter + 结构化 body）
- 安全扫描机制（防止 Agent 生成恶意 Skill）
- 平台兼容性字段（platforms: [macos, linux]）

---

## 问题 3：它怎么验证 Skill？

### 三层验证

#### 1. 格式验证（_validate_frontmatter）

```python
def _validate_frontmatter(content: str) -> Optional[str]:
    # 检查是否以 --- 开头
    # 检查是否有闭合的 ---
    # 解析 YAML
    # 检查必需字段：name, description
    # 检查 description 长度 <= 1024
    # 检查 body 是否为空
```

#### 2. 安全扫描（_security_scan_skill）

```python
def _security_scan_skill(skill_dir: Path) -> Optional[str]:
    result = scan_skill(skill_dir, source="agent-created")
    allowed, reason = should_allow_install(result)
    if not allowed:
        # 回滚，返回错误
```

**扫描内容：**
- 数据泄露（curl 带密钥、读取 .env）
- 提示注入（ignore previous instructions）
- 恶意命令（rm -rf、格式化磁盘）
- 隐藏内容（HTML 注释、不可见字符）

#### 3. 回滚机制

如果验证失败：
- 删除刚创建的目录
- 或恢复原始内容（对于 edit/patch）
- 返回详细错误信息给 Agent

### 太极OS 对比

**hermes-agent：** 格式验证 + 安全扫描 + 回滚  
**太极OS 当前设计：** 三层验证（语法/行为/风险）

**可借鉴：**
- 安全扫描的具体规则（tools/skills_guard.py）
- 回滚机制（验证失败 → 立即回滚）
- 错误信息返回给 Agent（让 Agent 自己修正）

---

## 问题 4：它怎么注册 / 索引？

### 注册方式

**直接写入文件系统，无需额外注册步骤。**

```
~/.hermes/skills/
├── mlops/
│   ├── axolotl/
│   │   └── SKILL.md
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/  # Agent-created skill
│       ├── SKILL.md
│       └── references/
└── .bundled_manifest
```

### 索引方式

**启动时扫描 ~/.hermes/skills/，构建内存索引。**

```python
def build_skills_system_prompt() -> str:
    """扫描 ~/.hermes/skills/ 构建技能索引"""
    skills_by_category = {}
    for skill_file in skills_dir.rglob("SKILL.md"):
        # 检查平台兼容性
        if not _skill_is_platform_compatible(skill_file):
            continue
        # 读取 description
        desc = _read_skill_description(skill_file)
        # 按 category 分组
        skills_by_category[category].append((skill_name, desc))
    # 生成 system prompt 片段
```

### 使用方式

**两种方式：**
1. **Slash 命令：** `/gif-search funny cats`
2. **自然对话：** "帮我搜索 GIF"（Agent 自动匹配并加载 Skill）

### 渐进式加载（Progressive Disclosure）

```
Level 0: skills_list() → [{name, description, category}, ...]  (~3k tokens)
Level 1: skill_view(name) → Full content + metadata
Level 2: skill_view(name, path) → Specific reference file
```

**关键点：**
- 不是一次性加载所有 Skill 内容
- 先加载索引（name + description）
- Agent 需要时再加载完整内容

### 太极OS 对比

**hermes-agent：** 文件系统 + 启动时扫描 + 渐进式加载  
**太极OS 当前设计：** draft registry（隔离注册区）

**差异分析：**
- hermes-agent 没有"草案"概念，创建即生效
- 太极OS 有隔离注册区，需要试运行后才推广

**可借鉴：**
- 渐进式加载（Level 0/1/2）
- 平台兼容性过滤（platforms 字段）
- Category 分组（便于管理和发现）

---

## 问题 5：它怎么根据使用结果继续改进？

### 改进机制

**Agent 主动调用 `skill_manage(action='patch', ...)` 或 `skill_manage(action='edit', ...)`**

#### Patch（推荐方式）

```python
skill_manage(
    action='patch',
    name='my-skill',
    old_string='旧的错误步骤',
    new_string='修正后的步骤',
    replace_all=False  # 默认要求唯一匹配
)
```

**特点：**
- Token 高效（只传递变更部分）
- 要求唯一匹配（防止误改）
- 可以指定 file_path（修改 references/ 等支持文件）

#### Edit（大改时用）

```python
skill_manage(
    action='edit',
    name='my-skill',
    content='完整的新 SKILL.md 内容'
)
```

**特点：**
- 完整替换
- 适合结构性重写

### 改进触发条件（写在 skill_manage description 中）

```python
"Update when: instructions stale/wrong, OS-specific failures, "
"missing steps or pitfalls found during use."
```

**具体场景：**
1. **指令过时/错误**
2. **OS 特定失败**（在某个平台上不工作）
3. **使用中发现缺失步骤**
4. **发现新的坑点**

### 改进流程

1. **Agent 使用 Skill 时遇到问题**
2. **Agent 找到解决方案**
3. **Agent 判断需要更新 Skill**
4. **Agent 调用 skill_manage(action='patch', ...)**
5. **系统验证 + 安全扫描**
6. **通过 → 更新文件**
7. **失败 → 回滚 + 返回错误**

### 太极OS 对比

**hermes-agent：** Agent 主动判断 → 调用 patch/edit  
**太极OS 当前设计：** feedback loop 记录使用结果 → 自动分析 → 生成改进建议

**差异分析：**
- hermes-agent 完全依赖 Agent 的主动性
- 太极OS 有独立的反馈循环和改进分析

**可借鉴：**
- Patch 优先于 Edit（Token 效率）
- 唯一匹配要求（防止误改）
- 支持文件的独立修改（references/、templates/）

---

## 核心洞察

### 1. Agent-Curated Memory 模式

hermes-agent 的 Skill 系统本质是 **Agent 策展的程序性记忆**。

**关键特征：**
- Agent 是主体，不是被动接受
- Agent 判断什么值得保存
- Agent 决定何时更新
- Agent 负责质量

**优势：**
- 灵活，能捕获非结构化的经验
- 质量高，因为 Agent 有上下文理解

**劣势：**
- 依赖 LLM 判断力
- 可能漏掉一些模式
- 成本高（每次判断都要 LLM 推理）

### 2. 渐进式加载（Progressive Disclosure）

**三层加载：**
- Level 0：索引（name + description）
- Level 1：完整 SKILL.md
- Level 2：支持文件

**为什么重要：**
- 减少 token 消耗
- 加快响应速度
- 只在需要时加载详细内容

**太极OS 应用：**
- 在 skill_trigger_spec 中加入 Level 0 信息
- 触发条件匹配后再加载完整内容

### 3. 安全扫描是必需的

**Agent 生成的 Skill 必须扫描：**
- 数据泄露
- 提示注入
- 恶意命令
- 隐藏内容

**hermes-agent 的做法：**
- 每次 create/edit/patch/write_file 后都扫描
- 失败立即回滚
- 返回详细错误给 Agent

**太极OS 应用：**
- 在 skill_validator 中集成安全扫描
- 参考 tools/skills_guard.py 的规则

### 4. Patch 优先于 Edit

**Patch 的优势：**
- Token 高效（只传递变更）
- 精确（要求唯一匹配）
- 可审计（知道改了什么）

**Edit 的场景：**
- 结构性重写
- 大范围修改

**太极OS 应用：**
- skill_feedback_loop 生成改进建议时，优先生成 patch
- 只在必要时生成 edit

### 5. 平台兼容性是一等公民

**platforms 字段：**
```yaml
platforms: [macos, linux]  # 只在 macOS 和 Linux 上加载
```

**为什么重要：**
- 避免在不兼容平台上显示无用 Skill
- 减少 token 浪费
- 提高用户体验

**太极OS 应用：**
- 在 SKILL.md frontmatter 中加入 platforms 字段
- 在 skill_trigger_spec 中加入平台检查

---

## 对太极OS Skill 自动创建 MVP 的建议

### 1. 融合两种模式

**建议：双轨制**

#### 轨道 1：自动检测（太极OS 原设计）
- skill_candidate_detector 检测重复模式
- 生成候选清单
- **不直接创建，而是提示 Agent**

#### 轨道 2：Agent 主动创建（hermes-agent 模式）
- Agent 在任务完成后判断是否值得保存
- Agent 调用 skill_drafter 生成草案
- 进入 draft registry

**融合点：**
- 自动检测到候选后，通过 system prompt 提示 Agent："你最近做了 3 次类似的任务（列出任务），要不要保存为 Skill？"
- Agent 可以选择接受、拒绝、或修改

### 2. 采用渐进式加载

**Level 0：** skill_trigger_spec（name + description + activation_signals）  
**Level 1：** 完整 SKILL.md  
**Level 2：** 支持文件（references/、templates/）

**实施：**
- skill_drafter 生成时同时生成 trigger spec
- 触发条件匹配后再加载完整内容

### 3. 集成安全扫描

**在 skill_validator 中加入：**
- 数据泄露检测
- 提示注入检测
- 恶意命令检测
- 隐藏内容检测

**参考：** hermes-agent 的 tools/skills_guard.py

### 4. Patch 优先策略

**skill_feedback_loop 生成改进建议时：**
- 优先生成 patch（old_string + new_string）
- 只在结构性变化时生成 edit

### 5. 平台兼容性字段

**在 SKILL.md frontmatter 中加入：**
```yaml
platforms: [windows, linux, macos]  # 或 all
```

**在 skill_trigger_spec 中加入平台检查。**

---

## 实施路径

### Phase 1：最小 MVP（当前目标）

1. **skill_candidate_detector** - 检测重复模式
2. **skill_drafter** - 生成草案（包括 trigger spec）
3. **skill_validator** - 三层验证（格式 + 行为 + 安全）
4. **draft registry** - 隔离注册
5. **feedback loop** - 记录使用结果

**不做：**
- Agent 主动创建（Phase 2）
- 渐进式加载（Phase 2）
- 自动改进（Phase 3）

### Phase 2：融合 Agent 主动创建

1. 在 system prompt 中加入 SKILLS_GUIDANCE
2. 提供 skill_manage 工具（简化版）
3. 自动检测到候选后提示 Agent

### Phase 3：渐进式加载 + 自动改进

1. 实现 Level 0/1/2 加载
2. feedback loop 自动生成 patch
3. Agent 审核后应用

---

## 总结

### hermes-agent 的核心设计

1. **Agent-Curated Memory** - Agent 是主体，主动判断和创建
2. **Progressive Disclosure** - 三层加载，减少 token 消耗
3. **Security-First** - 每次写入都扫描，失败立即回滚
4. **Patch-Preferred** - 优先用 patch，减少 token 和误改风险
5. **Platform-Aware** - 平台兼容性是一等公民

### 太极OS 可借鉴的点

1. **SKILL.md 格式规范** - frontmatter + 结构化 body
2. **安全扫描机制** - tools/skills_guard.py 的规则
3. **渐进式加载** - Level 0/1/2
4. **Patch 优先策略** - 改进时优先用 patch
5. **平台兼容性字段** - platforms: [...]

### 太极OS 的独特优势

1. **自动检测** - 不依赖 Agent 主动性
2. **隔离注册** - draft registry 提供安全缓冲
3. **Reality Ledger** - 完整生命周期记录
4. **Evolution Score** - 量化 Skill 价值
5. **易经状态引擎** - 决定当前是否允许生成/验证/推广

### 下一步

1. 完成 Skill 自动创建 MVP 规格书
2. 实现 skill_candidate_detector（首个候选：heartbeat_alert_deduper）
3. 实现 skill_drafter（生成 SKILL.md + trigger spec）
4. 实现 skill_validator（格式 + 行为 + 安全）
5. 实现 draft registry
6. 实现 feedback loop

---

**研究完成时间：** 2026-03-09 10:55  
**下一步：** 编写 Skill 自动创建 MVP 规格书
