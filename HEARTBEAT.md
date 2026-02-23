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

### 每天：AIOS 基线快照
- 运行 `C:\Program Files\Python312\python.exe C:\Users\A\.openclaw\workspace\aios\learning\baseline.py snapshot`
- 追加到 baseline.jsonl
- 如果 evolution_score grade 是 degraded/critical，主动提醒珊瑚海

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

### 每周：技能探索（主动学习）
- 搜索 ClawdHub 不同类别的新技能（轮换关键词：automation、monitor、finance、news、utility、dev tools 等）
- 评估是否对珊瑚海有用（结合已知偏好：游戏、AI、系统管理、资讯）
- 有价值的直接安装并简单测试
- 记录到 memory/YYYY-MM-DD.md（学了什么、装了什么、能干什么）
- 不打扰珊瑚海，除非发现特别好用的才主动推荐

### 每天 9:00：Agent 定时任务检查
- 运行 `& "C:\Program Files\Python312\python.exe" C:\Users\A\.openclaw\workspace\aios\agent_system\auto_dispatcher.py cron`
- 触发每日/每周/每小时定时任务（代码审查、性能报告、待办检查）
- 任务自动入队，等心跳时处理
- 静默执行，除非有重要发现

### 执行规则
- 深夜(23:00-08:00)不执行，等下次心跳
- 每次只执行1个到期任务，避免耗时过长
- 执行后更新 memory/selflearn-state.json 的时间戳

### 每次心跳：AIOS Pipeline（替代原 alerts.py）
- 运行 `& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\pipeline.py run`
- Pipeline 自动执行：sensors → alerts → reactor → verifier → convergence → feedback → evolution
- 如果 evolution grade 是 critical，主动告知珊瑚海
- 如果有 high_priority 建议，简要提醒
- 如果 reactor 有 pending_confirm，告知珊瑚海确认
- 其他情况静默（HEARTBEAT_OK）

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
