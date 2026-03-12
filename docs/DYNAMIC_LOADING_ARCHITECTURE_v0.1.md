# 太极OS 动态加载最小架构 v0.1

**设计原则：** 受控扩展性 > 极限热插拔能力

**核心理念：** 先做"可控动态加载"，不做"任意二进制加载"。

---

## 1. 设计目标

### 1.1 要解决的问题

- **Skill/Agent 能按需发现、注册、卸载**
  - 新 Skill 放进目录就能被发现
  - 不需要重启整个系统
  - 有明确的 manifest / version / capability

- **失败隔离**
  - 一个 Skill 加载失败，不能拖垮主系统
  - 进程级隔离，不是直接把不可信模块塞进主进程

- **热更新边界清晰**
  - 哪些可以热更新：配置、prompt、规则、纯 Python skill
  - 哪些不能热更新：核心状态模型、共享协议、关键适配层

### 1.2 与太极OS原则一致

- **上善若水** - 按需加载，不抢资源
- **大道至简** - 先 manifest + registry，不先上复杂插件总线
- **知止不殆** - 先做安全装载，再谈真正 hot reload

---

## 2. 目录结构

```
aios/
├── skills/                    # Skill 目录
│   ├── skill-a/
│   │   ├── skill.json        # Manifest（必需）
│   │   ├── SKILL.md          # 文档（必需）
│   │   ├── main.py           # 入口（必需）
│   │   └── ...               # 其他文件
│   ├── skill-b/
│   └── ...
├── agents/                    # Agent 目录
│   ├── agent-x/
│   │   ├── agent.json        # Manifest（必需）
│   │   ├── prompt.md         # Prompt 模板（必需）
│   │   ├── config.json       # 配置（可选）
│   │   └── ...
│   └── ...
└── agent_system/
    ├── registry/              # 注册表
    │   ├── skill_registry.json
    │   └── agent_registry.json
    └── loader/                # 加载器
        ├── skill_loader.py
        ├── agent_loader.py
        └── manifest_validator.py
```

---

## 3. Manifest 字段

### 3.1 Skill Manifest (`skill.json`)

```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "type": "skill",
  "entry": "main.py",
  "capabilities": ["read", "write", "network"],
  "dependencies": ["requests", "lancedb"],
  "trigger": {
    "activation_signals": ["keyword1", "keyword2"],
    "negative_conditions": ["exclude1"],
    "priority_score": 50
  },
  "isolation": {
    "mode": "process",
    "timeout_seconds": 60,
    "max_memory_mb": 512
  },
  "hot_reload": {
    "config": true,
    "prompt": true,
    "code": false
  },
  "metadata": {
    "author": "author-name",
    "description": "Skill description",
    "tags": ["tag1", "tag2"]
  }
}
```

**必需字段：**
- `name` - Skill 名称（唯一标识）
- `version` - 版本号（语义化版本）
- `type` - 类型（固定为 "skill"）
- `entry` - 入口文件（相对路径）

**可选字段：**
- `capabilities` - 权限声明（read/write/network/exec）
- `dependencies` - Python 依赖
- `trigger` - 触发条件
- `isolation` - 隔离配置
- `hot_reload` - 热更新配置
- `metadata` - 元数据

### 3.2 Agent Manifest (`agent.json`)

```json
{
  "name": "agent-name",
  "version": "1.0.0",
  "type": "agent",
  "role": "coder",
  "prompt_template": "prompt.md",
  "model": "claude-sonnet-4-6",
  "capabilities": ["code", "analysis"],
  "trigger": {
    "task_types": ["code", "refactor"],
    "priority": 80
  },
  "isolation": {
    "mode": "session",
    "timeout_seconds": 300
  },
  "hot_reload": {
    "config": true,
    "prompt": true,
    "model": true
  },
  "metadata": {
    "author": "author-name",
    "description": "Agent description",
    "tags": ["tag1", "tag2"]
  }
}
```

**必需字段：**
- `name` - Agent 名称（唯一标识）
- `version` - 版本号
- `type` - 类型（固定为 "agent"）
- `role` - 角色（coder/analyst/monitor/learner）
- `prompt_template` - Prompt 模板文件

---

## 4. 注册流程

### 4.1 发现阶段

**触发方式：**
- 系统启动时扫描
- 定期扫描（每 5 分钟）
- 手动触发（`aios.py reload`）

