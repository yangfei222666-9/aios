# UI Automation Skill

Windows UI 自动化工具，支持鼠标点击、键盘输入、窗口操作等。

## 触发词

- "点击按钮"
- "输入文字"
- "打开窗口"
- "关闭窗口"
- "最大化窗口"
- "UI 自动化"
- "模拟点击"
- "模拟输入"

## 功能

### 1. 鼠标操作
- 移动鼠标到指定坐标
- 左键/右键/中键点击
- 双击
- 拖拽

### 2. 键盘操作
- 输入文本
- 按键（Enter、Tab、Esc 等）
- 组合键（Ctrl+C、Alt+Tab 等）

### 3. 窗口操作
- 获取窗口列表
- 激活窗口
- 最大化/最小化/关闭窗口
- 移动/调整窗口大小

### 4. 截图
- 全屏截图
- 窗口截图
- 区域截图

## 使用方法

### 基础命令

```powershell
# 点击坐标 (100, 200)
.\ui-click.ps1 -X 100 -Y 200

# 输入文本
.\ui-type.ps1 -Text "Hello World"

# 按键
.\ui-press.ps1 -Key "Enter"

# 组合键
.\ui-hotkey.ps1 -Keys "Ctrl+C"

# 获取窗口列表
.\ui-windows.ps1

# 激活窗口
.\ui-activate.ps1 -Title "记事本"

# 截图
.\ui-screenshot.ps1 -Output "screenshot.png"
```

### 高级用法

```powershell
# 点击窗口中的按钮（相对坐标）
.\ui-click.ps1 -Window "记事本" -X 50 -Y 30

# 输入文本并按回车
.\ui-type.ps1 -Text "Hello" -PressEnter

# 拖拽
.\ui-drag.ps1 -FromX 100 -FromY 100 -ToX 200 -ToY 200

# 等待窗口出现
.\ui-wait.ps1 -Title "保存" -Timeout 10
```

## 示例场景

### 场景 1: 自动填写表单

```powershell
# 激活浏览器窗口
.\ui-activate.ps1 -Title "Chrome"

# 点击输入框
.\ui-click.ps1 -X 300 -Y 200

# 输入用户名
.\ui-type.ps1 -Text "username"

# Tab 到密码框
.\ui-press.ps1 -Key "Tab"

# 输入密码
.\ui-type.ps1 -Text "password"

# 点击登录按钮
.\ui-click.ps1 -X 300 -Y 300
```

### 场景 2: 批量处理窗口

```powershell
# 获取所有记事本窗口
$windows = .\ui-windows.ps1 -Filter "记事本"

# 逐个关闭
foreach ($win in $windows) {
    .\ui-activate.ps1 -Title $win.Title
    .\ui-hotkey.ps1 -Keys "Alt+F4"
    Start-Sleep -Milliseconds 500
}
```

### 场景 3: 截图并保存

```powershell
# 激活窗口
.\ui-activate.ps1 -Title "计算器"

# 等待窗口激活
Start-Sleep -Milliseconds 500

# 截图
.\ui-screenshot.ps1 -Window "计算器" -Output "calculator.png"
```

## 脚本文件

### ui-click.ps1
鼠标点击操作

### ui-type.ps1
键盘输入操作

### ui-press.ps1
按键操作

### ui-hotkey.ps1
组合键操作

### ui-windows.ps1
窗口管理

### ui-activate.ps1
激活窗口

### ui-screenshot.ps1
截图工具

### ui-drag.ps1
拖拽操作

### ui-wait.ps1
等待窗口

## 注意事项

1. **权限要求**：某些操作需要管理员权限
2. **坐标系统**：使用屏幕绝对坐标（左上角为 0,0）
3. **窗口标题**：支持部分匹配（模糊搜索）
4. **延迟控制**：操作之间建议加延迟（100-500ms）
5. **错误处理**：操作失败会返回错误信息

## 依赖

- Windows 10/11
- PowerShell 5.1+
- .NET Framework 4.5+

## 安全提示

- 不要在生产环境中使用未经测试的自动化脚本
- 避免自动化涉及敏感信息的操作
- 建议在虚拟机或测试环境中先验证

## 故障排除

### 问题：点击无效
- 检查坐标是否正确
- 确认窗口是否在前台
- 尝试增加延迟

### 问题：输入文本失败
- 确认输入框已获得焦点
- 检查输入法状态
- 尝试先点击输入框

### 问题：窗口找不到
- 检查窗口标题是否正确
- 使用 `ui-windows.ps1` 查看所有窗口
- 尝试部分匹配

## 更新日志

- 2026-02-25: 初始版本
