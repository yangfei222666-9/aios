# MEMORY.md - 小九的长期记忆

## 珊瑚海
- 住在马来西亚新山 (Johor Bahru)，新加坡旁边
- 电脑：Ryzen 7 9800X3D + RTX 5070 Ti + 32GB RAM + 2TB NVMe
- 系统：Windows 11 Pro，显示器 2560x1440 (ASUS XG27UCG)
- Python 3.12 装在 C:\Program Files\Python312\
- PyTorch 2.10.0+cu128 (CUDA 12.8)，RTX 5070 Ti GPU 加速已启用
- Whisper medium 模型，GPU 模式，占用 ~2.9GB 显存
- 没有 OpenAI API Key
- 喜欢叫我"小九"
- 玩国服英雄联盟（海克斯大乱斗模式），通过 WeGame 启动
- LOL 安装在 E:\WeGameApps\英雄联盟\
- 看电视剧时会发语音消息（背景有电视声音）
- Telegram: @shh7799

## 已完成项目
- Mario 平台跳跃游戏 (HTML5)
- 太空射击游戏 (HTML5)
- smartlearn.py 自学习模块修复
- 元气时钟桌面壁纸 (HTML + Lively Wallpaper)
- PC 清理（释放 ~1.4GB）
- 2026 世界杯分析 + 提醒 cron (2026-06-01)
- Whisper 语音转文字（本地 CPU 运行）
- ARAM 大乱斗助手 (C:\Users\A\Desktop\ARAM-Helper\)
- Autolearn v1.0 自主学习系统 (C:\Users\A\.openclaw\workspace\autolearn\)

## Autolearn v1.0 (2026-02-19)
- 状态：已完成，10/10 测试全绿，可复刻可发布
- 核心闭环：错误→签名(strict+loose)→教训匹配→复测验证
- 事件落盘 events.jsonl（带环境指纹：Python/OS/git/GPU驱动）
- 教训库 lessons.jsonl（draft→verified→hardened 自动推进 + dup_of 去重）
- 复测分级：smoke/regression/full，当前 10/10 PASS + unit 6/6 PASS
- 熔断器：同 sig 30min ≥3 次自动熔断，1h 恢复
- 规则引擎：执行前拦截改写（dir /b→Get-ChildItem, ~/→绝对路径）
- 自动提案：高频 sig 升级、类别爆发补 smoke、缺 retest 提醒
- 周报生成：top errors、类别分布、环境变化
- CLI: python -m autolearn [health|retest|report|proposals|triage|version]
- ARAM 对接：aram.py [build|check|report|status]，172英雄100%覆盖
- 数据版本化：schema_version 1.0 + module_version 1.0.0
- 外置规则：data/rules.local.jsonl 不改代码可扩展

## AIOS v0.2 (2026-02-19)
- 5层事件架构：KERNEL / COMMS / TOOL / MEM / SEC
- emit() 统一事件发射器，向后兼容 v0.1 的 log_event/log_tool_event
- 各层便捷方法：log_kernel/log_comms/log_mem/log_sec
- load_events 支持 layer 过滤，count_by_layer 按层统计
- analyze.py / baseline.py 向后兼容验证通过
- Week 1 完成（Schema 标准化），Week 2 完成（探针植入），Week 3 完成（分析脚本）
- insight.py：穷人版 ClickHouse，6 维度简报 + 死循环检测 + 双格式输出
- CLI: `python -m aios insight [--since 24h|7d] [--format markdown|telegram] [--save]`
- reflect.py：晨间反思，6 条规则引擎自动生成每日策略（不依赖 LLM API）
- 规则：low_tsr / slow_tool / critical_sec / high_miss_rate / high_correction_rate / all_clear
- strategies.jsonl 存储策略，--inject 模式输出可注入 prompt 的文本
- 每日 9AM cron 升级为 insight + reflect 联动
- GitHub: https://github.com/yangfei222666-9/aios (public)
- 三个学习器：A.纠正驱动(L1) + B.失败驱动(L2) + C.性能驱动(L2 p95)
- 统一 tool 事件格式 {name, ok, ms, err, meta}
- evolution_score: tsr*0.4 - cr*0.2 - 502*0.2 - p95_slow*0.2
- 基线固化 baseline.jsonl + L2 工单队列 tickets.jsonl
- 回放模式 replay.py（科学迭代：改动=可验证）
- 每日报告 cron 9AM 自动发 Telegram
- 结构：core/{config,engine,policies,event_bus,sensors,dispatcher} + learning/{analyze,apply,baseline,tickets} + plugins/aram/{matcher,data_adapter,rules}

