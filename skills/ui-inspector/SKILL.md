# UI Inspector Skill

UI 元素检查器，用于获取窗口信息、控件信息、坐标等。

## 触发词

- "检查窗口"
- "获取控件信息"
- "查看UI元素"
- "窗口信息"
- "控件坐标"

## 功能

### 1. 窗口信息
- 窗口标题、进程名、PID
- 窗口位置和大小
- 窗口状态（最大化/最小化/正常）

### 2. 鼠标位置
- 实时显示鼠标坐标
- 鼠标下的窗口信息
- 鼠标下的控件信息

### 3. 截图标注
- 截图并标注坐标
- 标注控件边界
- 导出带坐标的图片

## 使用方法

```powershell
# 获取当前鼠标位置
.\ui-mouse-pos.ps1

# 实时显示鼠标位置（按 Ctrl+C 停止）
.\ui-mouse-pos.ps1 -Live

# 获取窗口信息
.\ui-window-info.ps1 -Title "记事本"

# 获取所有窗口信息
.\ui-window-info.ps1 -All

# 截图并标注坐标
.\ui-screenshot-annotate.ps1 -Output "annotated.png"
```

## 示例

### 获取鼠标位置

```powershell
PS> .\ui-mouse-pos.ps1
鼠标位置: X=1024, Y=768
```

### 实时监控鼠标

```powershell
PS> .\ui-mouse-pos.ps1 -Live
[19:30:45] X=1024, Y=768
[19:30:46] X=1025, Y=769
[19:30:47] X=1026, Y=770
...
```

### 获取窗口信息

```powershell
PS> .\ui-window-info.ps1 -Title "Chrome"
标题: Google Chrome
进程: chrome
PID: 12345
位置: X=100, Y=100
大小: W=1280, H=720
状态: 正常
```

## 脚本文件

### ui-mouse-pos.ps1
获取鼠标位置

### ui-window-info.ps1
获取窗口信息

### ui-screenshot-annotate.ps1
截图并标注

## 依赖

- Windows 10/11
- PowerShell 5.1+
- .NET Framework 4.5+

## 更新日志

- 2026-02-25: 初始版本
