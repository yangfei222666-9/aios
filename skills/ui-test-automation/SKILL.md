# UI Test Automation Skill

UI 测试自动化框架，支持录制、回放、断言、报告生成。

## 触发词

- "UI 测试"
- "自动化测试"
- "测试用例"
- "回归测试"
- "UI 验证"

## 功能

### 1. 测试用例管理
- 创建测试用例
- 组织测试套件
- 参数化测试
- 数据驱动测试

### 2. 测试执行
- 单个用例执行
- 批量执行
- 并行执行
- 失败重试

### 3. 断言验证
- 窗口存在性
- 元素可见性
- 文本内容
- 截图对比

### 4. 测试报告
- HTML 报告
- JSON 报告
- 截图附件
- 执行日志

## 测试用例格式

### YAML 格式

```yaml
name: "记事本基础测试"
description: "测试记事本的打开、输入、保存功能"
steps:
  - action: launch
    app: notepad.exe
    wait: 2
  
  - action: type
    text: "Hello World"
    wait: 1
  
  - action: hotkey
    keys: "Ctrl+S"
    wait: 1
  
  - action: assert_window
    title: "另存为"
    timeout: 5
  
  - action: type
    text: "test.txt"
    wait: 1
  
  - action: hotkey
    keys: "Alt+S"
    wait: 2
  
  - action: assert_file
    path: "test.txt"
  
  - action: hotkey
    keys: "Alt+F4"
    wait: 1

assertions:
  - type: file_exists
    path: "test.txt"
  - type: file_contains
    path: "test.txt"
    text: "Hello World"
```

### JSON 格式

```json
{
  "name": "计算器测试",
  "description": "测试计算器的加法功能",
  "steps": [
    {
      "action": "launch",
      "app": "calc.exe",
      "wait": 2
    },
    {
      "action": "click",
      "window": "计算器",
      "x": 100,
      "y": 200,
      "wait": 0.5
    },
    {
      "action": "assert_window",
      "title": "计算器"
    }
  ]
}
```

## 使用方法

### 1. 创建测试用例

```powershell
# 从模板创建
.\ui-test-create.ps1 -Name "MyTest" -Template "basic"

# 手动创建
New-Item -Path "tests\my_test.yaml" -ItemType File
```

### 2. 运行测试

```powershell
# 运行单个测试
.\ui-test-run.ps1 -Test "tests\notepad_test.yaml"

# 运行测试套件
.\ui-test-run.ps1 -Suite "tests\smoke_tests"

# 并行运行
.\ui-test-run.ps1 -Suite "tests\all" -Parallel 4

# 失败重试
.\ui-test-run.ps1 -Test "tests\flaky_test.yaml" -Retry 3
```

### 3. 查看报告

```powershell
# 生成 HTML 报告
.\ui-test-report.ps1 -Input "results\latest.json" -Output "report.html"

# 打开报告
Start-Process "report.html"
```

## 测试示例

### 示例 1: 记事本测试

```yaml
name: "记事本完整测试"
description: "测试记事本的所有基础功能"

setup:
  - action: cleanup
    path: "test_*.txt"

steps:
  # 1. 打开记事本
  - action: launch
    app: notepad.exe
    wait: 2
  
  # 2. 输入文本
  - action: type
    text: "Line 1\nLine 2\nLine 3"
    wait: 1
  
  # 3. 保存文件
  - action: hotkey
    keys: "Ctrl+S"
    wait: 1
  
  - action: type
    text: "test_output.txt"
    wait: 0.5
  
  - action: hotkey
    keys: "Alt+S"
    wait: 2
  
  # 4. 关闭记事本
  - action: hotkey
    keys: "Alt+F4"
    wait: 1

assertions:
  - type: file_exists
    path: "test_output.txt"
  
  - type: file_contains
    path: "test_output.txt"
    text: "Line 1"
  
  - type: file_size
    path: "test_output.txt"
    min: 10

teardown:
  - action: cleanup
    path: "test_output.txt"
```

### 示例 2: 计算器测试

