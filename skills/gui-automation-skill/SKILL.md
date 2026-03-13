# GUI Automation Skill

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** 2026-03-13

---

## 概述

GUI 自动化执行层，支持跨平台桌面应用控制。

**核心能力：**
- 窗口查找与激活
- 鼠标/键盘操作
- 屏幕截图与元素识别
- 应用启动与关闭

**设计原则：**
- 优先真实鼠标流（自然、稳定、可验证）
- 避免生硬映射式执行
- 支持跨平台（Windows/macOS/Linux）

---

## 使用场景

**适用：**
- 桌面应用自动化（打开/关闭应用、点击按钮、输入文本）
- 重复性 GUI 操作（批量处理、定时任务）
- 跨应用工作流（从 A 应用复制数据到 B 应用）

**不适用：**
- Web 自动化（用 `browser` 工具）
- 需要高精度像素级操作的场景
- 需要绕过安全检测的场景

---

## 命令格式

```bash
gui-automation <action> [options]
```

### 可用操作

#### 1. 查找窗口
```bash
gui-automation find-window --title "记事本"
gui-automation find-window --class "Notepad"
gui-automation find-window --pid 12345
```

#### 2. 激活窗口
```bash
gui-automation activate-window --title "记事本"
gui-automation activate-window --handle 0x12345
```

#### 3. 鼠标操作
```bash
# 移动鼠标
gui-automation mouse-move --x 100 --y 200

# 点击
gui-automation mouse-click --x 100 --y 200 --button left
gui-automation mouse-click --x 100 --y 200 --button right --double

# 拖拽
gui-automation mouse-drag --from-x 100 --from-y 200 --to-x 300 --to-y 400
```

#### 4. 键盘操作
```bash
# 输入文本
gui-automation type-text --text "Hello World"

# 按键
gui-automation press-key --key "Enter"
gui-automation press-key --key "Ctrl+C"
gui-automation press-key --key "Alt+F4"
```

#### 5. 截图
```bash
# 全屏截图
gui-automation screenshot --output screenshot.png

# 窗口截图
gui-automation screenshot --window-title "记事本" --output notepad.png

# 区域截图
gui-automation screenshot --region 100,200,300,400 --output region.png
```

#### 6. 应用控制
```bash
# 启动应用
gui-automation launch-app --path "C:\Windows\notepad.exe"
gui-automation launch-app --name "notepad"

# 关闭应用
gui-automation close-app --title "记事本"
gui-automation close-app --pid 12345
```

---

## 配置文件

`gui-automation-config.json`

```json
{
  "default_delay_ms": 500,
  "mouse_speed": "normal",
  "screenshot_format": "png",
  "apps": {
    "notepad": {
      "path": "C:\\Windows\\notepad.exe",
      "window_title": "记事本"
    },
    "calculator": {
      "path": "C:\\Windows\\System32\\calc.exe",
      "window_title": "计算器"
    }
  }
}
```

---

## 实现方案

### 技术栈选择

**Windows:**
- `pywinauto` - 窗口查找与控制
- `pyautogui` - 鼠标/键盘操作
- `win32gui` - 底层 Windows API

**macOS:**
- `pyautogui` - 跨平台鼠标/键盘
- `AppKit` - 原生窗口控制
- `Quartz` - 截图

**Linux:**
- `pyautogui` - 跨平台鼠标/键盘
- `xdotool` - X11 窗口控制
- `scrot` - 截图

### 核心模块

```
gui-automation/
├── cli.py              # 命令行入口
├── window_manager.py   # 窗口查找与激活
├── mouse_controller.py # 鼠标操作
├── keyboard_controller.py # 键盘操作
├── screenshot.py       # 截图功能
├── app_launcher.py     # 应用启动与关闭
└── config.py           # 配置管理
```

---

## 安全考虑

1. **权限控制**
   - 需要用户明确授权
   - 敏感操作（关闭应用、删除文件）需要二次确认

2. **操作日志**
   - 记录所有 GUI 操作
   - 便于审计和回溯

3. **异常处理**
   - 窗口未找到时优雅降级
   - 操作失败时提供清晰错误信息

4. **速率限制**
   - 避免过快操作导致系统不稳定
   - 默认操作间隔 500ms

---

## 使用示例

### 示例 1：打开记事本并输入文本

```bash
# 1. 启动记事本
gui-automation launch-app --name "notepad"

# 2. 等待窗口出现
sleep 1

# 3. 激活窗口
gui-automation activate-window --title "记事本"

# 4. 输入文本
gui-automation type-text --text "Hello, World!"

# 5. 保存（Ctrl+S）
gui-automation press-key --key "Ctrl+S"
```

### 示例 2：截图并识别元素

```bash
# 1. 截取当前窗口
gui-automation screenshot --window-title "记事本" --output notepad.png

# 2. 使用 OCR 识别文本（需要额外工具）
# 或使用 image 工具分析截图
```

### 示例 3：自动化工作流

```bash
# 1. 打开应用 A
gui-automation launch-app --name "app-a"

# 2. 点击特定位置
gui-automation mouse-click --x 200 --y 300

# 3. 复制内容
gui-automation press-key --key "Ctrl+C"

# 4. 切换到应用 B
gui-automation activate-window --title "App B"

# 5. 粘贴内容
gui-automation press-key --key "Ctrl+V"
```

---

## 开发计划

### Phase 1: 核心功能（MVP）
- [x] 窗口查找与激活
- [x] 基础鼠标操作（移动、点击）
- [x] 基础键盘操作（输入文本、按键）
- [x] 截图功能
- [ ] CLI 实现
- [ ] 配置文件支持

### Phase 2: 增强功能
- [ ] 应用启动与关闭
- [ ] 鼠标拖拽
- [ ] 组合键支持
- [ ] 区域截图
- [ ] 操作录制与回放

### Phase 3: 高级功能
- [ ] 元素识别（OCR/图像识别）
- [ ] 智能等待（等待元素出现）
- [ ] 错误重试机制
- [ ] 跨平台支持完善

---

## 依赖项

```
pyautogui>=0.9.54
pywinauto>=0.6.8  # Windows only
pillow>=10.0.0
```

---

## 故障排查

### 问题 1：窗口未找到
**原因：** 窗口标题不匹配或窗口未激活  
**解决：** 使用 `find-window` 确认窗口标题，或使用部分匹配

### 问题 2：鼠标点击位置不准
**原因：** 屏幕缩放比例影响坐标  
**解决：** 调整坐标或使用相对坐标

### 问题 3：操作过快导致失败
**原因：** 应用响应速度慢  
**解决：** 增加 `default_delay_ms` 或在操作间添加 `sleep`

---

## 最佳实践

1. **操作前先截图** - 便于调试和验证
2. **使用配置文件** - 避免硬编码路径和坐标
3. **添加等待时间** - 确保应用响应完成
4. **记录操作日志** - 便于问题排查
5. **测试多次** - 确保操作稳定性

---

## 参考资料

- [pyautogui 文档](https://pyautogui.readthedocs.io/)
- [pywinauto 文档](https://pywinauto.readthedocs.io/)
- [xdotool 文档](https://www.semicomplete.com/projects/xdotool/)

---

**维护者：** 小九 + 珊瑚海  
**创建日期：** 2026-03-13  
**最后更新：** 2026-03-13