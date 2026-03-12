# RPA + 视觉理解系统 - 使用指南

> **⚠️ STATUS: PROTOTYPE ONLY - NOT INTEGRATED**
> 
> - 观察期内封存，不接入太极OS主链
> - 不创建 RPA Agent / Skill
> - 不接心跳、不接自动决策
> - 观察期后需通过安全审查才能集成
>
> **RISK LEVEL: HIGH**  
> RPA + OCR 可能点错、输错、操作错对象。  
> 集成前必须：dry-run、审计日志、人工确认点、禁止高风险操作。

---

## 功能

- **RPA 自动化**：鼠标、键盘、窗口操作
- **视觉理解**：OCR 文字识别、文本定位
- **工作流引擎**：可配置的自动化流程

## 依赖安装

### 1. Python 库

```bash
pip install pyautogui pytesseract pillow opencv-python
```

### 2. Tesseract OCR（免费）

**Windows：**
1. 下载：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装到默认路径：`C:\Program Files\Tesseract-OCR\`
3. 添加中文语言包：
   - 下载 `chi_sim.traineddata`：https://github.com/tesseract-ocr/tessdata
   - 放到 `C:\Program Files\Tesseract-OCR\tessdata\`

**可选：PaddleOCR（更准确）**

```bash
pip install paddleocr
```

## 快速开始

### 示例 1：读取屏幕文本

```python
from rpa_vision import RPAController

rpa = RPAController()

# 读取全屏文本
text = rpa.read_screen()
print(text)

# 读取指定区域（x, y, width, height）
text = rpa.read_screen(region=(100, 100, 500, 300))
print(text)
```

### 示例 2：查找并点击文本

```python
from rpa_vision import RPAController

rpa = RPAController()

# 查找"确定"按钮并点击
if rpa.find_and_click("确定"):
    print("点击成功")
else:
    print("未找到文本")
```

### 示例 3：等待文本出现

```python
from rpa_vision import RPAController

rpa = RPAController()

# 等待"加载完成"出现（最多 10 秒）
if rpa.wait_for_text("加载完成", timeout=10):
    print("加载完成")
else:
    print("超时")
```

### 示例 4：执行工作流

```python
from rpa_vision import RPAController

rpa = RPAController()

workflow = [
    # 打开运行对话框
    {'action': 'hotkey', 'keys': ['win', 'r']},
    {'action': 'wait', 'seconds': 0.5},
    
    # 输入命令
    {'action': 'type_text', 'text': 'notepad'},
    {'action': 'press_key', 'key': 'enter'},
    {'action': 'wait', 'seconds': 1},
    
    # 输入文本
    {'action': 'type_text', 'text': 'Hello World!'},
    
    # 截图
    {'action': 'screenshot', 'save_path': 'result.png'},
    
    # 读取屏幕
    {'action': 'read_screen'},
    
    # 关闭窗口
    {'action': 'hotkey', 'keys': ['alt', 'f4']},
    {'action': 'wait', 'seconds': 0.5},
    {'action': 'find_and_click', 'target_text': '不保存'},
]

rpa.execute_workflow(workflow)
```

## 工作流动作

### 鼠标操作

```python
{'action': 'move_to', 'x': 100, 'y': 200, 'duration': 0.5}
{'action': 'click', 'x': 100, 'y': 200, 'button': 'left', 'clicks': 1}
{'action': 'click', 'button': 'right'}  # 当前位置右键
```

### 键盘操作

```python
{'action': 'type_text', 'text': 'Hello', 'interval': 0.1}
{'action': 'press_key', 'key': 'enter'}
{'action': 'hotkey', 'keys': ['ctrl', 'c']}
```

### 视觉操作

```python
{'action': 'screenshot', 'region': (0, 0, 800, 600), 'save_path': 'screen.png'}
{'action': 'read_screen', 'region': (100, 100, 500, 300), 'lang': 'chi_sim+eng'}
{'action': 'find_and_click', 'target_text': '确定', 'lang': 'chi_sim+eng'}
{'action': 'wait_for_text', 'target_text': '完成', 'timeout': 10, 'interval': 1.0}
```

### 等待

```python
{'action': 'wait', 'seconds': 2}
```

## 实际应用场景

### 1. 自动填表

```python
workflow = [
    {'action': 'find_and_click', 'target_text': '姓名'},
    {'action': 'type_text', 'text': '张三'},
    {'action': 'press_key', 'key': 'tab'},
    {'action': 'type_text', 'text': '18888888888'},
    {'action': 'find_and_click', 'target_text': '提交'},
]
```

### 2. 自动登录

```python
workflow = [
    {'action': 'find_and_click', 'target_text': '用户名'},
    {'action': 'type_text', 'text': 'admin'},
    {'action': 'press_key', 'key': 'tab'},
    {'action': 'type_text', 'text': 'password123'},
    {'action': 'find_and_click', 'target_text': '登录'},
    {'action': 'wait_for_text', 'target_text': '欢迎', 'timeout': 5},
]
```

### 3. 数据提取

```python
rpa = RPAController()

