# Web Monitor - 快速开始

## 1. 初始化（首次运行）

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system

# 检查所有监控项（建立基线）
python web_monitor.py
```

**输出：**
```
[START] Web Monitor - 2026-03-03 13:33:00
[INFO] Total monitors: 11
[CHECK] OpenAI API Changelog
   Current: 2f30fc49b81ecf96
[INFO] First check, baseline set
...
[DONE] Changes detected: 0
```

## 2. 测试变化检测

```bash
# 模拟版本变化
python test_web_monitor.py

# 再次检查（应该检测到变化）
python web_monitor.py --filter 6h
```

**输出：**
```
[CHECK] Data Dragon Versions
   Current: 16.5.1
[CHANGE] Detected!
   Old: 16.4.1
   New: 16.5.1
[NOTIFY] Queued: 🔔 Data Dragon Versions 版本更新...
```

## 3. 处理通知

```bash
# 发送队列中的通知
python web_monitor_handler.py
```

**输出：**
```
待发送通知: 1 条
NOTIFY:🔔 Data Dragon Versions 版本更新

旧版本: 16.4.1
新版本: 16.5.1

https://ddragon.leagueoflegends.com/api/versions.json
```

## 4. 添加到 Cron（自动化）

### 方式 1：通过 OpenClaw 配置

编辑 OpenClaw 配置文件，添加 `web_monitor_cron.yaml` 中的任务。

### 方式 2：手动测试 Cron 命令

```powershell
# 测试 6 小时监控
cd C:\Users\A\.openclaw\workspace\aios\agent_system;
& "C:\Program Files\Python312\python.exe" web_monitor.py --filter 6h;
$notify = & "C:\Program Files\Python312\python.exe" web_monitor_handler.py | Out-String;
if ($notify -match 'NOTIFY:') {
    $msg = $notify -replace '.*NOTIFY:', '';
    Write-Output "TELEGRAM:$msg"
}
```

## 5. 查看状态

```bash
# 查看监控状态
cat web_monitor_state.json

# 查看通知队列
cat web_monitor_notify.json
```

## 6. 常用命令

```bash
# 检查所有监控项
python web_monitor.py

# 仅检查 6 小时频率的项
python web_monitor.py --filter 6h

# 仅检查每日频率的项
python web_monitor.py --filter daily

# 仅检查每周频率的项
python web_monitor.py --filter weekly

# 处理通知队列
python web_monitor_handler.py

# 模拟变化（测试）
python test_web_monitor.py
```

## 7. 故障排查

### 问题：无法获取内容

```bash
# 检查网络连接
curl https://ddragon.leagueoflegends.com/api/versions.json

# 检查 Python 环境
python --version
```

### 问题：无法提取值

```bash
# 手动访问 URL，检查页面结构
# 调整 web_monitor_config.yaml 中的 detection 配置
```

### 问题：误报

```bash
# 调整 min_interval_hours（默认 24h）
# 编辑 web_monitor_config.yaml
```

## 8. 监控项管理

### 启用/禁用监控项

编辑 `web_monitor_config.yaml`：

```yaml
- name: "OpenAI API Changelog"
  enabled: false  # 禁用
```

### 添加新监控项

```yaml
- name: "GitHub Releases"
  url: "https://github.com/user/repo/releases"
  purpose: "new_entries"
  frequency: "daily"
  notify: ["telegram", "heartbeat"]
  enabled: true
```

### 调整检查频率

```yaml
- name: "Data Dragon Versions"
  frequency: "6h"  # 改为 daily / weekly / weekly_2x
```

## 9. 集成到 AIOS

### 心跳报告

在 `HEARTBEAT.md` 中添加：

```markdown
## Web Monitor 检查

每天汇总监控结果：
- AI 模型更新
- LoL 补丁上线
- 运行环境变化
```

### Telegram 通知

通知会自动发送到配置的 Telegram 聊天。

## 10. 维护建议

### 每周检查

- 查看 `web_monitor_state.json`（状态是否正常）
- 查看 `web_monitor_notify.json`（通知队列是否积压）
- 检查 Cron 任务执行日志

### 每月优化

- 分析误报率（调整检测策略）
- 更新 URL（失效链接）
- 添加新监控项（根据需求）

---

**下一步：** 阅读 `WEB_MONITOR_GUIDE.md` 了解详细配置和扩展。
