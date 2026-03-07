# Web Monitor - 通用网页监控系统

## 概述

监控 AI 模型、LoL 数据、运行环境的更新，自动检测变化并通知。

**核心特性：**
- ✅ 配置驱动（YAML）
- ✅ 多检测策略（JSON 字段、列表页标题、内容哈希）
- ✅ 分级通知（Telegram 紧急 + 心跳报告汇总）
- ✅ 防误报（24h 内同一消息不重复通知）
- ✅ 状态持久化（断点续传）

## 文件结构

```
aios/agent_system/
├── web_monitor_config.yaml    # 监控配置（12 个监控项）
├── web_monitor.py              # 主监控脚本
├── web_monitor_handler.py      # 通知处理器
├── web_monitor_state.json      # 状态文件（自动生成）
├── web_monitor_notify.json     # 通知队列（自动生成）
└── web_monitor_cron.yaml       # Cron 任务配置
```

## 监控清单（12 个）

### A. AI / 大模型与接口变更（5 个）
1. **OpenAI ChatGPT Release Notes** - 每天检查
2. **OpenAI Model Release Notes** - 每天检查
3. **OpenAI API Changelog** - 每 6 小时检查
4. **Anthropic Newsroom** - 每天检查
5. ~~OpenAI Codex Changelog~~ - 已移除（URL 失效）

### B. ARAM / LoL 数据与版本（5 个）
6. **LoL Patch Notes** - 每天检查
7. **LoL Patch Schedule** - 每周 2 次
8. **Data Dragon Versions** - 每 6 小时检查（最关键）
9. **Data Dragon Realms (NA)** - 每天检查
10. **Riot API Change Log** - 每周检查

### C. 运行环境更新（2 个）
11. **Node.js Blog** - 每周 2 次
12. **Python Downloads** - 每周检查

## 检测策略

### 1. JSON 字段监控（`json_field`）
- **用途：** API 端点、版本文件
- **示例：** Data Dragon Versions
- **逻辑：** 提取 `versions[0]`，对比上次值

### 2. 列表页标题监控（`first_item_title`）
- **用途：** 博客、新闻、补丁说明
- **示例：** LoL Patch Notes
- **逻辑：** 提取第一条 `<h2>` 标题，对比上次值

### 3. 内容哈希监控（`content_hash`）
- **用途：** 静态页面、时间表
- **示例：** LoL Patch Schedule
- **逻辑：** 计算内容 MD5，对比上次值

## 使用方式

### 1. 手动运行（测试）

```bash
# 检查所有监控项
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python web_monitor.py

# 按频率过滤
python web_monitor.py --filter 6h      # 仅检查 6 小时频率的项
python web_monitor.py --filter daily   # 仅检查每日频率的项
python web_monitor.py --filter weekly  # 仅检查每周频率的项
```

### 2. 处理通知队列

```bash
# 发送队列中的第一条通知
python web_monitor_handler.py
```

### 3. Cron 自动调度

将 `web_monitor_cron.yaml` 中的任务添加到 OpenClaw 配置：

```yaml
cron:
  jobs:
    # 复制 web_monitor_cron.yaml 的内容到这里
```

**调度计划：**
- **每 6 小时** - OpenAI API Changelog, Data Dragon Versions
- **每天 09:00** - ChatGPT/Model Release Notes, LoL Patch Notes, Anthropic, Realms
- **每周一/周四 10:00** - LoL Patch Schedule, Node.js Blog
- **每周一 11:00** - Riot API Change Log, Python Downloads

## 配置说明

### 监控项配置

```yaml
- name: "监控项名称"
  url: "https://example.com"
  purpose: "检测策略"  # new_entries / version_changed / content_hash
  frequency: "检查频率"  # 6h / daily / weekly_2x / weekly
  notify: ["通知方式"]  # heartbeat / telegram / telegram_major
  enabled: true
```

### 通知方式

- **`heartbeat`** - 心跳报告（汇总）
- **`telegram`** - Telegram 立即推送
- **`telegram_major`** - 仅重大更新推送
- **`telegram_on_vuln`** - 仅漏洞推送

### 防误报配置

```yaml
notification:
  min_interval_hours: 24  # 同一条消息 24h 内不重复通知
```

## 输出示例

### 检测到变化

