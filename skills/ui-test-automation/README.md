# UI Test Automation - 快速开始

## 安装依赖

```bash
pip install pyyaml
```

## 运行示例测试

### 1. 记事本测试

```bash
cd skills/ui-test-automation
python ui_test_runner.py examples/notepad_test.yaml
```

**预期结果：**
- ✅ 打开记事本
- ✅ 输入文本
- ✅ 保存文件
- ✅ 验证文件存在
- ✅ 验证文件内容
- ✅ 生成测试报告

### 2. 查看测试报告

```bash
# 报告会自动生成在当前目录
start test_report.html
```

## 创建自己的测试

### 步骤 1: 创建测试文件

创建 `my_test.yaml`:

```yaml
name: "我的测试"
description: "测试描述"

steps:
  - action: launch
    app: notepad.exe
    wait: 2
  
  - action: type
    text: "Hello"
    wait: 1

assertions:
  - type: window_exists
    title: "记事本"
```

### 步骤 2: 运行测试

```bash
python ui_test_runner.py my_test.yaml
```

### 步骤 3: 查看报告

```bash
start test_report.html
```

## 支持的动作

### launch - 启动应用
```yaml
- action: launch
  app: notepad.exe
  args: "file.txt"  # 可选
  wait: 2
```

### click - 点击
```yaml
- action: click
  x: 100
  y: 200
  window: "窗口标题"  # 可选
  wait: 0.5
```

### type - 输入文本
```yaml
- action: type
  text: "Hello World"
  press_enter: true  # 可选
  wait: 1
```

### hotkey - 组合键
```yaml
- action: hotkey
  keys: "Ctrl+S"
  wait: 1
```

### wait - 等待
```yaml
- action: wait
  seconds: 2
```

### screenshot - 截图
```yaml
- action: screenshot
  output: "screenshot.png"
  window: "窗口标题"  # 可选
  wait: 0.5
```

## 支持的断言

### file_exists - 文件存在
```yaml
- type: file_exists
  path: "test.txt"
```

### file_contains - 文件包含文本
```yaml
- type: file_contains
  path: "test.txt"
  text: "Hello"
```

### file_size - 文件大小
```yaml
- type: file_size
  path: "test.txt"
  min: 10
```

### window_exists - 窗口存在
```yaml
- type: window_exists
  title: "记事本"
```

## 高级功能

### 失败重试

```bash
python ui_test_runner.py my_test.yaml --retry 3
```

### 批量运行

```bash
# 运行目录下所有测试
python ui_test_runner.py examples/
```

### 并行执行

```bash
python ui_test_runner.py examples/ --parallel 4
```

## 故障排除

### 问题：测试失败
1. 检查应用是否正确启动
2. 增加等待时间
3. 查看截图（如果有）
4. 查看测试报告

### 问题：找不到窗口
1. 确认窗口标题正确
2. 增加启动后的等待时间
3. 使用 `ui-windows.ps1` 查看所有窗口

### 问题：点击无效
1. 确认坐标正确
2. 确认窗口在前台
3. 增加点击前的等待时间

## 最佳实践

1. **合理设置等待时间**：不要太快也不要太慢
2. **添加断言**：验证每个关键步骤
3. **清理环境**：使用 setup 和 teardown
4. **截图证据**：关键步骤截图
5. **失败重试**：对于不稳定的测试

## 示例测试用例

查看 `examples/` 目录下的示例：
- `notepad_test.yaml` - 记事本测试
- `calculator_test.yaml` - 计算器测试（待添加）
- `browser_test.yaml` - 浏览器测试（待添加）

## 集成到 AIOS

### 创建测试 Agent

```json
{
  "name": "ui-test-agent",
  "role": "UI 测试工程师",
  "goal": "执行 UI 自动化测试",
  "tools": ["ui-test-automation", "ui-automation", "ui-inspector"]
}
```

### 使用 Agent 运行测试

```
用户: 运行记事本测试

Agent:
1. 加载测试用例
2. 执行测试步骤
3. 验证断言
4. 生成报告
5. 返回结果
```

## 更新日志

- 2026-02-25: 初始版本
  - 支持基础动作（launch, click, type, hotkey）
  - 支持基础断言（file_exists, file_contains, file_size）
  - 生成 HTML 测试报告
