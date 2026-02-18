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

### 每次会话开始：教训检查
- 读 memory/lessons.json 里的 rules_derived
- 读 memory/corrections.json 里的 user_preferences
- 当前任务如果涉及相关 category，主动回顾对应教训
- 犯了新错就追加到 lessons.json
- 被用户纠正就追加到 corrections.json，并更新 user_preferences

### 执行规则
- 深夜(23:00-08:00)不执行，等下次心跳
- 每次只执行1个到期任务，避免耗时过长
- 执行后更新 memory/selflearn-state.json 的时间戳