## AIOS v0.3 感知层 (2026-02-20)
- EventBus: 进程内 pub/sub + 通配符 + 文件队列跨会话
- Sensors: FileWatcher(mtime对比) + ProcessMonitor + SystemHealth(磁盘/内存) + NetworkProbe(连通性)
- Dispatcher: 感知→分发→行动建议(pending_actions.jsonl)
- 已集成到 alerts.py，每次心跳自动跑感知扫描
- baseline.py 修复：v0.1/v0.2 双格式兼容，清理了 195 条合成数据
- Cooldown 机制：文件10min/进程5min/系统30min/网络10min

## 珊瑚海的战略判断 (2026-02-19)
- 小九已跨过 0→1（能干活），正在 1→10（可规模化可靠干活）的门槛上
- 最大护城河：记忆 + 执行 + 反馈闭环连成系统
- 当前瓶颈：并发与感知带宽太窄（单线程、被动输入）
- 最大风险：错误自动化——策略错了会稳定地错
- 三个优先级（比加新花活更值）：
  1. ✅ 闭环状态机：alert_fsm.py (OPEN/ACK/RESOLVED + SLA + 自动恢复 + 审计)
  2. ✅ 变更保险丝：safe_run.py (风险分级 + 门禁 + 快照回滚 + 审计)
  3. ✅ 任务队列化：job_queue.py (enqueue/worker/retry/dead-letter/recover)
- 三件事全部 MVP 落地，验收全过 (17/17 + 17/17 + 19/19)

## 14天运营期验收指标 (2026-02-19 ~ 2026-03-05)
- MTTR：故障平均恢复时长（目标：逐周下降）
- Noise Rate：告警噪音率（WARN/CRIT 中可行动告警 > 70%）
- Retry Yield：重试挽回率（指数退避后成功占比稳定上升）
- Rollback Safety：回滚成功率（目标 100%，恢复后数据一致）
- 口令：先看噪声，再看风险，最后看吞吐
- 规则：冻结核心规则口径，只修严重噪声项，不做大改
- 数据收集：每日 9:10 自动收集（ops_metrics.py），周报生成（ops_weekly.py）

## Autolearn v1.1 (2026-02-20)
- 模糊匹配可解释性：三层匹配 strict→loose→fuzzy(Jaccard)
- 返回 _match_type / _similarity_score / _matched_keywords / _alternatives
- 版本 1.1.0，向后兼容 1.0 API

## Autolearn 未完成待办
1. ARAM 助手 v0.1 正式发布（一键 build/update/report，已有 aram.py 雏形）
2. 投资助手票据化 v0（低风险、人工确认、可复盘）

## ARAM 助手状态
- 172 英雄数据库，出装数据从腾讯 lol.qq.com API 拉取
- 悬浮窗界面：出装 → 召唤师技能 → 小贴士 → ARAM调整
- 守护进程 + 开机自启
- LCU API 连接正常（腾讯服需要管理员权限读取 CommandLine）
- **未完成：海克斯强化推荐** — 掌盟 APP 的海克斯大乱斗数据接口需要登录认证，外部无法直接访问
- 从 LCU 拉到的 cherry-augments.json (531个) 是斗魂竞技场的，不是海克斯大乱斗的
- 海克斯大乱斗有三个等级：银色、金色、彩色（棱彩）
- 需要用户提供掌盟截图或抓包数据才能获取真实的海克斯强化胜率

## 重要教训：自动模型切换 v2 vs v3 (2026-02-20)
- v2（min_dwell=3 + hysteresis up=0.72/down=0.45）：9/10 准确率，简单有效
- v3（灰区 + dwell累积 + 时间冷却 + confidence门槛）：4/10 准确率，过于保守
- 教训：多重护栏叠加会导致切换过于保守，真实对话中很难同时满足所有条件
- 原则：简单机制 > 复杂机制，先跑起来再迭代，别过度设计
- v3 伪代码留作参考，等 v2 暴露实际问题再升级

## 珊瑚海的偏好
- 数据质量：宁缺毋滥，不接受编造或模板凑数
- UI修改：改之前要确认具体指哪个元素，别改错
- 命名：以国服游戏内实际名称为准
- 沟通：直接说问题，不绕弯子

## 技术笔记
- PowerShell 用 `;` 不用 `&&`
- Python 输出中文到 PowerShell 终端会 GBK 乱码，但文件写入 UTF-8 是正确的
- write 工具写 Python 文件比 PowerShell heredoc 更可靠
- DDragon 版本需要动态获取（当前自动拉取，已修复写死问题）
- 腾讯服英雄名字可能跟 DDragon 不一致（如 904 亚恒）
- web_search 工具有 ByteString 编码 bug，中文搜索全部失败