**扫描逻辑：**
```python
def discover_skills():
    skills_dir = Path("aios/skills")
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        
        manifest_path = skill_dir / "skill.json"
        if not manifest_path.exists():
            log_warning(f"Skill {skill_dir.name} missing skill.json")
            continue
        
        yield skill_dir, manifest_path
```

### 4.2 校验阶段

**三层校验：**

1. **格式校验** - JSON 格式、必需字段
2. **依赖校验** - Python 依赖是否已安装
3. **安全校验** - 权限声明、代码扫描

```python
def validate_manifest(manifest_path):
    # 1. 格式校验
    manifest = json.loads(manifest_path.read_text())
    required_fields = ["name", "version", "type", "entry"]
    for field in required_fields:
        if field not in manifest:
            raise ValidationError(f"Missing required field: {field}")
    
    # 2. 依赖校验
    if "dependencies" in manifest:
        for dep in manifest["dependencies"]:
            if not is_installed(dep):
                raise ValidationError(f"Missing dependency: {dep}")
    
    # 3. 安全校验
    if "capabilities" in manifest:
        for cap in manifest["capabilities"]:
            if cap not in ALLOWED_CAPABILITIES:
                raise ValidationError(f"Forbidden capability: {cap}")
    
    return manifest
```

### 4.3 注册阶段

**注册表结构：**

```json
{
  "skills": {
    "skill-name": {
      "name": "skill-name",
      "version": "1.0.0",
      "path": "aios/skills/skill-name",
      "status": "registered",
      "registered_at": "2026-03-12T11:15:00Z",
      "last_loaded": null,
      "load_count": 0,
      "error_count": 0
    }
  }
}
```

**注册逻辑：**
```python
def register_skill(manifest, skill_path):
    registry = load_registry()
    
    skill_name = manifest["name"]
    if skill_name in registry["skills"]:
        # 版本检查
        existing_version = registry["skills"][skill_name]["version"]
        new_version = manifest["version"]
        if new_version <= existing_version:
            log_info(f"Skill {skill_name} already registered with same or newer version")
            return
    
    # 注册
    registry["skills"][skill_name] = {
        "name": skill_name,
        "version": manifest["version"],
        "path": str(skill_path),
        "status": "registered",
        "registered_at": datetime.now().isoformat(),
        "last_loaded": None,
        "load_count": 0,
        "error_count": 0
    }
    
    save_registry(registry)
    log_info(f"Skill {skill_name} registered successfully")
```

### 4.4 路由阶段

**路由逻辑：**
```python
def route_task(task):
    registry = load_registry()
    
    # 1. 根据 task type 筛选候选 Skill/Agent
    candidates = []
    for skill_name, skill_info in registry["skills"].items():
        manifest = load_manifest(skill_info["path"])
        if matches_trigger(manifest["trigger"], task):
            candidates.append((skill_name, manifest))
    
    # 2. 按优先级排序
    candidates.sort(key=lambda x: x[1]["trigger"]["priority_score"], reverse=True)
    
    # 3. 返回最高优先级的 Skill
    if candidates:
        return candidates[0][0]
    else:
        return None
```

---

## 5. 失败隔离

### 5.1 进程级隔离

**原则：** 每个 Skill 在独立进程中运行，失败不影响主系统。

**实现方式：**
```python
def execute_skill(skill_name, task):
    manifest = load_manifest_by_name(skill_name)
    isolation_config = manifest.get("isolation", {})
    
    # 默认配置
    mode = isolation_config.get("mode", "process")
    timeout = isolation_config.get("timeout_seconds", 60)
    max_memory = isolation_config.get("max_memory_mb", 512)
    
    if mode == "process":
        # 启动独立进程
        proc = subprocess.Popen(
            ["python", manifest["entry"], json.dumps(task)],
            cwd=manifest["path"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            if proc.returncode != 0:
                raise SkillExecutionError(f"Skill failed: {stderr.decode()}")
            return json.loads(stdout.decode())
        except subprocess.TimeoutExpired:
            proc.kill()
            raise SkillTimeoutError(f"Skill timeout after {timeout}s")
    else:
        raise ValueError(f"Unsupported isolation mode: {mode}")
```

### 5.2 超时保护

**三层超时：**
1. **Skill 级超时** - manifest 中的 `timeout_seconds`
2. **Task 级超时** - 任务队列的 `max_execution_time`
3. **全局超时** - 系统级的 `global_timeout`

