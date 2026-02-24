# HEARTBEAT.md

## 自学任务
检查 memory/selflearn-state.json 的上次执行时间，按需执行以下任务：

### 每周：LOL数据刷新
- 检查国服LOL版本号是否变化（对比 memory/selflearn-state.json 里的 lol_version）
- 如果版本更新了：运行 C:\Users\A\Desktop\ARAM-Helper\fetch_real_data.py 刷新172英雄出装数据
- 更新 ARAM-Helper 的 DDragon 版本号

### 每3天：记忆整理
- 读最近的 memory/YYYY-MM-DD.md 日志
- 提取重要教训和新知识到 MEMORY.md
- 清理过期信息

### 每次心跳：AIOS 插件系统
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\plugin_heartbeat.py`
- 自动初始化插件系统
- 发布心跳事件到插件
- 插件自动响应（Telegram 通知、资源监控等）
- 输出：
  - `PLUGIN_OK` - 插件系统正常
  - `PLUGIN_ALERTS:N` - 发现 N 个告警
- 上次执行时间记录在 memory/selflearn-state.json 的 last_plugin_heartbeat

### 每小时：AIOS Agent 闭环（自动化升级维护）
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\orchestrator.py`
- 完整 OODA 循环：Observe → Orient → Decide → Act → Verify → Learn
- Agent 协作流程：
  1. Monitor Agent（每5分钟）- 监控系统状态
  2. Analyst Agent（每天）- 分析历史数据
  3. Optimizer Agent（每小时）- 生成优化计划
  4. Executor Agent（每30分钟）- 执行低风险优化
  5. Validator Agent（每天）- 验证优化效果
  6. Learner Agent（每天）- 从经验中学习
- 输出：
  - `ORCHESTRATOR_OK` - 周期完成，静默
  - `ORCHESTRATOR_ACTIONS:N` - 执行了 N 个优化行动
- 日志文件：`aios/orchestrator.log`
- 上次执行时间记录在 memory/selflearn-state.json 的 last_orchestrator

### 每天：AIOS 维护 Agent
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\maintenance_agent.py`
- 健康检查（Evolution Score、事件日志大小、Agent 状态）
- 自动清理（>7天的旧数据）
- 自动备份（关键数据文件）
- 自动修复（重启降级 Agent、清理大文件）
- 输出：
  - `MAINTENANCE_OK` - 所有任务成功，静默
  - `MAINTENANCE_PARTIAL` - 部分任务失败，需要检查
- 日志文件：`aios/maintenance.log`

### 每天：AIOS 自学习分析
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\learning_heartbeat.py`
- 分析 Provider 性能（哪个模型成功率高）
- 分析 Playbook 效果（哪些规则有效）
- 分析任务路由（哪种任务适合哪个 Agent）
- 生成学习报告
- 输出：
  - `LEARNING_OK` - 无重要发现，静默
  - `LEARNING_SUGGESTIONS` - 发现优化建议
- 上次执行时间记录在 memory/selflearn-state.json 的 last_learning_analysis

### 每天：AIOS 基线快照（dry-run 模式）
- 运行 `C:\Program Files\Python312\python.exe C:\Users\A\.openclaw\workspace\aios\learning\baseline.py snapshot`
- 追加到 metrics_history.jsonl
- **dry-run 期间（2026-02-24起1天）：** 只记录数据，不主动提醒
- **正式启用后：** 如果 evolution_score grade 是 degraded/critical，主动提醒珊瑚海

