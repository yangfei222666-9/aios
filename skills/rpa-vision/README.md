# RPA Vision - 视觉理解 + 自动化执行

**版本：** v0.1  
**状态：** MVP / 验证中  
**创建时间：** 2026-03-11

## 简介

RPA Vision 是一个基于 OCR + 视觉理解的自动化工具，用于 Windows 应用和网页的自动化操作。

**核心特性：**
- ✅ 免费 OCR（Windows OCR API）
- ✅ 智能元素定位（文本、按钮、输入框）
- ✅ 安全机制（DPI 适配、前台校验、Fail-safe）
- ✅ 调试模式（截图、OCR 结果、动作日志）
- ✅ Dry-run 模式（只识别不执行）

## 快速开始

### 1. 安装依赖

```bash
cd C:\Users\A\.openclaw\workspace\skills\rpa-vision
pip install -r requirements.txt
```

### 2. 运行 Demo

**Demo 1: 网页搜索**
```bash
python examples/search_demo.py
```

**Demo 2: Windows 登录表单**
```bash
python examples/login_demo.py
```

### 3. 基础用法

```python
from main import RPAVision

# 初始化
rpa = RPAVision(debug_mode=True)

# 截图并 OCR
rpa.capture_screen()
rpa.extract_text()

# 查找并点击文本
rpa.click_text("登录")

# 输入文本
rpa.type_text("hello@example.com")

# 等待条件
rpa.wait_for_text("提交成功", timeout=10)
```

## 项目结构

```
rpa-vision/
├── SKILL.md              # Skill 文档
├── README.md             # 本文件
├── requirements.txt      # 依赖
├── main.py               # 主入口
├── capture.py            # 截图模块
├── ocr/                  # OCR 引擎
│   ├── __init__.py
│   ├── base.py           # 基类
│   ├── windows_ocr.py    # Windows OCR API
│   ├── paddle_ocr.py     # PaddleOCR（待实现）
│   └── tesseract_ocr.py  # Tesseract（待实现）
├── vision_parser.py      # 视觉解析器
├── locator.py            # 元素定位器
├── executor.py           # 执行器
├── safety.py             # 安全模块
├── debug.py              # 调试模块
└── examples/             # 示例
    ├── search_demo.py    # 网页搜索
    └── login_demo.py     # 登录表单
```

## 核心能力

### 1. 截图（全屏/窗口/区域）
```python
# 全屏截图
screenshot = rpa.capture_screen()

# 区域截图
screenshot = rpa.capture_screen(region=(100, 100, 800, 600))
```

### 2. OCR 文本提取
```python
# 提取文本
result = rpa.extract_text()
# [{"text": "...", "bbox": (x, y, w, h), "confidence": 0.95}, ...]
```

### 3. 查找文本
```python
# 精确匹配
result = rpa.find_text("登录")

# 模糊匹配
result = rpa.find_text("登录", fuzzy=True, threshold=0.8)
```

### 4. 点击文本
```python
# 点击文本中心
rpa.click_text("确定")

# 点击文本 + 偏移
rpa.click_text("确定", offset=(10, 0))
```

### 5. 输入文本
```python
rpa.type_text("hello@example.com", interval=0.05)
```

### 6. 快捷键
```python
# 单个按键
rpa.press_key("enter")

# 组合键
rpa.hotkey("ctrl", "c")
```

### 7. 等待条件
```python
# 等待文本出现
rpa.wait_for_text("提交成功", timeout=10)

# 等待文本消失
rpa.wait_until_disappear("加载中", timeout=10)
```

### 8. 调试输出
```python
# 启用调试模式
rpa.enable_debug("./debug_output")

# 每次执行会保存：
# - 原始截图
# - OCR 识别结果（JSON）
# - 最终点击位置（标注图）
# - 执行动作日志
```

## OCR 引擎

### Windows OCR API（默认）
- ✅ 系统自带，免费
- ✅ 速度快，依赖轻
- ✅ 适合 UI 文本识别
- ⚠️ 复杂界面识别率一般

### PaddleOCR（待实现）
- ✅ 中文能力强
- ✅ 复杂界面更稳
- ⚠️ 依赖重，安装麻烦

### Tesseract（待实现）
- ✅ 通用成熟
- ✅ 兼容性好
- ⚠️ 中文 UI 识别率一般

## 安全机制

### 1. DPI 缩放处理
自动适配 Windows 125%/150% 缩放，确保坐标准确。

### 2. 前台窗口校验
执行点击前确认目标窗口在前台，避免误操作。

### 3. Fail-safe
鼠标移到左上角或按 Esc 立即中断执行。

### 4. Dry-run 模式
只识别不执行，用于调试和验证。

```python
rpa = RPAVision(dry_run=True)
```

### 5. 调试证据链
每次执行保存完整证据链，便于排错和复盘。

## 限制

- ❌ 不支持游戏自动化
- ❌ 不支持复杂动画界面
- ❌ 不支持反自动化检测绕过
- ⚠️ 需要目标窗口在前台
- ⚠️ 需要稳定的界面布局

## 下一步

- [ ] 完成 2 个 demo 验证
- [ ] 实现 PaddleOCR 引擎
- [ ] 实现 Tesseract 引擎
- [ ] 增加模板匹配能力
- [ ] 增加流程编排
- [ ] 集成到 AIOS Agent 系统

## 维护者

小九 + 珊瑚海

## 许可

MIT License
