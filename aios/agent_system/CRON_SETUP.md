# Site Monitor Cron 配置示例

## Linux/macOS Crontab

编辑 crontab：
```bash
crontab -e
```

添加以下任务：

```cron
# Site Monitor - 每 6 小时检查一次（高优先级）
0 */6 * * * /path/to/run_site_monitor.sh >> /path/to/logs/cron.log 2>&1

# Site Monitor - 每天 09:00 检查一次（每日优先级）
0 9 * * * /path/to/run_site_monitor.sh >> /path/to/logs/cron.log 2>&1

# Site Monitor - 每周一/周四 10:00 检查一次（每周 2 次）
0 10 * * 1,4 /path/to/run_site_monitor.sh >> /path/to/logs/cron.log 2>&1
```

## Windows 任务计划程序

### 方式 1：通过 GUI

1. 打开"任务计划程序"（Task Scheduler）
2. 创建基本任务
3. 触发器：每 6 小时
4. 操作：启动程序
   - 程序：`powershell.exe`
   - 参数：`-ExecutionPolicy Bypass -File "C:\Users\A\.openclaw\workspace\aios\agent_system\run_site_monitor.ps1"`

### 方式 2：通过 PowerShell

```powershell
# 每 6 小时执行一次
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Users\A\.openclaw\workspace\aios\agent_system\run_site_monitor.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6)
Register-ScheduledTask -TaskName "SiteMonitor-6h" -Action $action -Trigger $trigger -Description "Site Monitor - High Priority (6h)"

# 每天 09:00 执行一次
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Users\A\.openclaw\workspace\aios\agent_system\run_site_monitor.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
Register-ScheduledTask -TaskName "SiteMonitor-Daily" -Action $action -Trigger $trigger -Description "Site Monitor - Daily Priority"
```

## OpenClaw Cron（推荐）

在 OpenClaw 配置中添加：

```yaml
cron:
  jobs:
    # Site Monitor - 每 6 小时
    - name: "Site Monitor - High Priority"
      schedule:
        kind: "every"
        everyMs: 21600000  # 6 小时
      payload:
        kind: "systemEvent"
        text: |
          cd C:\Users\A\.openclaw\workspace\aios\agent_system;
          & "C:\Program Files\Python312\python.exe" site_monitor.py --config monitors.yaml;
          if (Test-Path site_monitor_notify.json) {
            $notify = Get-Content site_monitor_notify.json -Raw | ConvertFrom-Json;
            foreach ($n in $notify) {
              Write-Output "TELEGRAM:$($n.message)"
            }
            Remove-Item site_monitor_notify.json
          }
      sessionTarget: "main"
      enabled: true

    # Site Monitor - 每天 09:00
    - name: "Site Monitor - Daily"
      schedule:
        kind: "cron"
        expr: "0 9 * * *"
        tz: "Asia/Shanghai"
      payload:
        kind: "systemEvent"
        text: |
          cd C:\Users\A\.openclaw\workspace\aios\agent_system;
          & "C:\Program Files\Python312\python.exe" site_monitor.py --config monitors.yaml;
          if (Test-Path site_monitor_notify.json) {
            $notify = Get-Content site_monitor_notify.json -Raw | ConvertFrom-Json;
            foreach ($n in $notify) {
              Write-Output "TELEGRAM:$($n.message)"
            }
            Remove-Item site_monitor_notify.json
          }
      sessionTarget: "main"
      enabled: true
```

## 测试

### 手动测试

```bash
# Linux/macOS
./run_site_monitor.sh --dry-run

# Windows
powershell -ExecutionPolicy Bypass -File run_site_monitor.ps1 -DryRun
```

### 查看日志

```bash
# Linux/macOS
tail -f logs/site_monitor.log

# Windows
Get-Content logs\site_monitor.log -Tail 20 -Wait
```

## 故障排查

### 问题 1：权限错误

**Linux/macOS：**
```bash
chmod +x run_site_monitor.sh
```

**Windows：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 2：锁文件残留

**Linux/macOS：**
```bash
rm /tmp/site_monitor.lock
```

**Windows：**
```powershell
Remove-Item C:\Users\A\.openclaw\workspace\aios\agent_system\site_monitor.lock
```

### 问题 3：Python 路径错误

**检查 Python 路径：**
```bash
# Linux/macOS
which python3

# Windows
where python
```

更新脚本中的 `$PY` 变量。

---

**推荐配置：**
- **开发/测试** - 手动运行脚本
- **生产环境** - OpenClaw Cron（集成度最高）
- **独立部署** - 系统 Cron/任务计划程序