```yaml
name: "计算器加法测试"
description: "测试计算器的加法功能"

steps:
  # 1. 打开计算器
  - action: launch
    app: calc.exe
    wait: 3
  
  # 2. 点击数字和运算符
  - action: click_button
    window: "计算器"
    button: "2"
    wait: 0.5
  
  - action: click_button
    window: "计算器"
    button: "+"
    wait: 0.5
  
  - action: click_button
    window: "计算器"
    button: "3"
    wait: 0.5
  
  - action: click_button
    window: "计算器"
    button: "="
    wait: 1
  
  # 3. 截图验证
  - action: screenshot
    window: "计算器"
    output: "calc_result.png"
  
  # 4. 关闭计算器
  - action: hotkey
    keys: "Alt+F4"
    wait: 1

assertions:
  - type: screenshot_contains
    image: "calc_result.png"
    text: "5"
```

### 示例 3: 浏览器测试

```yaml
name: "浏览器导航测试"
description: "测试浏览器的基本导航功能"

steps:
  # 1. 打开浏览器
  - action: launch
    app: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    args: "--new-window"
    wait: 3
  
  # 2. 输入 URL
  - action: hotkey
    keys: "Ctrl+L"
    wait: 0.5
  
  - action: type
    text: "https://www.google.com"
    press_enter: true
    wait: 3
  
  # 3. 等待页面加载
  - action: wait_window
    title: "Google"
    timeout: 10
  
  # 4. 截图
  - action: screenshot
    window: "Google"
    output: "google_homepage.png"
  
  # 5. 关闭浏览器
  - action: hotkey
    keys: "Alt+F4"
    wait: 1

assertions:
  - type: file_exists
    path: "google_homepage.png"
```

## 高级功能

### 1. 参数化测试

```yaml
name: "参数化登录测试"
parameters:
  - username: "user1"
    password: "pass1"
    expected: "success"
  
  - username: "user2"
    password: "wrong"
    expected: "failure"

steps:
  - action: type
    text: "{{username}}"
  
  - action: press
    key: "Tab"
  
  - action: type
    text: "{{password}}"
  
  - action: press
    key: "Enter"
  
  - action: assert_result
    expected: "{{expected}}"
```

### 2. 数据驱动测试

```yaml
name: "数据驱动测试"
data_source: "test_data.csv"

steps:
  - action: type
    text: "{{column1}}"
  
  - action: click
    x: "{{column2}}"
    y: "{{column3}}"
```

### 3. 条件执行

```yaml
steps:
  - action: assert_window
    title: "对话框"
    if_exists: continue
    if_not_exists: skip_next
  
  - action: click
    x: 100
    y: 200
```

## 测试报告示例

### HTML 报告

```html
<!DOCTYPE html>
<html>
<head>
    <title>UI 测试报告</title>
</head>
<body>
    <h1>测试报告</h1>
    <p>执行时间: 2026-02-25 20:15:00</p>
    <p>总用例: 10</p>
    <p>通过: 8</p>
    <p>失败: 2</p>
    <p>成功率: 80%</p>
    
    <h2>测试结果</h2>
    <table>
        <tr>
            <th>用例名称</th>
            <th>状态</th>
            <th>耗时</th>
            <th>截图</th>
        </tr>
        <tr>
            <td>记事本测试</td>
            <td>✅ 通过</td>
            <td>5.2s</td>
            <td><a href="screenshots/test1.png">查看</a></td>
        </tr>
    </table>
</body>
</html>
```

## 脚本文件

### ui-test-run.ps1
测试执行器

### ui-test-create.ps1
测试用例创建器

### ui-test-report.ps1
报告生成器

### ui-test-recorder.ps1
操作录制器

### ui-test-validator.ps1
断言验证器

## 依赖

- Windows 10/11
- PowerShell 5.1+
- .NET Framework 4.5+
- Python 3.8+（可选，用于高级功能）

## 最佳实践

1. **测试隔离**：每个测试用例独立运行
2. **清理环境**：setup 和 teardown 确保环境干净
3. **等待时间**：合理设置等待时间，避免过快或过慢
4. **截图证据**：关键步骤截图，便于调试
5. **失败重试**：对于不稳定的测试，设置重试次数

## 故障排除

### 问题：测试不稳定
- 增加等待时间
- 添加窗口存在性检查
- 使用重试机制

### 问题：断言失败
- 检查截图
- 查看日志
- 手动验证步骤

### 问题：性能慢
- 减少不必要的等待
- 使用并行执行
- 优化测试用例

## 更新日志

- 2026-02-25: 初始版本
