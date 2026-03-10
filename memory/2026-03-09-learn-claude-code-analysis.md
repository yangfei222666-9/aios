# learn-claude-code 深度分析报告

**分析时间：** 2026-03-09  
**分析目标：** 回答 5 个核心问题，为太极OS Skill 自动创建与 Agent 编排提供参考

---

## 问题 1：任务循环是怎么一层层长出来的？

### 核心演化路径

```
s01: 最小循环 (while + stop_reason)
  ↓
s02: 工具分发 (dispatch map: name->handler)
  ↓
s03: 计划能力 (TodoManager + nag reminder)
  ↓
s04: 子代理 (fresh messages[] per child)
  ↓
s05: Skills on-demand (SKILL.md via tool_result)
  ↓
s06: 上下文压缩 (3-layer compression)
  ↓
s07: 任务图 (file-based CRUD + deps graph)
  ↓
s08: 后台任务 (daemon threads + notify queue)
  ↓
s09: Agent 团队 (teammates + JSONL mailboxes)
  ↓
s10-s12: 团队协议 + 自主 Agent + Worktree 隔离
```

### 关键洞察

**1. 循环本身从不改变**

从 s01 到 s12，核心循环始终是：

```python
def agent_loop(messages):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM,
            messages=messages, tools=TOOLS,
        )
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            return
        
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = TOOL_HANDLERS[block.name](**block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

**所有能力都是通过增加工具、修改 system prompt、或在循环外围加钩子实现的。**

**2. 演化的三个阶段**

- **Phase 1 (s01-s02)：** 建立循环 + 工具分发机制
- **Phase 2 (s03-s06)：** 增加计划、子代理、Skills、上下文管理
- **Phase 3 (s07-s09)：** 持久化（任务图）+ 并发（后台任务）+ 协作（团队）
- **Phase 4 (s10-s12)：** 团队协议 + 自主性 + 隔离执行

**3. 每一步只增加一个机制**

- s01: 一个工具 (bash) + 一个循环 = 一个 Agent
- s02: 增加工具 = 增加一个 handler
- s03: 增加计划 = 增加 TodoManager 工具
- s04: 增加子代理 = 增加 task 工具（启动新循环）
- s05: 增加 Skills = 增加 load_skill 工具
- s06: 增加压缩 = 在循环外围加压缩逻辑
- s07: 增加任务图 = 增加 task_create/update/list/get 工具
- s08: 增加后台任务 = 增加 background_run 工具 + 通知队列
- s09: 增加团队 = 增加 spawn/send/read_inbox 工具

**每一步都是"增量式"，不破坏已有结构。**

---

## 问题 2：子代理是怎么被引入的？

### 核心设计

**问题：** 主 Agent 的 messages[] 会无限增长，每次读文件、执行命令都会留在上下文里。

**解决方案：** 子代理使用独立的 messages[]，只返回摘要给父代理。

### 实现机制

```python
def run_subagent(prompt: str) -> str:
    sub_messages = [{"role": "user", "content": prompt}]
    for _ in range(30):  # 安全限制
        response = client.messages.create(
            model=MODEL, system=SUBAGENT_SYSTEM,
            messages=sub_messages,
            tools=CHILD_TOOLS, max_tokens=8000,
        )
        sub_messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            break
        
        # 执行工具，追加结果...
    
    # 只返回最后的文本摘要
    return "".join(
        b.text for b in response.content if hasattr(b, "text")
    ) or "(no summary)"
```

### 关键特性

1. **独立上下文：** 子代理的 messages[] 与父代理完全隔离
2. **只返回摘要：** 子代理可能执行 30+ 次工具调用，但父代理只收到一段文字摘要
3. **工具限制：** 子代理不能再调用 task 工具（防止递归）
4. **一次性：** 子代理执行完就销毁，没有持久化

### 对太极OS的启发

**太极OS 当前的 sessions_spawn 类似，但有两个关键差异：**

1. **learn-claude-code 的子代理是"一次性"的**，太极OS 的 spawn 是"持久化"的
2. **learn-claude-code 的子代理只返回摘要**，太极OS 的 spawn 返回完整结果

**建议：**
- 太极OS 可以增加一个"一次性子代理"模式，用于快速任务（如"读取这个文件并总结"）
- 保留当前的"持久化 spawn"用于长期任务

---

## 问题 3：Skills 是怎么被挂进主流程的？

### 核心设计：两层加载

**Layer 1：** Skill 名称 + 描述放在 system prompt（便宜）  
**Layer 2：** Skill 完整内容通过 tool_result 按需注入（昂贵）

### 实现机制

```python
class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills = {}
        for f in sorted(skills_dir.rglob("SKILL.md")):
            text = f.read_text()
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.parent.name)
            self.skills[name] = {"meta": meta, "body": body}
    
    def get_descriptions(self) -> str:
        lines = []
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "")
            lines.append(f" - {name}: {desc}")
        return "\n".join(lines)
    
    def get_content(self, name: str) -> str:
        skill = self.skills.get(name)
        if not skill:
            return f"Error: Unknown skill '{name}'."
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"
```

### System Prompt 示例

```python
SYSTEM = f"""You are a coding agent at {WORKDIR}.
Skills available:
{SKILL_LOADER.get_descriptions()}"""
```

输出：

```
You are a coding agent at /path/to/workdir.
Skills available:
 - git: Git workflow helpers
 - test: Testing best practices
 - code-review: Code review checklist
