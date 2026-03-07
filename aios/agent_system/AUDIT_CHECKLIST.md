# AIOS 审计日志 + 资源限制 验收清单

## 一、审计日志系统

### 1.1 核心文件
- [x] audit_logger.py - 审计日志记录器
- [x] audit_context.py - 审计上下文透传
- [x] test_audit_system.py - 完整测试脚本

### 1.2 接入点
- [x] spawn_manager.py - spawn.request + spawn.result + file.modify
- [x] low_success_regeneration.py - policy.allow
- [ ] command_runner.py - command.exec（待集成到实际执行器）

### 1.3 事件类型覆盖
- [x] file.read / file.write / file.delete / file.modify
- [x] command.exec
- [x] spawn.request / spawn.accepted / spawn.rejected / spawn.result
- [x] policy.allow / policy.reject

### 1.4 验收标准
```bash
# 运行测试
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" test_audit_system.py

# 验收通过条件：
# 1. 所有测试通过
# 2. audit_logs/YYYY-MM-DD.jsonl 生成
# 3. 至少包含 6 种事件类型
# 4. 可通过 jq 查询
```

---

## 二、资源限制系统

### 2.1 核心文件
- [x] resource_limits.py - 资源限制配置
- [x] command_runner.py - 带限制的命令执行器

### 2.2 限制类型
- [x] 最大并发（Semaphore）
- [x] 队列长度限制
- [x] 单任务超时
- [x] stdout/stderr 上限
- [x] 超限自动 kill

### 2.3 配置项
```bash
export AIOS_MAX_AGENT_CONCURRENCY=3
export AIOS_MAX_GLOBAL_SPAWN_QUEUE=100
export AIOS_MAX_SPAWN_PER_TICK=5
export AIOS_DEFAULT_TASK_TIMEOUT_SEC=300
export AIOS_MAX_STDOUT_BYTES=1048576
export AIOS_MAX_STDERR_BYTES=1048576
```

### 2.4 验收标准
```bash
# 测试超时 kill
cd C:\Users\A\.openclaw\workspace\aios\agent_system
& "C:\Program Files\Python312\python.exe" command_runner.py

# 验收通过条件：
# 1. 正常命令执行成功
# 2. 超时命令被 kill
# 3. 审计日志记录 kill 原因
```

---

## 三、完整链路验证

### 3.1 端到端测试
```bash
# 1. 运行审计系统测试
python test_audit_system.py

# 2. 运行 spawn_manager（触发审计）
python spawn_manager.py

# 3. 运行 low_success_regeneration（触发策略审计）
python low_success_regeneration.py

# 4. 查询审计日志
jq -c 'select(.action_type=="spawn.request")' audit_logs/*.jsonl
jq -c 'select(.action_type=="policy.allow")' audit_logs/*.jsonl
jq -c 'select(.action_type=="command.exec")' audit_logs/*.jsonl
```

### 3.2 验收通过条件
- [ ] audit_logs/*.jsonl 包含完整链路事件
- [ ] spawn.request → policy.allow → spawn.result → file.modify
- [ ] 所有高危操作（risk_level=high/critical）可追溯
- [ ] 超时命令被 kill 且记录原因

---

## 四、常用查询命令

### 4.1 今天所有高危动作
```bash
jq -c 'select(.risk_level=="high" or .risk_level=="critical")' audit_logs/$(date -u +%F).jsonl
```

### 4.2 查某个 lesson 全链路
```bash
jq -c 'select(.lesson_id=="lesson-001")' audit_logs/*.jsonl
```

### 4.3 查谁执行过命令
```bash
jq -r 'select(.action_type=="command.exec") | [.timestamp,.agent_id,.target,.exit_code] | @tsv' audit_logs/*.jsonl
```

### 4.4 查被拒绝的策略
```bash
jq -c 'select(.action_type=="policy.reject")' audit_logs/*.jsonl
```

### 4.5 查超时被 kill 的命令
```bash
jq -c 'select(.action_type=="command.exec" and .result=="killed" and .reason=="timeout exceeded")' audit_logs/*.jsonl
```

---

## 五、下一步计划

### 5.1 本周必须完成
- [x] audit_event() 落地
- [x] 四类关键事件接入
- [x] timeout + 并发限制 + 输出上限 + queue 上限
- [ ] 完整链路验证（端到端测试）

### 5.2 下周可选
- [ ] CPU/内存硬限制（psutil 或 setrlimit）
- [ ] 审计看板（Web UI）
- [ ] 敏感路径保护（黑名单）
- [ ] 操作确认门槛（删除/覆盖/外发）

### 5.3 以后再做
- [ ] 权限隔离（需要重构）
- [ ] 沙箱执行（Docker）
- [ ] Elasticsearch / Loki 集成
- [ ] OpenTelemetry 集成

---

## 六、拍板建议

**本周实现边界：**
1. ✅ 审计日志落地（append-only JSONL）
2. ✅ 四类关键事件接入（file/command/spawn/policy）
3. ✅ 资源限制第一阶段（timeout/并发/输出/队列）
4. ⏳ 完整链路验证（端到端测试）

**本周不做：**
- CPU/内存硬限制
- 审计看板
- 权限模型重构
- 沙箱

**核心价值：**
> 先把"能查清楚"与"不会拖死"补上。
> 用 append-only 审计日志解决可追溯，
> 用 timeout / 并发 / 输出上限解决可生存。
> 这两件做完，系统就从"能跑"变成"可控"。

---

**最后更新：** 2026-03-06 22:50  
**维护者：** 小九 + 珊瑚海