### 每天：自动系统维护
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\maintenance\auto_cleanup.py`
- 清理 >7天的 events.jsonl（节省磁盘空间）
- 归档 >30天的 memory/*.md（压缩到 archive/）
- 清理临时文件（.bak、__pycache__）
- 检查磁盘空间（>80% 警告，>90% 危险）
- 输出：
  - `CLEANUP_OK` - 系统健康，静默
  - `CLEANUP_WARNING` - 磁盘使用率 >80%
  - `CLEANUP_CRITICAL` - 磁盘使用率 >90%，需要立即清理

### 每天：自动知识提取
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\learning\knowledge_extractor.py`
- 从 events.jsonl 提取重复错误模式（≥3次）
- 自动追加到 memory/lessons.json（draft 级别）
- 从最近3天的 memory/*.md 提取用户偏好
- 自动更新 USER.md（如果发现新偏好）
- 输出：
  - `KNOWLEDGE_OK` - 无新知识，静默
  - `KNOWLEDGE_EXTRACTED:N` - 提取了 N 条新教训

### 每天：自动性能优化
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\learning\performance_optimizer.py`
- 监控最近1小时的系统性能
- 识别慢操作（>5s）、高延迟（>3s）、频繁操作
- 生成优化建议（降低心跳频率、增加缓存TTL、批量写入、清理闲置Agent）
- 自动应用低风险优化
- 输出：
  - `PERF_OK` - 性能正常，静默
  - `PERF_OPTIMIZED:N` - 应用了 N 个优化
  - `PERF_DEGRADED` - 发现严重性能问题

### 每次会话开始：教训检查
- 读 memory/lessons.json 里的 rules_derived
- 读 memory/corrections.json 里的 user_preferences
- 当前任务如果涉及相关 category，主动回顾对应教训
- 犯了新错就追加到 lessons.json
- 被用户纠正就追加到 corrections.json，并更新 user_preferences

### 每周：周趋势报告
- 运行 `& "C:\Program Files\Python312\python.exe" -m aios.scripts.trend_weekly --save --format telegram`
- 检查是否有"发散中"的错误类型，有则提醒珊瑚海
- 上次执行时间记录在 selflearn-state.json 的 last_trend_weekly

### 每3天：记忆盲区扫描
- 运行 `& "C:\Program Files\Python312\python.exe" -m aios.scripts.memory_gaps --format telegram`
- 如果输出包含"盲区超阈值"，主动提醒珊瑚海并给出修复建议
- 上次执行时间记录在 selflearn-state.json 的 last_memory_gaps

### 每天：技能探索与自动安装（主动学习）
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\scripts\daily_skill_explorer.py`
- 搜索 ClawdHub 不同类别的新技能（轮换关键词：notification、backup、log、security、performance、database、github、ai、automation 等）
- 评估是否对珊瑚海有用（结合已知偏好：游戏、AI、系统管理、资讯）
- **自动安装高价值技能**（评分 ≥3.0 且与 AIOS 相关）
- 简单测试（检查 SKILL.md、运行基础命令）
- 记录到 memory/YYYY-MM-DD.md（搜了什么、装了什么、能干什么）
- 输出：
  - `SKILLS_OK` - 无新技能安装，静默
  - `SKILLS_INSTALLED:N` - 安装了 N 个新技能
- 上次执行时间记录在 memory/selflearn-state.json 的 last_skill_explore

### 每天 9:00：Agent 定时任务检查
- 运行 `& "C:\Program Files\Python312\python.exe" C:\Users\A\.openclaw\workspace\aios\agent_system\auto_dispatcher.py cron`
- 触发每日/每周/每小时定时任务（代码审查、性能报告、待办检查）
- 任务自动入队，等心跳时处理
- 静默执行，除非有重要发现

### 执行规则
- 深夜(23:00-08:00)不执行，等下次心跳
- 每次只执行1个到期任务，避免耗时过长
- 执行后更新 memory/selflearn-state.json 的时间戳

### 每次心跳：AIOS v0.6 预热版本（生产就绪）
- **首次启动：** 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\warmup.py` 预热组件
- **后续心跳：** 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\heartbeat_runner_optimized.py`
- 超快速资源监控（CPU/内存，~3ms，比原版快 443 倍）
- 仅记录事件到 events.jsonl
- 输出：
  - `HEARTBEAT_OK (2ms)` - 系统正常，静默
  - `AIOS_ALERT:xxx (5ms)` - 发现异常，记录但不自动修复
- **完整修复由 Orchestrator（每小时）和 Reactor（每10分钟）负责**

### 每次心跳：Agent 自动进化（Evolution Engine v2）
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\evolution_engine.py run`
- 完整 5 阶段进化闭环：
  1. **Observe** - 收集追踪数据、失败模式
  2. **Analyze** - 识别 Prompt 缺陷、策略缺口
  3. **Learn** - 从经验中生成新策略、提取最佳实践
  4. **Evolve** - 优化 Prompt、调整配置、合并策略
  5. **Share** - 跨 Agent 知识传播
- 频率控制：每天一次（或每 6 小时一次）
- 熔断机制：24h 内同一 Agent 最多进化 1 次
- 自动应用低风险改进（thinking level、timeout、retry、prompt 规则追加）
- 中高风险改进需要人工审核（不自动应用）
- 输出：
  - `EVOLUTION_OK` - 无需进化，静默
  - `EVOLUTION_APPLIED:N` - 应用了 N 项改进
- 状态文件：`aios/agent_system/data/evolution/engine_state.json`
- 进化报告：`aios/agent_system/data/evolution/reports/`

### 后台进程：Scheduler（自动调度核心）
- 后台运行 `scheduler.py`（开机自启）
- 监控 → 判断 → 触发 → 修复 → 验证 → 更新评分
- 自动响应资源峰值（CPU/内存/GPU）
- 自动处理任务失败和超时
- 自动管理 Agent 状态（idle/running/blocked/degraded）
- 通过 Event Bus 与其他模块通信
- 静默运行，除非有 critical 决策需要人工确认

### 每10分钟：Reactor 自动触发
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\reactor_auto_trigger.py`
- 监听最近 10 分钟的事件（error event、timeout、high latency）
- 自动匹配 playbooks 并执行修复
- 如果有 pending_confirm 的 playbook，告知珊瑚海确认
- 静默执行，除非有重要发现
- 上次执行时间记录在 memory/selflearn-state.json 的 last_reactor

### 每次心跳：Agent 任务队列
- 运行 `& "C:\Program Files\Python312\python.exe" C:\Users\A\.openclaw\workspace\aios\agent_system\auto_dispatcher.py heartbeat`
- 处理最多 5 个排队任务
- 自动路由到合适的 Agent（coder/analyst/monitor/researcher）
- 静默执行，除非有失败需要人工介入

### 每次心跳：Agent Spawn 请求处理（异步模式）
- 检查 aios/agent_system/spawn_requests.jsonl
- 如果有待处理请求，批量创建子 Agent（不等待完成）
- 使用 sessions_spawn(..., cleanup="keep") 保持会话
- 记录 spawn 状态到 spawn_results.jsonl（spawned_at + session_key）
- 通过 subagents list 异步查询结果
- 静默执行，除非有失败需要人工介入

### 每天：Agent 自我改进（Self-Improving Agent）
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\self_improving_heartbeat.py`
- 分析最近 7 天的 Agent 执行轨迹
- 识别重复失败模式（最少出现 3 次）
- 自动应用低风险改进（超时、优先级、请求频率）
- 输出：
  - `IMPROVEMENT_OK` - 系统健康，无需改进（或 24h 内已运行）
  - `IMPROVEMENT_APPLIED:N` - 应用了 N 个改进
  - `IMPROVEMENT_FAILED:1` - 改进失败，需要人工审核
- 改进报告保存到 `aios/agent_system/data/reports/cycle_*.json`
- 上次执行时间记录在 memory/selflearn-state.json 的 last_self_improving
