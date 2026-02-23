# 天气爬虫部署文档

## 项目概述

基于 wttr.in API 的天气数据爬虫，支持自动定时采集和数据存储。

## 系统要求

- **操作系统**: Windows 10/11 或 Windows Server 2016+
- **Python**: 3.7 或更高版本
- **权限**: 设置计划任务需要管理员权限

## 依赖说明

### Python 依赖包

```
requests>=2.28.0    # HTTP 请求库
pytest>=7.0.0       # 测试框架（仅开发环境需要）
```

### 安装依赖

```bash
# 方式 1: 使用 pip 直接安装
pip install requests pytest

# 方式 2: 使用虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate
pip install requests pytest
```

## 安装步骤

### 1. 下载项目文件

将以下文件放置在同一目录下：

```
weather_crawler/
├── weather_crawler.py              # 爬虫主程序
├── test_weather_crawler.py         # 测试套件
├── run_weather_crawler.ps1         # 启动脚本
├── setup_weather_task.ps1          # 计划任务设置脚本
└── DEPLOYMENT.md                   # 本文档
```

### 2. 安装 Python 依赖

```powershell
# 进入项目目录
cd C:\path\to\weather_crawler

# 安装依赖
pip install requests
```

### 3. 测试运行

```powershell
# 手动运行一次（默认查询北京）
python weather_crawler.py

# 指定城市
python weather_crawler.py Shanghai
python weather_crawler.py --city Tokyo
```

成功运行后会生成 `weather_data.json` 文件。

### 4. 设置计划任务

```powershell
# 以管理员身份运行 PowerShell
# 右键点击 PowerShell 图标 -> "以管理员身份运行"

# 执行设置脚本
.\setup_weather_task.ps1

# 自定义参数
.\setup_weather_task.ps1 -TaskName "MyWeatherTask" -ExecutionTime "09:30" -City "Shanghai"
```

## 使用说明

### 手动运行

#### 使用 Python 直接运行

```powershell
# 默认查询北京
python weather_crawler.py

# 指定城市（英文）
python weather_crawler.py London

# 指定城市（中文）
python weather_crawler.py 上海

# 使用命名参数
python weather_crawler.py --city "New York"
```

#### 使用 PowerShell 启动脚本

```powershell
# 默认查询北京
.\run_weather_crawler.ps1

# 指定城市
.\run_weather_crawler.ps1 -City "Shanghai"

# 指定虚拟环境路径
.\run_weather_crawler.ps1 -City "Tokyo" -VenvPath "venv"
```

### 计划任务管理

```powershell
# 查看任务状态
Get-ScheduledTask -TaskName "WeatherCrawler_Daily"

# 查看任务详细信息
Get-ScheduledTaskInfo -TaskName "WeatherCrawler_Daily"

# 手动运行任务
Start-ScheduledTask -TaskName "WeatherCrawler_Daily"

# 禁用任务
Disable-ScheduledTask -TaskName "WeatherCrawler_Daily"

# 启用任务
Enable-ScheduledTask -TaskName "WeatherCrawler_Daily"

# 删除任务
Unregister-ScheduledTask -TaskName "WeatherCrawler_Daily" -Confirm:$false
```

### 查看日志

```powershell
# 查看最新日志
Get-Content weather_crawler.log -Tail 50

# 实时监控日志
Get-Content weather_crawler.log -Wait

# 在记事本中打开
notepad weather_crawler.log
```

### 查看数据

```powershell
# 查看 JSON 数据
Get-Content weather_data.json | ConvertFrom-Json | Format-List

# 查看最新一条记录
$data = Get-Content weather_data.json | ConvertFrom-Json
$data[-1]
```

## 配置说明

### 修改执行时间

编辑 `setup_weather_task.ps1` 中的参数：

```powershell
.\setup_weather_task.ps1 -ExecutionTime "06:00"  # 改为早上 6 点
```

### 修改查询城市

编辑 `run_weather_crawler.ps1` 中的默认城市：

```powershell
param(
    [string]$City = "Shanghai",  # 改为上海
    ...
)
```

或在设置任务时指定：

```powershell
.\setup_weather_task.ps1 -City "Shanghai"
```

### 修改重试机制

编辑 `weather_crawler.py` 中的常量：

```python
MAX_RETRIES = 3               # 最大重试次数
REQUEST_TIMEOUT = 15          # 请求超时时间（秒）
```

编辑 `setup_weather_task.ps1` 中的设置：

```powershell
$Settings = New-ScheduledTaskSettingsSet `
    -RestartCount 3 `                          # 失败重试次数
    -RestartInterval (New-TimeSpan -Minutes 10) # 重试间隔
```

## 故障排查

### 问题 1: 找不到 Python

**症状**: 运行脚本时提示 "未找到 Python 解释器"