```

### 工具调用

```python
TOOL_HANDLERS = {
    "load_skill": lambda **kw: SKILL_LOADER.get_content(kw["name"]),
}
```

当 Agent 调用 `load_skill(name="git")` 时，完整的 git workflow 内容（~2000 tokens）才会被注入到 tool_result 中。

### 关键特性

1. **按需加载：** 只有 Agent 主动调用 load_skill 时，完整内容才会进入上下文
2. **Token 高效：** 10 个 Skill 的描述只占 ~100 tokens，而不是 20,000 tokens
3. **可扩展：** 增加新 Skill 只需要在 skills/ 目录下增加一个 SKILL.md 文件

### 对太极OS的启发

**这正是太极OS Skill Auto-Creation v1.1 需要的"按需激活"机制！**

**当前太极OS的问题：**
- 所有 Skill 都在启动时加载到 system prompt
- 随着 Skill 增加，system prompt 会爆炸

**learn-claude-code 的解决方案：**
- Layer 1: Skill 名称 + 描述（便宜）
- Layer 2: Skill 完整内容（按需）

**建议：**
- 在 Skill Auto-Creation v1.1 中增加 `skill_trigger_spec`
- 在 system prompt 中只放 Skill 名称 + 描述 + 触发条件
- 增加 `load_skill` 工具，让 Agent 按需加载完整内容

---

## 问题 4：后台任务结果怎么回写，哪里容易丢？

### 核心设计：通知队列

**问题：** 有些命令需要几分钟（npm install, pytest, docker build），如果阻塞等待，Agent 就无法做其他事情。

**解决方案：** 后台任务在独立线程中运行，完成后将结果放入通知队列，Agent 在每次 LLM 调用前检查队列。

### 实现机制

```python
class BackgroundManager:
    def __init__(self):
        self.tasks = {}
        self._notification_queue = []
        self._lock = threading.Lock()
    
    def run(self, command: str) -> str:
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {"status": "running", "command": command}
        thread = threading.Thread(
            target=self._execute, args=(task_id, command), daemon=True)
        thread.start()
        return f"Background task {task_id} started"
    
    def _execute(self, task_id, command):
        try:
            r = subprocess.run(command, shell=True, cwd=WORKDIR,
                             capture_output=True, text=True, timeout=300)
            output = (r.stdout + r.stderr).strip()[:50000]
        except subprocess.TimeoutExpired:
            output = "Error: Timeout (300s)"
        
        with self._lock:
            self._notification_queue.append({
                "task_id": task_id, "result": output[:500]
            })
    
    def drain_notifications(self):
        with self._lock:
            notifs = self._notification_queue[:]
            self._notification_queue.clear()
        return notifs
```

### Agent Loop 集成

```python
def agent_loop(messages: list):
    while True:
        # 在每次 LLM 调用前检查通知队列
        notifs = BG.drain_notifications()
        if notifs:
            notif_text = "\n".join(
                f"[bg:{n['task_id']}] {n['result']}" for n in notifs)
            messages.append({"role": "user",
                           "content": f"<background-results>\n{notif_text}\n</background-results>"})
            messages.append({"role": "assistant",
                           "content": "Noted background results."})
        
        response = client.messages.create(...)
        # ...