**超时处理：**
- 超时后立即 kill 进程
- 记录超时事件到 `skill_execution_errors.jsonl`
- 更新注册表的 `error_count`
- 如果连续超时 3 次，自动禁用 Skill

### 5.3 状态回滚

**原则：** Skill 失败后，系统状态应回滚到执行前。

**实现方式：**
```python
def execute_skill_with_rollback(skill_name, task):
    # 1. 保存当前状态
    snapshot = save_state_snapshot()
    
    try:
        # 2. 执行 Skill
        result = execute_skill(skill_name, task)
        
        # 3. 验证结果
        if not validate_result(result):
            raise SkillValidationError("Invalid result format")
        
        return result
    except Exception as e:
        # 4. 回滚状态
        restore_state_snapshot(snapshot)
        log_error(f"Skill {skill_name} failed, state rolled back: {e}")
        raise
```

---

## 6. 热更新边界

### 6.1 可热更新

**配置文件：**
- `config.json` - Skill/Agent 配置
- `prompt.md` - Agent prompt 模板
- `trigger` 字段 - 触发条件

**更新方式：**
```python
def hot_reload_config(skill_name):
    manifest = load_manifest_by_name(skill_name)
    
    if not manifest.get("hot_reload", {}).get("config", False):
        raise HotReloadError(f"Skill {skill_name} does not support config hot reload")
    
    # 重新加载配置
    config_path = Path(manifest["path"]) / "config.json"
    new_config = json.loads(config_path.read_text())
    
    # 更新注册表
    registry = load_registry()
    registry["skills"][skill_name]["config"] = new_config
    save_registry(registry)
    
    log_info(f"Skill {skill_name} config hot reloaded")
```

### 6.2 不可热更新

**核心协议：**
- `status_adapter.py` - 状态适配层
- `task_queue.py` - 任务队列协议
- `agent_router.py` - Agent 路由逻辑

**共享数据结构：**
- `agents.json` - Agent 注册表
- `task_queue.jsonl` - 任务队列
- `agent_execution_record.jsonl` - 执行记录

**原因：** 这些是系统的"骨架"，热更新会导致状态不一致、数据污染、协议破裂。

**更新方式：** 必须重启系统。

### 6.3 热更新检查

**启动时检查：**
```python
def check_hot_reload_safety():
    # 检查核心文件是否被修改
    core_files = [
        "aios/agent_system/core/status_adapter.py",
        "aios/agent_system/core/task_queue.py",
        "aios/agent_system/core/agent_router.py"
    ]
    
    for file_path in core_files:
        if file_modified_since_last_boot(file_path):
            log_warning(f"Core file {file_path} modified, restart required")
            return False
    
    return True
```

---

## 7. 实施路径

### Phase 1: 最小可用（当前）

**目标：** 证明"目录扫描 + manifest 校验 + 注册表"可行。

**任务：**
1. ✅ 实现 `skill_loader.py` - 扫描 skills/ 目录
2. ✅ 实现 `manifest_validator.py` - 校验 skill.json
3. ✅ 实现 `skill_registry.json` - 注册表
4. ✅ 实现 `aios.py reload` - 手动触发重新加载

**验收标准：**
- 新 Skill 放进 skills/ 目录后，执行 `aios.py reload` 能被发现并注册
- 注册表能正确记录 Skill 信息
- 校验失败的 Skill 不会被注册

### Phase 2: 进程隔离（下一步）

**目标：** 证明"进程级隔离 + 超时保护"可行。

**任务：**
1. 实现 `execute_skill()` - 在独立进程中执行 Skill
2. 实现超时保护 - 超时后 kill 进程
3. 实现错误记录 - 记录到 `skill_execution_errors.jsonl`
4. 实现自动禁用 - 连续失败 3 次后禁用

**验收标准：**
- Skill 超时后不会拖垮主系统
- 错误能被正确记录
- 连续失败的 Skill 能被自动禁用

### Phase 3: 热更新（未来）

**目标：** 证明"配置热更新 + 核心协议保护"可行。

**任务：**
1. 实现 `hot_reload_config()` - 热更新配置
2. 实现核心文件检查 - 启动时检查核心文件是否被修改
3. 实现热更新日志 - 记录所有热更新操作

**验收标准：**
- 配置文件修改后能立即生效
- 核心文件修改后系统拒绝启动（要求重启）
- 所有热更新操作有日志可追溯

