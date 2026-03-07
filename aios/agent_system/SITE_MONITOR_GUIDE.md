# Site Monitor - 融合版本

## 概述

基于珊瑚海的实现 + 我的 OpenClaw 集成，融合两者优势。

**核心特性：**
- ✅ **4 种监控类型** - json_key / list_regex / github_atom / pypi
- ✅ **零依赖** - 仅用 urllib + json（可选 pyyaml）
- ✅ **双通知模式** - Telegram Bot API 或 OpenClaw 文件通信
- ✅ **防误报** - min_interval_hours（同一监控项在窗口内不重复通知）
- ✅ **错误处理** - 错误也走 min_interval，避免刷屏
- ✅ **Heartbeat 追加** - 不覆盖历史记录
- ✅ **强大的 JSON 路径** - 支持 `a.b[0].c` 混合路径

## 监控类型

### 1. JSON 字段监控（`json_key`）

监控 JSON API 的特定字段变化。

**示例：Data Dragon Versions**
```yaml
- name: "Data Dragon Versions"
  type: "json_key"
  url: "https://ddragon.leagueoflegends.com/api/versions.json"
  json_path: "0"  # 数组第一个元素
  priority: "high"
  min_interval_hours: 6
```

**JSON 路径语法：**
- `"0"` 或 `"[0]"` - 数组索引
- `"n.champion"` - 嵌套字段
- `"a.b[0].c"` - 混合路径

### 2. 列表页 Regex 监控（`list_regex`）

监控列表页的最新条目（标题 + 日期）。

**示例：LoL Patch Notes**
```yaml
- name: "LoL Patch Notes"
  type: "list_regex"
  url: "https://www.leagueoflegends.com/en-us/news/tags/patch-notes/"
  pattern: '<h2[^>]*>(?P<title>Patch [0-9.]+[^<]*)</h2>'
  priority: "high"
  min_interval_hours: 12
```

**Regex 要求：**
- 必须包含 named group `(?P<title>...)`
- 可选 named group `(?P<date>...)` 和 `(?P<link>...)`

### 3. GitHub Atom 监控（`github_atom`）

监控 GitHub 仓库的 Releases / Commits / Issues。

**示例：OpenClaw Releases**
```yaml
- name: "OpenClaw Releases"
  type: "github_atom"
  url: "https://github.com/openclaw/openclaw"
  feed_url: "https://github.com/openclaw/openclaw/releases.atom"
  priority: "high"
  min_interval_hours: 24
```

**Atom Feed 类型：**
- `releases.atom` - 新版本发布
- `commits/main.atom` - 主分支提交
- `issues.atom` - 新 Issue

### 4. PyPI 包监控（`pypi`）

监控 Python 包的版本变化。

**示例：requests 包**
```yaml
- name: "requests Package"
  type: "pypi"
  package: "requests"
  url: "https://pypi.org/project/requests/"
  priority: "daily"
  min_interval_hours: 168  # 每周检查一次
```

## 使用方式

### 1. 基本用法

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system

# 检查所有监控项
python site_monitor.py --config site_monitor_config.yaml

# 仅检查特定监控项
python site_monitor.py --config site_monitor_config.yaml --only "Data Dragon Versions,OpenClaw Releases"

# 干运行（不发送通知）
python site_monitor.py --config site_monitor_config.yaml --dry-run
```

### 2. 通知模式

**模式 1：OpenClaw 文件通信（默认）**
```bash
python site_monitor.py --config site_monitor_config.yaml
# 通知写入 site_monitor_notify.json，由 OpenClaw 处理
```

**模式 2：Telegram Bot API**
```bash
# 设置环境变量
export TG_BOT_TOKEN="your_bot_token"
export TG_CHAT_ID="your_chat_id"

# 使用 Telegram Bot
python site_monitor.py --config site_monitor_config.yaml --use-telegram-bot
```

### 3. 自定义路径

```bash
python site_monitor.py \
  --config monitors.yaml \
  --state my_state.json \
  --heartbeat reports/my_heartbeat.md \
  --notify-file my_notify.json
```

## 配置说明

### 监控项配置

```yaml
- name: "监控项名称"
  type: "监控类型"  # json_key / list_regex / github_atom / pypi
  url: "监控 URL"
  priority: "优先级"  # high / daily
  min_interval_hours: 24  # 最小通知间隔（小时）
  
  # json_key 特有
  json_path: "字段路径"
  
  # list_regex 特有
  pattern: "正则表达式"
  
  # github_atom 特有
  feed_url: "Atom Feed URL"
  
  # pypi 特有
  package: "包名"
