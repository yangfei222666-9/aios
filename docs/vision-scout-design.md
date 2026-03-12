# 视觉前哨（Vision Scout）设计文档 v1.0

## 定位

给小正（Mac）补一个轻量级视觉理解链路。
只做读屏、定位、识别，不做决策。

## 原则

- 最小可用，先跑通再迭代
- 只上 OCR + 截图解析，不上 YOLO / OmniParser
- 本地可跑、低资源占用
- 只负责读，不负责决策

## 技术选型

| 能力 | 工具 | 说明 |
|------|------|------|
| 截图 | `screencapture`（macOS 自带） | 零依赖 |
| OCR | `PaddleOCR` | 轻量，支持中英文，本地运行 |
| UI 操作 | `pyautogui` | 跨平台，点击/输入/滚动 |
| 坐标定位 | PaddleOCR 返回的 bbox | 文字 → 坐标映射 |

## 最小文件结构

```
rpa/
├── vision_scout.py    # 核心：截图 → OCR → 结构化输出
├── executor.py        # 执行：点击/输入/滚动
├── cache/             # 页面元素缓存
│   └── page_cache.json
└── README.md
```

## 核心流程

```
1. 截图（screencapture / pyautogui.screenshot）
2. OCR 识别（PaddleOCR）
3. 输出结构化 JSON：
   [
     {"text": "确认", "x": 320, "y": 480, "w": 60, "h": 24, "confidence": 0.95},
     {"text": "取消", "x": 420, "y": 480, "w": 60, "h": 24, "confidence": 0.92}
   ]
4. 缓存结果（可选，按窗口标题索引）
5. 执行层根据结构化数据操作
```

## API 设计

### vision_scout.py

```python
def screenshot(region=None) -> str:
    """截图，返回图片路径"""

def ocr(image_path: str) -> list[dict]:
    """OCR 识别，返回 [{text, x, y, w, h, confidence}]"""

def find_text(image_path: str, target: str) -> dict | None:
    """在截图中找到指定文字的位置"""

def scan() -> list[dict]:
    """截图 + OCR 一步到位"""
```

### executor.py

```python
def click(x: int, y: int):
    """点击指定坐标"""

def type_text(text: str):
    """输入文字"""

def click_text(target: str):
    """截图 → 找到文字 → 点击"""
```

## Mac 依赖安装

```bash
pip install paddleocr pyautogui pillow
```

## 使用示例

```python
from rpa.vision_scout import scan, find_text
from rpa.executor import click

# 扫描当前屏幕
elements = scan()
print(elements)

# 找到"确认"按钮并点击
btn = find_text(None, "确认")
if btn:
    click(btn["x"], btn["y"])
```

## 后续扩展（不在 v1 范围内）

- UI 元素类型识别（按钮/输入框/下拉框）
- 页面状态缓存和复用
- 窗口切换和管理
- 更复杂的视觉模型（YOLO / OmniParser）

## 时间线

- Day 1：Mac 安装依赖 + 验证 PaddleOCR 可用
- Day 2：实现 vision_scout.py + executor.py
- Day 3：端到端测试（截图 → OCR → 点击）

---

**版本：** v1.0
**创建时间：** 2026-03-12 23:17
**状态：** 设计完成，待实现
