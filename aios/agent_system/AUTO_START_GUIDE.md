# Memory Server 开机自启动配置说明

## 方法 1：Windows 任务计划程序（推荐）

### 创建任务

1. 打开任务计划程序：`Win + R` → 输入 `taskschd.msc`
2. 点击"创建基本任务"
3. 填写信息：
   - 名称：`AIOS Memory Server`
   - 描述：`自动启动 AIOS Memory Server`
4. 触发器：选择"当计算机启动时"
5. 操作：选择"启动程序"
   - 程序/脚本：`powershell.exe`
   - 添加参数：`-ExecutionPolicy Bypass -File "C:\Users\A\.openclaw\workspace\aios\agent_system\start_memory_server.ps1"`
6. 完成

### 快速创建命令（管理员权限）

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-ExecutionPolicy Bypass -File "C:\Users\A\.openclaw\workspace\aios\agent_system\start_memory_server.ps1"'
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "AIOS Memory Server" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "自动启动 AIOS Memory Server"
```

### 验证任务

```powershell
Get-ScheduledTask -TaskName "AIOS Memory Server"
```

### 手动触发测试

```powershell
Start-ScheduledTask -TaskName "AIOS Memory Server"
```

### 删除任务（如需要）

```powershell
Unregister-ScheduledTask -TaskName "AIOS Memory Server" -Confirm:$false
```

---

## 方法 2：启动文件夹（简单但不推荐）

### 创建快捷方式

1. 右键 `start_memory_server.ps1` → 创建快捷方式
2. 右键快捷方式 → 属性
3. 目标改为：
   ```
   powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\A\.openclaw\workspace\aios\agent_system\start_memory_server.ps1"
   ```
4. 将快捷方式复制到启动文件夹：
   - 按 `Win + R` → 输入 `shell:startup`
   - 粘贴快捷方式

**缺点：** 需要用户登录后才启动，不如任务计划程序可靠。

---

## 方法 3：Windows 服务（最可靠，但复杂）

使用 NSSM (Non-Sucking Service Manager) 将 Memory Server 注册为 Windows 服务。

### 安装 NSSM

```powershell
# 使用 Chocolatey
choco install nssm

# 或手动下载
# https://nssm.cc/download
```

### 创建服务

```powershell
nssm install "AIOS Memory Server" "C:\Program Files\Python312\python.exe" "-X utf8 memory_server.py"
nssm set "AIOS Memory Server" AppDirectory "C:\Users\A\.openclaw\workspace\aios\agent_system"
nssm set "AIOS Memory Server" AppEnvironmentExtra "PYTHONUTF8=1" "PYTHONIOENCODING=utf-8"
nssm set "AIOS Memory Server" DisplayName "AIOS Memory Server"
nssm set "AIOS Memory Server" Description "AIOS 记忆服务器 - 提供语义搜索和记忆检索"
nssm set "AIOS Memory Server" Start SERVICE_AUTO_START
nssm start "AIOS Memory Server"
```

### 管理服务

```powershell
# 启动
nssm start "AIOS Memory Server"

# 停止
nssm stop "AIOS Memory Server"

# 重启
nssm restart "AIOS Memory Server"

# 查看状态
nssm status "AIOS Memory Server"

# 删除服务
nssm remove "AIOS Memory Server" confirm
```

---

## 推荐方案

**当前阶段：** 使用**方法 1（任务计划程序）**

**原因：**
- ✅ 系统启动时自动运行
- ✅ 不需要用户登录
- ✅ 可靠性高
- ✅ 易于管理和调试
- ✅ 不需要额外工具

**观察期后：** 如果需要更高可靠性，可升级到**方法 3（Windows 服务）**

---

## 验证自动启动

重启电脑后，检查 Memory Server 是否自动启动：

```powershell
# 检查进程
Get-Process -Name python | Where-Object { $_.CommandLine -like "*memory_server.py*" }

# 检查端口
Test-NetConnection -ComputerName 127.0.0.1 -Port 7788

# 检查 API
Invoke-WebRequest -Uri "http://127.0.0.1:7788/status"
```

---

## 故障排查

### 任务未启动

1. 检查任务计划程序中的任务状态
2. 查看任务历史记录（右键任务 → 属性 → 历史记录）
3. 手动运行脚本测试：
   ```powershell
   powershell.exe -ExecutionPolicy Bypass -File "C:\Users\A\.openclaw\workspace\aios\agent_system\start_memory_server.ps1"
   ```

### 端口被占用

```powershell
# 查看占用 7788 端口的进程
netstat -ano | findstr :7788

# 结束进程（替换 <PID>）
taskkill /PID <PID> /F
```

### 权限问题

确保任务以管理员权限运行（任务属性 → 常规 → 使用最高权限运行）

---

## 当前状态

- ✅ 启动脚本已创建：`start_memory_server.ps1`
- ⏳ 待配置：任务计划程序自动启动
- ⏳ 待验证：重启后自动启动

**下一步：** 执行上面的"快速创建命令"配置任务计划程序。