```

### 关键问题：结果容易丢失的场景

**1. Agent Loop 提前退出**

如果 Agent 在后台任务完成前就退出了（stop_reason != "tool_use"），通知队列中的结果会丢失。

**示例：**

```
1. Agent 启动后台任务 A（需要 60 秒）
2. Agent 继续做其他事情
3. Agent 在 30 秒后完成所有工作，退出循环
4. 后台任务 A 在 60 秒后完成，但 Agent 已经退出，结果丢失
```

**2. 通知队列没有持久化**

通知队列是内存中的列表，如果进程崩溃或重启，所有未读通知都会丢失。

**3. 没有超时保护**

如果后台任务永远不完成（例如死锁），通知永远不会进入队列。

### 对太极OS的启发

**太极OS 当前的问题：**
- 任务队列有持久化（task_queue.jsonl）
- 但执行结果的回写依赖 sessions_spawn 的返回
- 如果 spawn 的 Agent 提前退出，结果可能丢失

**learn-claude-code 的警示：**
- 后台任务结果必须持久化到磁盘
- 不能依赖"Agent 还在运行"这个假设
- 需要有超时保护和失败重试机制

**建议：**
- 在 task_queue.jsonl 中增加 `result` 字段
- 后台任务完成后，直接写入 task_queue.jsonl
- Heartbeat 检查时，读取 task_queue.jsonl 中的结果，而不是依赖 spawn 返回

---

## 问题 5：哪些地方是教学版，哪些地方值得太极OS吸收进正式基线？

### 教学版（不要直接照搬）

**1. JSONL 邮箱协议（s09-s12）**

- **教学版：** 每个 Agent 有一个 JSONL 文件作为收件箱，发送消息就是追加一行 JSON
- **生产版：** 需要更健壮的消息队列（如 SQLite、Redis）
- **太极OS：** 已经有 task_queue.jsonl，可以复用

**2. 简化的生命周期管理**

- **教学版：** 只有 append-only 的事件流
- **生产版：** 需要完整的生命周期钩子（PreToolUse, SessionStart/End, ConfigChange）
- **太极OS：** 已经有 Reality Ledger，比教学版更完善

**3. 没有权限治理**

- **教学版：** 所有 Agent 都有相同的工具权限
- **生产版：** 需要基于角色的权限控制
- **太极OS：** 需要增加权限治理

**4. 没有 Session 恢复/分叉**

- **教学版：** Session 是一次性的
- **生产版：** 需要支持 Session 恢复、分叉、归档
- **太极OS：** 已经有 sessions_* 工具，但需要增强

### 值得吸收进太极OS的部分

**1. 渐进式能力组织方式 ⭐⭐⭐⭐⭐**

- **核心价值：** 每一步只增加一个机制，不破坏已有结构
- **太极OS 应用：** Skill Auto-Creation 应该分阶段推进，不要一次性做太多

**2. Skills 的两层加载机制 ⭐⭐⭐⭐⭐**

- **核心价值：** Layer 1（描述）+ Layer 2（完整内容）
- **太极OS 应用：** 直接用于 Skill Auto-Creation v1.1

**3. 任务图的依赖管理 ⭐⭐⭐⭐**

- **核心价值：** blockedBy + blocks 边，自动解锁依赖
- **太极OS 应用：** 当前 task_queue.jsonl 是平坦的，可以增加依赖关系

**4. 后台任务的通知队列 ⭐⭐⭐⭐**

- **核心价值：** 在每次 LLM 调用前检查通知队列
- **太极OS 应用：** Heartbeat 可以增加通知队列检查

**5. 子代理的独立上下文 ⭐⭐⭐**

- **核心价值：** 子代理只返回摘要，不污染父代理上下文
- **太极OS 应用：** 增加"一次性子代理"模式

**6. 上下文压缩的三层策略 ⭐⭐⭐**

- **核心价值：** 保留关键信息，压缩或丢弃次要信息
- **太极OS 应用：** 当前没有上下文压缩，长期运行会爆炸

### 不值得吸收的部分

**1. 简化的 MCP 实现**

- **原因：** 教学版省略了 transport/OAuth/resource subscribe/polling
- **太极OS：** 如果需要 MCP，应该用完整的生产级实现

**2. 没有安全沙盒**

- **原因：** 教学版所有命令都直接执行
- **太极OS：** 需要沙盒隔离（参考 Agent Safehouse）

**3. 没有错误恢复**

- **原因：** 教学版没有重试、回滚、降级机制
- **太极OS：** 需要完整的错误处理

---

## 总结：对太极OS的直接建议

### 立即可做（P0）

1. **增加 Skills 的两层加载机制**
   - 在 system prompt 中只放 Skill 名称 + 描述
   - 增加 `load_skill` 工具，按需加载完整内容

2. **增加任务依赖管理**
   - 在 task_queue.jsonl 中增加 `blockedBy` 和 `blocks` 字段
   - 任务完成时自动解锁依赖

3. **增加后台任务结果持久化**
   - 后台任务完成后，直接写入 task_queue.jsonl
   - Heartbeat 检查时，读取结果而不是依赖 spawn 返回

### 短期可做（P1）

4. **增加"一次性子代理"模式**
   - 用于快速任务（如"读取这个文件并总结"）
   - 只返回摘要，不污染主 Agent 上下文

5. **增加上下文压缩机制**
   - 保留关键信息（任务、决策、错误）
   - 压缩或丢弃次要信息（中间步骤、调试输出）

### 长期可做（P2）

6. **增加权限治理**
   - 基于角色的工具权限控制
   - 高风险操作需要二次确认

7. **增加 Session 恢复/分叉**
   - 支持 Session 暂停、恢复、分叉
   - 支持 Session 归档和历史回放

---

## 最终结论

**learn-claude-code 最值得太极OS学习的是"渐进式能力组织方式"和"Skills 的两层加载机制"。**

**它不是一个可以直接照搬的生产级系统，而是一个"结构教材"。**

**太极OS 应该吸收它的设计思路，而不是复制它的实现细节。**

**最重要的是：每一步只增加一个机制，不破坏已有结构。**