**解决方案**:
1. 确认 Python 已安装: `python --version`
2. 将 Python 添加到系统 PATH
3. 或创建虚拟环境并在脚本中指定路径

### 问题 2: 网络连接失败

**症状**: 日志显示 "网络连接失败" 或 "请求超时"

**解决方案**:
1. 检查网络连接: `ping wttr.in`
2. 检查防火墙设置
3. 尝试使用代理（修改 `weather_crawler.py` 添加代理配置）
4. 增加超时时间: 修改 `REQUEST_TIMEOUT` 常量

### 问题 3: 计划任务未执行

**症状**: 到了设定时间但任务没有运行

**解决方案**:
1. 检查任务状态: `Get-ScheduledTask -TaskName "WeatherCrawler_Daily"`
2. 查看任务历史: 打开"任务计划程序" -> 查看任务历史记录
3. 确认计算机在设定时间处于开机状态
4. 检查任务设置中的"条件"选项卡

### 问题 4: 权限错误

**症状**: 无法创建日志文件或保存数据

**解决方案**:
1. 确认对项目目录有写入权限
2. 以管理员身份运行脚本
3. 修改文件保存路径到有权限的目录

### 问题 5: 数据解析失败

**症状**: 日志显示 "数据解析失败" 或 "缺少字段"

**解决方案**:
1. 检查城市名称是否正确
2. 尝试使用英文城市名
3. 查看 API 返回的原始数据（添加调试日志）
4. 检查 wttr.in API 是否有变更

### 问题 6: 依赖包缺失

**症状**: 运行时提示 "No module named 'requests'"

**解决方案**:
```powershell
# 安装缺失的包
pip install requests

# 如果使用虚拟环境，确保已激活
venv\Scripts\activate
pip install requests
```

### 问题 7: PowerShell 执行策略限制

**症状**: 运行脚本时提示 "无法加载，因为在此系统上禁止运行脚本"

**解决方案**:
```powershell
# 临时允许（仅当前会话）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 永久允许（需要管理员权限）
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 测试

### 运行单元测试

```powershell
# 运行所有测试
pytest test_weather_crawler.py -v

# 运行特定测试类
pytest test_weather_crawler.py::TestFetchWeatherJson -v

# 查看测试覆盖率
pytest test_weather_crawler.py --cov=weather_crawler --cov-report=html
```

### 手动测试流程

1. **测试爬虫功能**:
   ```powershell
   python weather_crawler.py Beijing
   ```
   检查是否生成 `weather_data.json`

2. **测试启动脚本**:
   ```powershell
   .\run_weather_crawler.ps1 -City "Shanghai"
   ```
   检查是否生成 `weather_crawler.log`

3. **测试计划任务**:
   ```powershell
   # 创建任务
   .\setup_weather_task.ps1
   
   # 手动触发
   Start-ScheduledTask -TaskName "WeatherCrawler_Daily"
   
   # 检查结果
   Get-ScheduledTaskInfo -TaskName "WeatherCrawler_Daily"
   ```

## 维护建议

1. **定期检查日志**: 每周查看一次日志文件，确认任务正常执行
2. **清理旧数据**: 定期归档或清理 `weather_data.json` 中的历史数据
3. **更新依赖**: 定期更新 Python 依赖包: `pip install --upgrade requests`
4. **备份数据**: 定期备份 `weather_data.json` 文件
5. **监控磁盘空间**: 确保日志和数据文件不会占满磁盘

## 高级配置

### 配置多个城市

创建多个计划任务，每个任务查询不同城市：

```powershell
.\setup_weather_task.ps1 -TaskName "Weather_Beijing" -City "Beijing" -ExecutionTime "08:00"
.\setup_weather_task.ps1 -TaskName "Weather_Shanghai" -City "Shanghai" -ExecutionTime "08:05"
.\setup_weather_task.ps1 -TaskName "Weather_Guangzhou" -City "Guangzhou" -ExecutionTime "08:10"
```

### 配置邮件通知

修改 `run_weather_crawler.ps1`，在 `catch` 块中添加邮件发送代码：

```powershell
catch {
    # 发送邮件通知
    Send-MailMessage `
        -From "crawler@example.com" `
        -To "admin@example.com" `
        -Subject "天气爬虫执行失败" `
        -Body $ErrorMsg `
        -SmtpServer "smtp.example.com"
}
```

### 数据库存储

修改 `weather_crawler.py`，将数据保存到数据库而非 JSON 文件。

## 联系支持

如遇到其他问题，请检查：
- wttr.in API 文档: https://github.com/chubin/wttr.in
- Python requests 文档: https://requests.readthedocs.io/
- Windows 任务计划程序文档: https://docs.microsoft.com/en-us/windows/win32/taskschd/
