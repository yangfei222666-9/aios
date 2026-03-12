# UIVisionAgent - 太极OS 视觉感知层

## 定位

太极OS 的视觉感知层，负责"看懂界面 + 输出操作"。

**职责边界：**
- ✅ 接收截图 + 任务描述
- ✅ 输出单步操作
- ✅ 返回置信度
- ❌ 不做任务拆解
- ❌ 不做状态管理
- ❌ 不自动执行操作

---

## 接口契约（v1.0）

### 输入

```python
{
    "task_desc": "点击登录按钮",
    "screenshot": Image  # PIL.Image 对象
}
```

### 输出

```python
{
    "status": "ok" | "uncertain",
    "thought": "我看到登录按钮在右上角",
    "action": {
        "type": "click" | "type" | "scroll" | "press",
        "params": {...}
    },
    "confidence": 0.92
}
```

### Action 格式

```python
# click
{"type": "click", "params": {"x": 850, "y": 120}}

# type
{"type": "type", "params": {"text": "username"}}

# scroll
{"type": "scroll", "params": {"direction": "down", "amount": 3}}

# press
{"type": "press", "params": {"key": "enter"}}
```

---

## 架构设计

```
UIVisionAgent
    ├── VisionEngine（可替换）
    │   ├── UITARSEngine（默认）
    │   ├── OSAtlasEngine（备选）
    │   └── OmniParserEngine（备选）
    │
    ├── perceive() - 核心接口
    │   ├── 调用 VisionEngine.infer()
    │   ├── 解析输出
    │   └── 返回 PerceptionResult
    │
    └── ActionExecutor（可选）
        └── execute() - 执行操作（pyautogui）
```

**关键设计：** VisionEngine 是插件，UI-TARS 只是默认实现。

---

## 使用方式

### 基础用法

```python
from ui_vision_agent import UIVisionAgent
from PIL import Image

# 初始化
agent = UIVisionAgent()

# 加载截图
screenshot = Image.open("screenshot.png")

# 感知
result = agent.perceive("点击登录按钮", screenshot)

print(result.to_dict())
```

### 带执行器

```python
from ui_vision_agent import UIVisionAgent, ActionExecutor

agent = UIVisionAgent()
executor = ActionExecutor()

result = agent.perceive("点击登录按钮", screenshot)

if result.status == "ok" and result.confidence >= 0.8:
    exec_result = executor.execute(result.action)
    print(f"执行结果: {exec_result}")
```

### 替换视觉引擎

```python
from ui_vision_agent import UIVisionAgent, VisionEngine

class MyCustomEngine(VisionEngine):
    def infer(self, screenshot, task_desc):
        # 自定义实现
        return "Thought: ...\nAction: click(start_box='(100,200)')"

agent = UIVisionAgent(engine=MyCustomEngine())
```

---

## 与太极OS 集成

```
TaskQueue → Dispatcher → UIVisionAgent.perceive()
                              ↓
                         返回 Action
                              ↓
                    调用方决定是否执行
                              ↓
                    ActionExecutor.execute()
                              ↓
                    记录到 task_executions.jsonl
```

**关键：** UIVisionAgent 只做"感知 + 建议"，执行权在调用方。

---

## 依赖

### 核心依赖
- `Pillow` - 图像处理
- `transformers` - UI-TARS 模型加载
- `torch` - PyTorch

### 可选依赖
- `pyautogui` - 操作执行（如果需要 ActionExecutor）

### 安装

```bash
pip install pillow transformers torch pyautogui
```

---

## 下一步

1. **试跑 UI-TARS 模型** - 验证推理流程
2. **集成到 Dispatcher** - 让 GUI 任务能自动路由到 UIVisionAgent
3. **添加日志记录** - 记录每次感知结果到 `ui_vision_log.jsonl`
4. **性能优化** - 模型常驻内存，避免重复加载

---

**版本：** v1.0  
**最后更新：** 2026-03-12  
**维护者：** 小九 + 珊瑚海