# 截图
rpa.screenshot(region=(100, 100, 800, 600), save_path='data.png')

# 提取文本
text = rpa.read_screen(region=(100, 100, 800, 600))

# 保存到文件
with open('extracted_data.txt', 'w', encoding='utf-8') as f:
    f.write(text)
```

### 4. 自动化测试

```python
workflow = [
    # 打开应用
    {'action': 'hotkey', 'keys': ['win', 'r']},
    {'action': 'type_text', 'text': 'myapp.exe'},
    {'action': 'press_key', 'key': 'enter'},
    {'action': 'wait', 'seconds': 2},
    
    # 测试功能
    {'action': 'find_and_click', 'target_text': '新建'},
    {'action': 'wait_for_text', 'target_text': '新建成功', 'timeout': 5},
    
    # 截图验证
    {'action': 'screenshot', 'save_path': 'test_result.png'},
    
    # 关闭应用
    {'action': 'hotkey', 'keys': ['alt', 'f4']},
]
```

## 安全设置

- **FAILSAFE**：鼠标移到屏幕左上角可中止（默认开启）
- **PAUSE**：每次操作后暂停 0.5 秒（可调整）
- **日志记录**：所有操作记录到 `rpa_log.jsonl`

## 故障排查

### Tesseract 未找到

```
[ERROR] pytesseract.pytesseract.TesseractNotFoundError
```

**解决：**
1. 确认 Tesseract 已安装
2. 检查路径是否正确（修改 `rpa_vision.py` 中的 `tesseract_paths`）

### OCR 识别不准确

**解决：**
1. 使用 `preprocess_image()` 预处理图像
2. 调整语言参数（`lang='chi_sim+eng'`）
3. 尝试 PaddleOCR（更准确）

### 找不到文本

**解决：**
1. 截图查看实际内容
2. 调整搜索区域
3. 检查文本是否完全匹配（可用 `in` 模糊匹配）

## 进阶用法

### 自定义 OCR 引擎

```python
# 使用 PaddleOCR（更准确）
rpa = RPAController(ocr_engine='paddleocr')
```

### 图像预处理

```python
from rpa_vision import VisualOCR
from PIL import Image

ocr = VisualOCR()
img = Image.open('screenshot.png')

# 预处理
processed = ocr.preprocess_image(img)
processed.save('processed.png')

# 提取文本
text = ocr.extract_text(processed)
```

### 批量处理

```python
import os
from rpa_vision import VisualOCR

ocr = VisualOCR()

for filename in os.listdir('screenshots'):
    if filename.endswith('.png'):
        img = Image.open(f'screenshots/{filename}')
        text = ocr.extract_text(img)
        
        # 保存结果
        with open(f'results/{filename}.txt', 'w', encoding='utf-8') as f:
            f.write(text)
```

## 集成到 AIOS

### 创建 RPA Agent

```python
# agents.json
{
  "name": "RPA_Automator",
  "role": "RPA 自动化执行器",
  "group": "automation",
  "enabled": true,
  "mode": "active",
  "capabilities": ["rpa", "ocr", "workflow"],
  "tools": ["rpa_vision.py"]
}
```

### 创建 Skill

```markdown
# SKILL.md - RPA 自动化

## When to Use
- 需要自动化 GUI 操作
- 需要从屏幕提取文本
- 需要执行重复性任务

## How to Use
1. 定义工作流（JSON 格式）
2. 调用 `rpa_vision.py`
3. 验证执行结果

## Example
```python
from rpa_vision import RPAController

rpa = RPAController()
workflow = [...]
rpa.execute_workflow(workflow)
```
```

## 最佳实践

1. **先测试后自动化** - 手动执行一遍，确认流程
2. **添加等待时间** - 避免操作过快导致失败
3. **使用区域截图** - 提高 OCR 准确率
4. **记录日志** - 便于调试和审计
5. **错误处理** - 添加重试和回滚机制

## 限制

- 依赖屏幕分辨率和窗口位置
- OCR 准确率受图像质量影响
- 不适合需要高精度的场景
- 无法处理动态验证码

## 替代方案

- **API 自动化** - 优先使用 API（更稳定）
- **Selenium** - Web 自动化
- **Playwright** - 现代 Web 自动化
- **UIAutomation** - Windows 原生自动化

---

**版本：** v1.0  
**创建时间：** 2026-03-12  
**维护者：** 小九
