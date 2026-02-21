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

### 每周：技能探索（主动学习）
- 搜索 ClawdHub 不同类别的新技能（轮换关键词：automation、monitor、finance、news、utility、dev tools 等）
- 评估是否对珊瑚海有用（结合已知偏好：游戏、AI、系统管理、资讯）
- 有价值的直接安装并简单测试
- 记录到 memory/YYYY-MM-DD.md（学了什么、装了什么、能干什么）
- 不打扰珊瑚海，除非发现特别好用的才主动推荐

### 执行规则
- 深夜(23:00-08:00)不执行，等下次心跳
- 每次只执行1个到期任务，避免耗时过长
- 执行后更新 memory/selflearn-state.json 的时间戳

### 每次心跳：异常检查（轻量）
- 运行 `& "C:\Program Files\Python312\python.exe" C:\Users\A\.openclaw\workspace\scripts\alerts.py`
- 如果输出包含 CRIT 且有"需要立即推送"，主动告知珊瑚海
- WARN 不推送，自动进周报
- INFO 静默，仅落盘
