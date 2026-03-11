# RPA Vision - 视觉理解 + 自动化执行

**版本：** v0.1  
**状态：** MVP / 验证中  
**创建时间：** 2026-03-11

## 能力定义

通过 OCR + 视觉理解实现 Windows 应用和网页的自动化操作。

**核心能力（8 个）：**
1. 截图（全屏/窗口/区域）
2. OCR 文本提取（返回文字 + bbox 坐标）
3. 查找文本（find_text）
4. 点击文本（click_text）
5. 输入文本（type_text）
6. 快捷键（hotkey）
7. 等待条件（wait_for_text）
8. 调试输出（截图、OCR 结果、动作日志）

## 使用场景

- ✅ Windows 应用自动化（登录、表单填写、按钮点击）
- ✅ 网页自动化（搜索、导航、数据提取）
- ❌ 游戏自动化（v0 不支持）

## OCR 引擎优先级

1. **Windows OCR API**（默认）- 系统自带，免费，速度快
2. **PaddleOCR**（fallback）- 中文能力强，复杂界面更稳
3. **Tesseract**（兜底）- 通用成熟，兼容性好

## 定位策略

1. **主路径：** OCR 定位文字 + 相对位置推断
2. **辅路径：** 模板匹配找图标/无文字按钮
3. **兜底：** 坐标点击

## 安全机制

- ✅ DPI 缩放处理（125%/150% 缩放适配）
- ✅ 前台窗口校验（执行前确认目标窗口在前台）
- ✅ Fail-safe（鼠标移到左上角或按 Esc 中断）
- ✅ Dry-run 模式（只识别不执行）
- ✅ 调试证据链（截图、OCR 结果、动作日志）

## 使用方式

### 基础用法

```python
from rpa_vision import RPAVision

rpa = RPAVision()

# 截图并 OCR
result = rpa.capture_and_ocr()

# 查找文本
bbox = rpa.find_text("登录")

# 点击文本
rpa.click_text("确定")

# 输入文本
rpa.type_text("hello@example.com")

# 等待条件
rpa.wait_for_text("提交成功", timeout=10)
```

### Demo 1：网页搜索

```python
from rpa_vision import RPAVision

rpa = RPAVision()

# 1. 打开浏览器（假设已打开）
# 2. 定位搜索框
rpa.click_text("搜索")

# 3. 输入关键词
rpa.type_text("OpenClaw")

# 4. 回车
rpa.press_key("enter")

# 5. 等待结果页
rpa.wait_for_text("搜索结果", timeout=10)
```

### Demo 2：Windows 登录表单

```python
from rpa_vision import RPAVision

rpa = RPAVision()

# 1. 找"用户名"标签
user_label = rpa.find_text("用户名")

# 2. 找相邻输入框
input_box = rpa.find_nearest_input(user_label)

# 3. 输入用户名
rpa.click(input_box)
rpa.type_text("admin")

# 4. 输入密码
rpa.click_text("密码")
rpa.type_text("password123")

# 5. 点击登录
rpa.click_text("登录")

# 6. 等待结果
rpa.wait_for_text("登录成功", timeout=10)
```

## API 参考

### 识别类

- `capture_screen(region=None)` - 截图
- `extract_text(image=None)` - OCR 提取文本
- `find_text(target, fuzzy=False)` - 查找文本
- `find_nearest_input(label_bbox)` - 查找最近的输入框
- `find_button(name)` - 查找按钮

### 执行类

- `click(x, y)` - 点击坐标
- `click_text(target, offset=(0,0))` - 点击文本
- `type_text(text, interval=0.05)` - 输入文本
- `press_key(key)` - 按键
- `hotkey(*keys)` - 快捷键
- `drag(start, end)` - 拖拽

### 流程类

- `wait_for_text(target, timeout=10)` - 等待文本出现
- `wait_until_disappear(target, timeout=10)` - 等待文本消失
- `run_step(step_config)` - 执行步骤配置

### 调试类

- `enable_debug(output_dir)` - 启用调试模式
- `dry_run(enabled=True)` - 启用 Dry-run 模式
- `get_last_screenshot()` - 获取最后一次截图
- `get_last_ocr_result()` - 获取最后一次 OCR 结果

## 依赖

```
pyautogui>=0.9.54
mss>=9.0.1
pillow>=10.0.0
pywin32>=306  # Windows OCR API
paddleocr>=2.7.0  # 可选
pytesseract>=0.3.10  # 可选
opencv-python>=4.8.0  # 模板匹配
```

## 安装

```bash
cd C:\Users\A\.openclaw\workspace\skills\rpa-vision
pip install -r requirements.txt
```

## 调试

启用调试模式后，每次执行会保存：
- 原始截图
- OCR 识别结果（JSON）
- 最终点击位置（标注图）
- 执行动作日志

```python
rpa = RPAVision()
rpa.enable_debug("./debug_output")
```

## 限制

- ❌ 不支持游戏自动化
- ❌ 不支持复杂动画界面
- ❌ 不支持反自动化检测绕过
- ⚠️ 需要目标窗口在前台
- ⚠️ 需要稳定的界面布局

## 下一步

- [ ] 完成 2 个 demo 验证
- [ ] 补充模板匹配能力
- [ ] 增加流程编排
- [ ] 集成到 AIOS Agent 系统

## 维护者

小九 + 珊瑚海

---

**核心原则：** 先把截图 → OCR → 定位 → 执行 → 校验 → 调试证据链打通，再扩展复杂功能。