---

## 8. 与现有系统集成

### 8.1 与 Skill 自动创建集成

**流程：**
```
发现重复模式 → 生成 Skill 草案 → 验证 → 写入 skills/draft/ → 触发 reload → 注册到 draft registry
```

**关键点：**
- 草案 Skill 放在 `skills/draft/` 目录
- 正式 Skill 放在 `skills/` 目录
- 两者使用相同的 manifest 格式和注册流程

### 8.2 与 Agent 系统集成

**流程：**
```
新 Agent 放入 agents/ → 触发 reload → 注册到 agent_registry.json → 任务路由时可用
```

**关键点：**
- Agent 的 manifest 包含 `role` 和 `task_types`
- 任务路由时根据 `task_types` 匹配 Agent
- Agent 的隔离模式是 `session`（不是 `process`）

### 8.3 与 Heartbeat 集成

**定期扫描：**
```python
def heartbeat():
    # ... 其他检查 ...
    
    # 定期扫描新 Skill/Agent
    if should_reload():
        reload_skills()
        reload_agents()
    
    # ... 其他检查 ...
```

**扫描频率：** 每 5 分钟一次（可配置）

---

## 9. 安全考虑

### 9.1 权限声明

**原则：** Skill 必须声明所需权限，系统根据权限决定是否允许执行。

**权限类型：**
- `read` - 读取文件
- `write` - 写入文件
- `network` - 网络访问
- `exec` - 执行外部命令

**检查逻辑：**
```python
def check_permission(skill_name, action):
    manifest = load_manifest_by_name(skill_name)
    capabilities = manifest.get("capabilities", [])
    
    if action not in capabilities:
        raise PermissionError(f"Skill {skill_name} does not have {action} permission")
```

### 9.2 代码扫描

**扫描内容：**
- 危险函数调用（`eval`, `exec`, `__import__`）
- 文件系统操作（`os.remove`, `shutil.rmtree`）
- 网络操作（`requests`, `urllib`）
- 进程操作（`subprocess`, `os.system`）

**扫描时机：**
- 注册时扫描一次
- 热更新时重新扫描

### 9.3 沙箱隔离

**未来方向：**
- 使用 Docker 容器隔离 Skill
- 使用 seccomp/AppArmor 限制系统调用
- 使用 cgroups 限制资源使用

**当前阶段：** 进程级隔离 + 超时保护已足够。

---

## 10. 监控与观测

### 10.1 注册表监控

**监控指标：**
- 已注册 Skill/Agent 数量
- 加载成功/失败次数
- 平均加载时间
- 错误率

**输出位置：**
- Dashboard - 实时显示
- 健康报告 - 每日汇总

### 10.2 执行监控

**监控指标：**
- Skill 执行次数
- 平均执行时间
- 超时次数
- 失败次数

**输出位置：**
- `skill_execution_record.jsonl` - 详细记录
- Dashboard - 实时显示

### 10.3 热更新监控

**监控指标：**
- 热更新次数
- 热更新成功/失败次数
- 核心文件修改检测

**输出位置：**
- `hot_reload_log.jsonl` - 详细记录
- 健康报告 - 每日汇总

---

## 11. 总结

### 11.1 核心价值

太极OS 动态加载机制的核心价值不是"极限性能"或"任意二进制加载"，而是：

1. **可控扩展性** - 新能力能安全地加入系统
2. **失败隔离** - 单个能力失败不拖垮整个系统
3. **可观测性** - 所有加载、执行、失败都有记录
4. **热更新边界清晰** - 知道什么能热更、什么不能热更

### 11.2 与太极OS原则一致

- **上善若水** - 按需加载，不抢资源
- **大道至简** - manifest + registry，不上复杂插件总线
- **细作** - 先最小可运行，再扩展
- **自明** - 所有操作可观测、可追溯
- **知止** - 先做安全装载，不追求极限热插拔

### 11.3 下一步

1. **Phase 1** - 实现最小可用（目录扫描 + manifest 校验 + 注册表）
2. **Phase 2** - 实现进程隔离（独立进程 + 超时保护 + 错误记录）
3. **Phase 3** - 实现热更新（配置热更 + 核心协议保护）

**当前优先级：** Phase 1

---

**版本：** v0.1  
**最后更新：** 2026-03-12  
**维护者：** 小九 + 珊瑚海