```

### 优先级

- **`high`** - 立即 Telegram 通知
- **`daily`** - 仅记录到 Heartbeat 报告

### 最小通知间隔

防止同一监控项频繁通知：

- `6` - 6 小时内不重复通知
- `24` - 24 小时内不重复通知
- `168` - 7 天内不重复通知

## 输出示例

### 检测到变化

```
8 event(s):
- [Data Dragon Versions] JSON key changed: 0 -> 16.4.1
- [OpenClaw Releases] GitHub feed latest: 2026-03-03T04:43:08Z tag:github.com,2008:Repository/1103012935/v2026.3.2
- [requests Package] PyPI version: 2.32.5
```

### 无变化

```
no changes.
```

### Heartbeat 报告

```markdown
## 2026-03-03T13:45:00+08:00
- [Data Dragon Versions] JSON key changed: 0 -> 16.4.1 | https://ddragon.leagueoflegends.com/api/versions.json
- [OpenClaw Releases] GitHub feed latest: 2026-03-03T04:43:08Z tag:github.com,2008:Repository/1103012935/v2026.3.2 | https://github.com/openclaw/openclaw
```

## 集成到 Cron

### OpenClaw Cron 任务

```yaml
- name: "Site Monitor - High Priority"
  schedule:
    kind: "every"
    everyMs: 21600000  # 6 小时
  payload:
    kind: "systemEvent"
    text: |
      cd C:\Users\A\.openclaw\workspace\aios\agent_system;
      & "C:\Program Files\Python312\python.exe" site_monitor.py --config site_monitor_config.yaml;
      $notify = Get-Content site_monitor_notify.json -Raw | ConvertFrom-Json;
      if ($notify) {
        foreach ($n in $notify) {
          Write-Output "TELEGRAM:$($n.message)"
        }
        Remove-Item site_monitor_notify.json
      }
  sessionTarget: "main"
  enabled: true
```

## 故障排查

### 问题 1：Regex 未匹配

**症状：** `ERROR: ValueError: regex 未匹配到任何内容`

**解决：**
1. 手动访问 URL，查看页面结构
2. 调整 `pattern`，确保包含 `(?P<title>...)`
3. 使用在线 Regex 测试工具验证

### 问题 2：HTTP 403 Forbidden

**症状：** `ERROR: HTTPError: HTTP Error 403: Forbidden`

**解决：**
1. 设置环境变量 `MONITOR_UA`
2. 使用更真实的 User-Agent

```bash
export MONITOR_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### 问题 3：JSON 路径错误

**症状：** `ERROR: KeyError: 'field_name'`

**解决：**
1. 手动访问 JSON API，查看结构
2. 调整 `json_path`
3. 测试路径：

```bash
python -c "import json; print(json.loads(open('test.json').read())['path']['to']['field'])"
```

## 对比：Web Monitor vs Site Monitor

| 特性 | Web Monitor | Site Monitor |
|------|-------------|--------------|
| 依赖 | urllib + json | urllib + json |
| 监控类型 | 3 种 | 4 种 |
| GitHub 支持 | ❌ | ✅ Atom Feed |
| PyPI 支持 | ❌ | ✅ 原生支持 |
| JSON 路径 | 简单 | 强大（混合路径） |
| 通知模式 | OpenClaw | OpenClaw + Telegram Bot |
| 错误处理 | 基础 | 高级（错误也走 min_interval） |
| Heartbeat | 覆盖 | 追加 |

**建议：**
- **新项目** - 使用 Site Monitor（功能更强）
- **已有项目** - 继续使用 Web Monitor（稳定）

## 扩展监控项

### 添加新监控项

1. 编辑 `site_monitor_config.yaml`
2. 添加新条目
3. 测试：

```bash
python site_monitor.py --config site_monitor_config.yaml --only "新监控项名称" --dry-run
```

### 自定义监控类型

如果需要新的监控类型，编辑 `site_monitor.py`：

```python
elif mtype == "custom_type":
    # 自定义逻辑
    value = "..."
    changed = (value != str(last_value)) if last_value is not None else True
    msg = f"[{name}] Custom message"
```

## 维护建议

### 每周检查

- 查看 `site_monitor_state.json`（状态是否正常）
- 查看 `reports/heartbeat_monitor.md`（历史记录）
- 检查 Cron 任务执行日志

### 每月优化

- 分析误报率（调整 `min_interval_hours`）
- 更新 URL（失效链接）
- 添加新监控项（根据需求）

---

**版本：** v1.0（融合版）  
**最后更新：** 2026-03-03  
**维护者：** 小九 + 珊瑚海  
**基于：** 珊瑚海的 site_monitor.py + 小九的 web_monitor.py