```
[START] Web Monitor - 2026-03-03 13:30:00

[CHECK] Data Dragon Versions
   URL: https://ddragon.leagueoflegends.com/api/versions.json
   Purpose: version_changed
   Current: 15.5.1
[CHANGE] Detected!
   Old: 15.4.1
   New: 15.5.1
[NOTIFY] Queued: 🔔 Data Dragon Versions 版本更新...

[DONE] Changes detected: 1
[SAVE] State saved to web_monitor_state.json
```

### 无变化

```
[START] Web Monitor - 2026-03-03 13:30:00

[CHECK] LoL Patch Notes
   URL: https://www.leagueoflegends.com/en-us/news/tags/patch-notes/
   Purpose: new_patch_notes
   Current: Patch 15.5 Notes
[OK] No change

[DONE] Changes detected: 0
```

## 故障排查

### 1. 无法获取内容

**症状：** `[ERROR] Failed to fetch`

**原因：**
- 网络问题
- URL 失效
- 反爬虫限制

**解决：**
- 检查网络连接
- 验证 URL 是否有效
- 调整 User-Agent

### 2. 无法提取值

**症状：** `[WARN] Failed to extract value`

**原因：**
- 页面结构变化
- 正则表达式不匹配
- JSON 字段路径错误

**解决：**
- 手动访问 URL，检查页面结构
- 调整 `detection` 配置中的 `selector` 或 `field`

### 3. 误报（频繁通知）

**症状：** 同一条消息重复通知

**原因：**
- 页面包含动态内容（时间戳、随机 ID）
- 检测策略不稳定

**解决：**
- 调整 `min_interval_hours`（默认 24h）
- 切换检测策略（`content_hash` → `first_item_title`）

## 扩展监控项

### 添加新监控项

1. 编辑 `web_monitor_config.yaml`
2. 添加新条目：

```yaml
- name: "GitHub Releases"
  url: "https://github.com/user/repo/releases"
  purpose: "new_entries"
  frequency: "daily"
  notify: ["telegram", "heartbeat"]
  enabled: true
```

3. 运行测试：

```bash
python web_monitor.py --filter daily
```

### 添加新检测策略

1. 编辑 `web_monitor.py`
2. 在 `check_monitor()` 中添加新 `method`
3. 在 `web_monitor_config.yaml` 的 `detection` 中配置

## 性能优化

### 1. 减少网络请求

- 按频率分组调度（6h / daily / weekly）
- 避免高峰时段（09:00-10:00）

### 2. 缓存优化

- 状态文件（`web_monitor_state.json`）持久化
- 通知队列（`web_monitor_notify.json`）批量处理

### 3. 超时控制

- 默认超时：10 秒
- 可在 `fetch_content()` 中调整

## 集成到 AIOS

### 1. 心跳报告

在 `HEARTBEAT.md` 中添加：

```markdown
## Web Monitor 检查

每天汇总监控结果：
- AI 模型更新
- LoL 补丁上线
- 运行环境变化
```

### 2. Telegram 通知

通知格式：

```
🔔 Data Dragon Versions 版本更新

旧版本: 15.4.1
新版本: 15.5.1

https://ddragon.leagueoflegends.com/api/versions.json
```

### 3. Dashboard 集成

在 AIOS Dashboard 中显示：
- 最近 7 天的变化
- 监控项状态（正常/异常）
- 通知历史

## 维护建议

### 每周检查

1. 查看 `web_monitor_state.json`（状态是否正常）
2. 查看 `web_monitor_notify.json`（通知队列是否积压）
3. 检查 Cron 任务执行日志

### 每月优化

1. 分析误报率（调整检测策略）
2. 更新 URL（失效链接）
3. 添加新监控项（根据需求）

## 常见问题

### Q: 为什么有些监控项没有通知？

A: 检查 `notify` 配置，确保包含 `telegram` 或 `telegram_major`。

### Q: 如何临时禁用某个监控项？

A: 在 `web_monitor_config.yaml` 中设置 `enabled: false`。

### Q: 如何调整检查频率？

A: 修改 `frequency` 字段，并更新对应的 Cron 任务。

### Q: 如何查看历史通知？

A: 查看 `web_monitor_notify.json`（队列）和 Telegram 聊天记录。

## 下一步

- [ ] 添加 RSS/Atom 订阅支持
- [ ] 集成 GitHub Releases 监控
- [ ] 支持 Webhook 通知
- [ ] Dashboard 可视化
- [ ] 邮件通知支持

---

**版本：** v1.0  
**最后更新：** 2026-03-03  
**维护者：** 小九 + 珊瑚海
