# UI Skills 新增说明

## 新增 Skills

### 1. ui-automation
**路径：** `skills/ui-automation/`

**功能：**
- 鼠标操作（点击、双击、拖拽）
- 键盘操作（输入文本、按键、组合键）
- 窗口操作（激活、最大化、关闭）
- 截图功能

**核心脚本：**
- `ui-click.ps1` - 鼠标点击
- `ui-type.ps1` - 键盘输入
- `ui-windows.ps1` - 窗口管理
- `ui_automation.py` - Python 包装器

**使用场景：**
- 自动填写表单
- 批量处理窗口
- UI 测试自动化
- 重复性操作自动化

### 2. ui-inspector
**路径：** `skills/ui-inspector/`

**功能：**
- 获取鼠标位置
- 实时监控鼠标
- 获取窗口信息
- 截图标注

**核心脚本：**
- `ui-mouse-pos.ps1` - 鼠标位置
- `ui-window-info.ps1` - 窗口信息
- `ui-screenshot-annotate.ps1` - 截图标注

**使用场景：**
- UI 调试
- 坐标定位
- 窗口信息查询
- 自动化脚本开发辅助

## 集成到 AIOS

### Agent 配置建议

可以创建一个 **UI Automation Agent**，专门处理 UI 相关任务：

```json
{
  "name": "ui-automation-agent",
  "role": "UI 自动化专家",
  "goal": "执行 Windows UI 自动化任务",
  "backstory": "精通 Windows UI 自动化，能够模拟鼠标键盘操作，处理窗口管理任务",
  "tools": [
    "ui-automation",
    "ui-inspector",
    "screenshot"
  ],
  "model": "claude-sonnet-4-6",
  "thinking": "off",
  "timeout": 60
}
```

### 使用示例

**场景 1: 自动填写表单**
```
用户: 帮我在记事本里输入"Hello World"

Agent:
1. 使用 ui-windows.ps1 查找记事本窗口
2. 使用 ui-click.ps1 激活窗口
3. 使用 ui-type.ps1 输入文本
```

**场景 2: 批量截图**
```
用户: 截取所有打开的浏览器窗口

Agent:
1. 使用 ui-windows.ps1 获取所有浏览器窗口
2. 逐个激活窗口
3. 使用 ui-screenshot.ps1 截图
4. 保存到指定目录
```

**场景 3: UI 调试**
```
用户: 告诉我当前鼠标位置

Agent:
1. 使用 ui-mouse-pos.ps1 获取坐标
2. 返回 X, Y 坐标
```

## 下一步计划

### 短期（1-2天）
- [ ] 完善 ui-automation 的所有脚本
- [ ] 添加更多示例
- [ ] 测试所有功能

### 中期（1周）
- [ ] 创建 UI Automation Agent
- [ ] 集成到 AIOS Agent System
- [ ] 添加错误处理和重试机制

### 长期（1个月）
- [ ] 支持更多 UI 框架（WPF、UWP）
- [ ] 添加 OCR 识别功能
- [ ] 支持图像识别定位

## 注意事项

1. **权限要求**：某些操作需要管理员权限
2. **稳定性**：UI 自动化依赖窗口状态，建议添加重试机制
3. **安全性**：避免自动化涉及敏感信息的操作
4. **兼容性**：目前仅支持 Windows 10/11

## 测试清单

- [ ] ui-click.ps1 - 点击功能
- [ ] ui-type.ps1 - 输入功能
- [ ] ui-windows.ps1 - 窗口列表
- [ ] ui-mouse-pos.ps1 - 鼠标位置
- [ ] ui_automation.py - Python 包装器
- [ ] 集成测试 - 完整场景

## 更新日志

- 2026-02-25: 创建 ui-automation 和 ui-inspector skills
