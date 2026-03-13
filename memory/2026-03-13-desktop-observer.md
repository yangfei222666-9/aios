# Session: 2026-03-13 08:41:35 UTC

- **Session Key**: agent:main:main
- **Session ID**: 67589d0c-d81b-41f1-aa6d-9a4c8d3cabbd
- **Source**: telegram

## Conversation Summary

assistant: 对，这个方向更靠谱。我现在给你一个**最小可做版本**，先把"行为映射"跑起来。

---

## 桌面观察助手 - 最小可做版本 (MVP)

### 核心思路

**不做：** 全屏 OCR、暴力截图、内容深度分析  
**只做：** 轻量级行为感知 + 关键时刻触发分析

---

## 第一版：采集这 5 个信号

### 1. 前台应用 + 窗口标题

```python
# mac_observer.py
import subprocess

def get_active_app():
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        set frontWindow to name of front window of first application process whose frontmost is true
    end tell
    return frontApp & "|" & frontWindow
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip().split("|")

# 每 2 秒采一次
# 输出：("iTerm2", "小九 - AIOS Heartbeat")
```

### 2. 鼠标位置 + 移动轨迹

```python
from Quartz import CGEventSourceCreate, kCGEventSourceStateHIDSystemState, CGEventGetLocation
from Quartz.CoreGraphics import CGEventCreate, kCGEventMouseMoved

def get_mouse_position():
    event = CGEventCreate(None)
    loc = CGEventGetLocation(event)
    return (int(loc.x), int(loc.y))

# 每 0.5 秒采一次
# 记录最近 10 个点，判断：
# - 是否在同一区域停留 > 5s（可能在看报告）
# - 是否在两个区域来回移动（可能在对比）
# - 是否长时间不动（可能离开了）
```

### 3. 点击事件

```python
from Quartz import CGEventTapCreate, kCGEventLeftMouseDown, kCGEventRightMouseDown

def mouse_click_callback(proxy, type, event, refcon):
    loc = CGEventGetLocation(event)
    print(f"点击: ({int(loc.x)}, {int(loc.y)})")
    # 记录点击位置 + 时间戳

# 监听点击事件（不阻塞）
```

### 4. 键盘活动频率

```python
from pynput import keyboard

last_key_time = time.time()
key_count = 0

def on_key_press(key):
    global key_count, last_key_time
    key_count += 1
    last_key_time = time.time()

# 每 10 秒统计一次键盘活跃度
# 如果 key_count > 50 → 正在打字
# 如果 key_count < 5 → 可能在看东西
```

### 5. 屏幕变化热区

```python
import subprocess, hashlib

def capture_screen_hash():
    subprocess.run(["screencapture", "-x", "/tmp/screen.png"])
    with open("/tmp/screen.png", "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# 每 5 秒采一次
# 如果 hash 变化 → 屏幕有更新
# 如果连续 3 次不变 → 屏幕静止（可能在看报告）
```

---

## 事件判断逻辑

```python
# behavior_judge.py

def judge_behavior(data):
    app, window = data["active_app"], data["window_title"]
    mouse_pos = data["mouse_position"]
    mouse_trail = data["mouse_trail"]  # 最近 10 个点
    click_count = data["click_count"]
    key_count = data["key_count"]
    screen_changed = data["screen_changed"]
    
    # 规则 1：正在看小九的报告
    if "小九" in window or "AIOS" in window:
        if not screen_changed and key_count < 5:
            return "reading_xiaojiu_report"
    
    # 规则 2：终端里出现错误
    if app in ["iTerm2", "Terminal"]:
        if screen_changed and click_count == 0:
            return "terminal_error_maybe"
    
    # 规则 3：鼠标在同一区域停留 > 5s
    if len(set(mouse_trail)) < 3:  # 移动范围很小
        return "stuck_or_reading"
    
    # 规则 4：鼠标在两个区域来回移动
    if is_oscillating(mouse_trail):
        return "comparing_content"
    
    # 规则 5：长时间无键盘无鼠标
    if time.time() - data["last_activity"] > 60:
        return "idle_or_away"
    
    return "normal"
```

---

## 触发分析的时机

只在这些情况下才截图 + OCR + 让我分析：

```python
TRIGGER_CONDITIONS = {
    "reading_xiaojiu_report": {
        "action": "capture_window",
        "reason": "你在看小九的报告，我需要知道内容"
    },
    "terminal_error_maybe": {
        "action": "capture_window",
        "reason": "终端可能出错了，我需要看一眼"
    },
    "stuck_or_reading": {
        "action": "wait_5s_then_check",
        "reason": "你可能卡住了，或者在认真看东西"
    },
    "comparing_content": {
        "action": "capture_both_regions",
        "reason": "你在对比两块内容，我需要知道是什么"
    }
}
```

---

## 数据流

```
每 2s 采集 5 个信号
    ↓
行为判断（10 条规则）
    ↓
命中触发条件？
    ↓ 是
截图活跃窗口 → OCR → 发给小九分析 → Telegram 通知你
    ↓ 否
静默，继续采集
```

---

## 目录结构

```
desktop_observer/
├── main.py              # 主循环
├── signal_collector.py  # 采集 5 个信号
├── behavior_judge.py    # 行为判断逻辑
├── trigger_handler.py   # 触发分析
├── notifier.py          # 通知小九
└── config.json          # 配置
```

---

## config.json

```json
{
  "scan_interval_sec": 2,
  "mouse_trail_length": 10,
  "idle_threshold_sec": 60,
  "trigger_apps": ["iTerm2", "Terminal", "Cursor", "Telegram"],
  "trigger_keywords": ["小九", "AIOS", "Error", "Traceback"],
  "notify_channel": "telegram"
}
```

---

## 最小 MVP 功能表

第一版只做这 3 件事：

1. **监控前台应用 + 窗口标题**  
   发现 "小九" / "AIOS" 关键词 → 记录

2. **监控鼠标停留**  
   在同一区域停留 > 5s → 截图活跃窗口 → OCR

3. **监控屏幕变化**  
   终端窗口有变化 + 包含 "Error" → 截图 → 通知你

代码量：~200 行  
开发时间：半天  
依赖：`pyobjc`, `pynput`, `Pillow`

---

## 下一步

要我直接写这个 MVP 吗？还是你想先看看哪个模块的详细实现？
assistant: 先把文件都读一遍。
assistant: 好，读完了。直接挑刺。

---

## 技术总管审查报告

### 问题 1：假功能，落不了地

README 里这些全是空头支票：

- `python cli.py scheduler-status` — cli.py 存在吗？没验证过
- `python cli.py trigger-schedule` — 同上
- `from evaluator import Evaluator` — Evaluator 类有 `check_system_health()` 方法吗？
- `python restore.py --backup-id backup-20260313` — restore.py 接受这个参数吗？
- `Learning Loop` 整节 — 这个模块真的跑起来了吗？

**结论：** README 描述的是"理想中的太极OS"，不是"现在实际能用的太极OS"。对外发布会被人第一步就踩坑。

---

### 问题 2：QUICKSTART 的第 3 步会直接失败

```python
from task_queue import TaskQueue
queue = TaskQueue()
task_id = queue.add_task(task_type="test", ...)
```

`add_task()` 的签名对吗？`task_type="test"` 会被路由到哪个 Agent？没有 Agent 处理 "test" 类型，任务会永远 pending。新用户第一步就卡死。

---

### 问题 3：requirements.txt 有噪音

`openai-whisper==20250625` — 这是语音转文字，太极OS 核心功能用到了吗？如果只是 AIOS 语音命令的依赖，不该放在这里，会让人困惑。

`langchain-openai==1.1.10` — 同样，太极OS 核心用到了吗？还是某个实验性模块的遗留？

---

### 问题 4：progress.md 目标跑偏了

"让太极OS 从个人项目变成可分享的开源产品" — 这是你们现在最重要的事吗？

按 MEMORY.md 的主矛盾：**"有定义、无运行；有记录、无学习"**，产品化是 P2，先把真链跑起来才是 P0。

progress.md 的 7 个阶段里，没有一个是"让 GitHub_Researcher 真正运行起来"，没有一个是"让 Learning Loop 真正闭环"。

---

### 问题 5：和主仆桌面代理方案完全脱节

这 4 个文件描述的是一个"通用 AIOS 平台"，但你们刚刚讨论的方向是：

- 主仆分层（豆包 1.6 Flash 做仆，豆包 2.0 Lite 做主）
- 桌面观察 + 行为映射
- 多模态视觉理解替代 OCR
- 执行验证闭环

这些在文档里完全没有体现。如果要把太极OS 往这个方向推，文档需要重写，不是修补。

---

## 我的建议

**现在这 4 个文件的定位应该是：**

- README.md → 降级为"内部技术说明"，不对外发布，等真链跑通再改
- QUICKSTART.md → 改成"本地开发者快速验证"，只写真实能跑的步骤
- requirements.txt → 清理掉不确定的依赖，只留核心
- progress.md → 重写优先级，P0 改成"让真链跑通"

**能直接复用进主仆方案的：**
- 架构图里的数据流结构（Task Queue → Scheduler → Agent → 回写）
- agents.json 的配置格式
- events.db 的事件存储机制

**不该混进主仆方案的：**
- 社区建设、Docker、CI/CD 这些 — 现在完全不是时候
- Evolution Score 的描述 — 还没真正跑起来，先别对外承诺

---

要我直接改写这几个文件，改成"真实可用版"吗？
assistant: 先把文件都读一遍。
assistant: 好，读完了。直接挑刺。

---

## 技术总管审查报告

### 问题 1：假功能，落不了地

README 里这些全是空头支票：

- `python cli.py scheduler-status` — cli.py 存在吗？没验证过
- `python cli.py trigger-schedule` — 同上
- `from evaluator import Evaluator` — Evaluator 类有 `check_system_health()` 方法吗？
- `python restore.py --backup-id backup-20260313` — restore.py 接受这个参数吗？
- `Learning Loop` 整节 — 这个模块真的跑起来了吗？

**结论：** README 描述的是"理想中的太极OS"，不是"现在实际能用的太极OS"。对外发布会被人第一步就踩坑。

---

### 问题 2：QUICKSTART 的第 3 步会直接失败

```python
from task_queue import TaskQueue
queue = TaskQueue()
task_id = queue.add_task(task_type="test", ...)
```

`add_task()` 的签名对吗？`task_type="test"` 会被路由到哪个 Agent？没有 Agent 处理 "test" 类型，任务会永远 pending。新用户第一步就卡死。

---

### 问题 3：requirements.txt 有噪音

`openai-whisper==20250625` — 这是语音转文字，太极OS 核心功能用到了吗？如果只是 AIOS 语音命令的依赖，不该放在这里，会让人困惑。

`langchain-openai==1.1.10` — 同样，太极OS 核心用到了吗？还是某个实验性模块的遗留？

---

### 问题 4：progress.md 目标跑偏了

"让太极OS 从个人项目变成可分享的开源产品" — 这是你们现在最重要的事吗？

按 MEMORY.md 的主矛盾：**"有定义、无运行；有记录、无学习"**，产品化是 P2，先把真链跑起来才是 P0。

progress.md 的 7 个阶段里，没有一个是"让 GitHub_Researcher 真正运行起来"，没有一个是"让 Learning Loop 真正闭环"。

---

### 问题 5：和主仆桌面代理方案完全脱节

这 4 个文件描述的是一个"通用 AIOS 平台"，但你们刚刚讨论的方向是：

- 主仆分层（豆包 1.6 Flash 做仆，豆包 2.0 Lite 做主）
- 桌面观察 + 行为映射
- 多模态视觉理解替代 OCR
- 执行验证闭环

这些在文档里完全没有体现。如果要把太极OS 往这个方向推，文档需要重写，不是修补。

---

## 我的建议

**现在这 4 个文件的定位应该是：**

- README.md → 降级为"内部技术说明"，不对外发布，等真链跑通再改
- QUICKSTART.md → 改成"本地开发者快速验证"，只写真实能跑的步骤
- requirements.txt → 清理掉不确定的依赖，只留核心
- progress.md → 重写优先级，P0 改成"让真链跑通"

**能直接复用进主仆方案的：**
- 架构图里的数据流结构（Task Queue → Scheduler → Agent → 回写）
- agents.json 的配置格式
- events.db 的事件存储机制

**不该混进主仆方案的：**
- 社区建设、Docker、CI/CD 这些 — 现在完全不是时候
- Evolution Score 的描述 — 还没真正跑起来，先别对外承诺

---

要我直接改写这几个文件，改成"真实可用版"吗？
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "24985",
  "sender_id": "7986452220",
  "sender": "珊瑚海",
  "timestamp": "Fri 2026-03-13 16:36 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "珊瑚海 (7986452220)",
  "id": "7986452220",
  "name": "珊瑚海",
  "username": "shh7799"
}
```

这个 MVP 思路是对的，能做，而且比一上来全屏硬看靠谱得多。

但我直接给你挑刺，避免你后面白干：

这版里最该改的 5 点

• 别用全屏 hash
价值太低，噪音太大。
应该改成：
• 活跃窗口截图 hash
• 或固定区域 hash
• “鼠标停留 = 在看报告” 太粗
更准确应该是：
• 鼠标停留
• 
 • 键盘低活跃
• 
 • 窗口标题命中
• 
 • 该窗口最近有变化后进入静止
这几个一起判断
• 第一版别强绑 OCR
你前面已经决定要走轻量多模态模型，那这里 OCR 只能当兜底，不该是主线
• 点击监听 / 键盘监听在 macOS 上要先过权限
就是辅助功能 / 输入监听权限，不然代码写了也跑不起来
• “发给小九分析” 这句别反
如果按你后来定的架构，应该是：
• 观察器采信号
• 仆多模态看图
• 主做深层判断
• 再决定要不要通知你 / 群里汇报
不是一股脑“发给小九”

───

我会把它改成这个更稳的版本

第一阶段：纯行为映射

只做：

• 前台应用
• 窗口标题
• 鼠标轨迹
• 点击位置
• 键盘活跃度
• 活跃窗口变化检测

先不做复杂视觉理解。

第二阶段：触发后截图

只有命中事件才做：

• 截活跃窗口
• 交给仆多模态模型看
• 返回：
• 页面类型
• 关键区域
• 可点元素
• 是否疑似报错 / 报告 / 卡住

第三阶段：主代理判断

主来决定：

• 现在是什么任务态
• 要不要提醒你
• 要不要让仆执行下一步
• 这次经验值不值得入库

───

你这版代码层面的具体建议

get_active_app()

这个能用，但要注意：

• 有些 app 没有 front window name
• 有时 AppleScript 会报空值
• 要做异常兜底，不然主循环会断

鼠标轨迹

不要只存最近 10 个点，应该存：

• (x, y, t)
这样你才能判断：
• 停留时长
• 速度变化
• 来回振荡

点击事件

别只 print，至少要落：

• 时间戳
• 坐标
• 前台 app
• 当前窗口标题

键盘活动

别只数总键数，应该存窗口维度：

• 最近 10 秒在什么 app 里输入
这样你才能判断“是在聊天、写代码、还是搜东西”

触发条件

我建议先只保留这 3 个：

• reading_report
• terminal_error_maybe
• stuck_on_same_window

别一开始把规则堆太多。

───

我会这样定 MVP 边界

第一版目标不是“自动帮你做事”
而是：

正确判断你当前大致处于什么工作状态。

只要它能比较稳地识别：

• 你在看报告
• 你在终端看报错
• 你卡住了
• 你离开了

这个 MVP 就成功了。

───

如果让我现在拍板

我会让第一版目录变成这样：

desktop_observer/
├── main.py
├── collectors/
│ ├── active_window.py
│ ├── mouse_tracker.py
│ ├── keyboard_activity.py
│ └── window_capture.py
├── judges/
│ └── behavior_judge.py
├── triggers/
│ └── trigger_handler.py
├── memory/
│ └── event_store.py
├── models/
│ └── vision_client.py
├── notifier/
│ └── telegram_notify.py
└── config.json

这样后面从“观察器”升级到“主仆系统”不会推倒重来。

───

最后一句结论

这版可以开写，但要把“全屏 hash + OCR 主线”改成“活跃窗口行为映射 + 触发式多模态识别主线”。

如果你愿意，我下一条就不聊概念了，
我直接把这个 MVP 改成正式技术方案 v1，按模块、数据结构、主循环、触发条件给你写出来。
assistant: 好，你说得对。我刚才那版确实有几个硬伤：

1. **全屏 hash 噪音太大** — 改成活跃窗口 hash
2. **"鼠标停留 = 在看报告" 太粗** — 加上键盘低活跃 + 窗口标题命中 + 静止判断
3. **OCR 不该是主线** — 改成触发式多模态识别
4. **macOS 权限问题** — 需要辅助功能权限，要提前说明
5. **"发给小九分析" 架构反了** — 应该是观察器 → 仆 → 主 → 通知

---

## 我现在给你正式技术方案 v1

按你说的"先行为映射，再触发截图，最后主代理判断"的三阶段来。

---

## 技术方案 v1 - 桌面观察器 MVP

### 目标

**不是"自动帮你做事"，而是"正确判断你当前大致处于什么工作状态"。**

能稳定识别：
- 你在看报告
- 你在终端看报错
- 你卡住了
- 你离开了

---

## 架构设计

### 目录结构

```
desktop_observer/
├── main.py                      # 主循环
├── collectors/                  # 数据采集层
│   ├── active_window.py         # 前台应用 + 窗口标题
│   ├── mouse_tracker.py         # 鼠标轨迹 + 点击
│   ├── keyboard_activity.py     # 键盘活跃度
│   └── window_capture.py        # 活跃窗口截图
├── judges/                      # 判断层
│   └── behavior_judge.py        # 行为模式判断
├── triggers/                    # 触发层
│   └── trigger_handler.py       # 触发条件处理
├── models/                      # 模型层
│   └── vision_client.py         # 多模态视觉识别
├── notifier/                    # 通知层
│   └── telegram_notify.py       # Telegram 通知
├── memory/                      # 存储层
│   └── event_store.py           # 事件存储
└── config.json                  # 配置文件
```

---

## 第一阶段：纯行为映射

### 数据采集

#### 1. active_window.py

```python
import Quartz
import subprocess

def get_active_app():
    """获取前台应用名称和窗口标题"""
    try:
        # 获取前台应用
        app = Quartz.NSWorkspace.sharedWorkspace().frontmostApplication()
        app_name = app.localizedName()
        
        # 获取窗口标题（AppleScript）
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            tell process frontApp
                try
                    set windowTitle to name of front window
                on error
                    set windowTitle to ""
                end try
            end tell
        end tell
        return windowTitle
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=1)
        window_title = result.stdout.strip()
        
        return {
            'app': app_name,
            'window_title': window_title,
            'timestamp': time.time()
        }
    except Exception as e:
        return {'app': None, 'window_title': None, 'error': str(e)}
```

#### 2. mouse_tracker.py

```python
from pynput import mouse
import time

class MouseTracker:
    def __init__(self):
        self.positions = []  # [(x, y, t), ...]
        self.clicks = []     # [(x, y, t, button), ...]
        self.max_history = 100
        
    def on_move(self, x, y):
        """鼠标移动"""
        self.positions.append((x, y, time.time()))
        if len(self.positions) > self.max_history:
            self.positions.pop(0)
    
    def on_click(self, x, y, button, pressed):
        """鼠标点击"""
        if pressed:
            self.clicks.append((x, y, time.time(), str(button)))
            if len(self.clicks) > self.max_history:
                self.clicks.pop(0)
    
    def get_recent_activity(self, seconds=10):
        """获取最近 N 秒的活动"""
        now = time.time()
        recent_pos = [(x, y, t) for x, y, t in self.positions if now - t < seconds]
        recent_clicks = [(x, y, t, b) for x, y, t, b in self.clicks if now - t < seconds]
        return {
            'positions': recent_pos,
            'clicks': recent_clicks,
            'is_idle': len(recent_pos) < 5  # 10 秒内移动少于 5 次 = 静止
        }
```

#### 3. keyboard_activity.py

```python
from pynput import keyboard
import time

class KeyboardTracker:
    def __init__(self):
        self.key_counts = {}  # {app_name: [(timestamp, count), ...]}
        self.current_app = None
        
    def on_press(self, key):
        """键盘按下"""
        if self.current_app:
            if self.current_app not in self.key_counts:
                self.key_counts[self.current_app] = []
            self.key_counts[self.current_app].append(time.time())
    
    def update_current_app(self, app_name):
        """更新当前前台应用"""
        self.current_app = app_name
    
    def get_activity(self, app_name, seconds=10):
        """获取指定应用最近 N 秒的键盘活跃度"""
        if app_name not in self.key_counts:
            return 0
        now = time.time()
        recent = [t for t in self.key_counts[app_name] if now - t < seconds]
        return len(recent)
```

#### 4. window_capture.py

```python
import Quartz
import hashlib
from PIL import Image

def capture_active_window():
    """截取活跃窗口"""
    # 获取前台窗口的 bounds
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    
    for window in window_list:
        if window.get('kCGWindowLayer', 0) == 0:  # 前台窗口
            bounds = window['kCGWindowBounds']
            x, y, w, h = bounds['X'], bounds['Y'], bounds['Width'], bounds['Height']
            
            # 截图
            image = Quartz.CGWindowListCreateImage(
                Quartz.CGRectMake(x, y, w, h),
                Quartz.kCGWindowListOptionIncludingWindow,
                window['kCGWindowNumber'],
                Quartz.kCGWindowImageDefault
            )
            
            # 转 PIL Image
            pil_image = Image.frombytes('RGB', (w, h), image)
            
            # 计算 hash
            img_hash = hashlib.md5(pil_image.tobytes()).hexdigest()
            
            return {
                'image': pil_image,
                'hash': img_hash,
                'bounds': (x, y, w, h)
            }
    
    return None
```

---

## 第二阶段：触发后截图

### 触发条件判断

#### behavior_judge.py

```python
class BehaviorJudge:
    def __init__(self):
        self.last_window_hash = None
        self.window_stable_since = None
        
    def judge(self, active_window, mouse_activity, keyboard_activity, window_capture):
        """判断当前行为模式"""
        triggers = []
        
        # 1. 判断是否在看报告
        if self._is_reading_report(active_window, mouse_activity, keyboard_activity):
            triggers.append({
                'type': 'reading_report',
                'confidence': 0.8,
                'context': {
                    'app': active_window['app'],
                    'window_title': active_window['window_title']
                }
            })
        
        # 2. 判断是否在看终端报错
        if self._is_terminal_error(active_window, window_capture):
            triggers.append({
                'type': 'terminal_error_maybe',
                'confidence': 0.7,
                'context': {
                    'app': active_window['app'],
                    'window_hash': window_capture['hash']
                }
            })
        
        # 3. 判断是否卡住
        if self._is_stuck(active_window, mouse_activity, window_capture):
            triggers.append({
                'type': 'stuck_on_same_window',
                'confidence': 0.6,
                'context': {
                    'stuck_duration': time.time() - self.window_stable_since
                }
            })
        
        return triggers
    
    def _is_reading_report(self, active_window, mouse_activity, keyboard_activity):
        """判断是否在看报告"""
        # 条件：
        # 1. 鼠标停留（10 秒内移动少于 5 次）
        # 2. 键盘低活跃（10 秒内按键少于 10 次）
        # 3. 窗口标题命中关键词（report, 报告, 分析, dashboard）
        # 4. 窗口最近有变化后进入静止
        
        keywords = ['report', '报告', '分析', 'dashboard', 'summary']
        title = active_window.get('window_title', '').lower()
        
        return (
            mouse_activity['is_idle'] and
            keyboard_activity < 10 and
            any(kw in title for kw in keywords)
        )
    
    def _is_terminal_error(self, active_window, window_capture):
        """判断是否在看终端报错"""
        # 条件：
        # 1. 前台应用是终端（Terminal, iTerm, VS Code）
        # 2. 窗口标题包含错误关键词（error, failed, exception）
        
        terminal_apps = ['Terminal', 'iTerm2', 'Visual Studio Code', 'PyCharm']
        error_keywords = ['error', 'failed', 'exception', 'traceback']
        
        app = active_window.get('app', '')
        title = active_window.get('window_title', '').lower()
        
        return (
            app in terminal_apps and
            any(kw in title for kw in error_keywords)
        )
    
    def _is_stuck(self, active_window, mouse_activity, window_capture):
        """判断是否卡住"""
        # 条件：
        # 1. 窗口 hash 超过 60 秒没变化
        # 2. 鼠标有活动（说明人在，但窗口没变）
        
        current_hash = window_capture['hash']
        
        if current_hash != self.last_window_hash:
            self.last_window_hash = current_hash
            self.window_stable_since = time.time()
            return False
        
        if self.window_stable_since is None:
            self.window_stable_since = time.time()
            return False
        
        stuck_duration = time.time() - self.window_stable_since
        
        return (
            stuck_duration > 60 and
            not mouse_activity['is_idle']
        )
```

### 触发处理

#### trigger_handler.py

```python
class TriggerHandler:
    def __init__(self, vision_client, notifier):
        self.vision_client = vision_client
        self.notifier = notifier
        
    def handle(self, trigger, window_capture):
        """处理触发事件"""
        trigger_type = trigger['type']
        
        if trigger_type == 'reading_report':
            self._handle_reading_report(trigger, window_capture)
        elif trigger_type == 'terminal_error_maybe':
            self._handle_terminal_error(trigger, window_capture)
        elif trigger_type == 'stuck_on_same_window':
            self._handle_stuck(trigger, window_capture)
    
    def _handle_reading_report(self, trigger, window_capture):
        """处理"在看报告"触发"""
        # 1. 截图交给仆多模态模型
        vision_result = self.vision_client.analyze(
            image=window_capture['image'],
            prompt="这是一个报告页面吗？如果是，提取关键信息（标题、结论、数据）"
        )
        
        # 2. 主代理判断是否需要通知
        if vision_result['is_report'] and vision_result['has_key_findings']:
            self.notifier.send(
                f"📊 检测到你在看报告：{vision_result['title']}\n"
                f"关键发现：{vision_result['key_findings']}"
            )
    
    def _handle_terminal_error(self, trigger, window_capture):
        """处理"终端报错"触发"""
        vision_result = self.vision_client.analyze(
            image=window_capture['image'],
            prompt="这是一个错误信息吗？如果是，提取错误类型和关键行"
        )
        
        if vision_result['is_error']:
            self.notifier.send(
                f"⚠️ 检测到终端报错：{vision_result['error_type']}\n"
                f"关键行：{vision_result['key_line']}"
            )
    
    def _handle_stuck(self, trigger, window_capture):
        """处理"卡住"触发"""
        stuck_duration = trigger['context']['stuck_duration']
        self.notifier.send(
            f"🤔 你在同一个窗口停留了 {int(stuck_duration)} 秒，需要帮助吗？"
        )
```

---

## 第三阶段：主代理判断

### 多模态视觉识别

#### vision_client.py

```python
import anthropic

class VisionClient:
    def __init__(self, api_key, model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def analyze(self, image, prompt):
        """分析图片"""
        # 将 PIL Image 转 base64
        import base64
        from io import BytesIO
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # 调用 Claude Vision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        # 解析结果
        return self._parse_response(response.content[0].text)
    
    def _parse_response(self, text):
        """解析模型返回的文本"""
        # 简单的 JSON 解析（实际应该更健壮）
        import json
        try:
            return json.loads(text)
        except:
            return {'raw': text}
```

---

## 主循环

#### main.py

```python
import time
from collectors.active_window import get_active_app
from collectors.mouse_tracker import MouseTracker
from collectors.keyboard_activity import KeyboardTracker
from collectors.window_capture import capture_active_window
from judges.behavior_judge import BehaviorJudge
from triggers.trigger_handler import TriggerHandler
from models.vision_client import VisionClient
from notifier.telegram_notify import TelegramNotifier
from memory.event_store import EventStore

def main():
    # 初始化
    mouse_tracker = MouseTracker()
    keyboard_tracker = KeyboardTracker()
    behavior_judge = BehaviorJudge()
    vision_client = VisionClient(api_key="your-api-key")
    notifier = TelegramNotifier(bot_token="your-bot-token", chat_id="your-chat-id")
    trigger_handler = TriggerHandler(vision_client, notifier)
    event_store = EventStore()
    
    # 启动监听
    mouse_listener = mouse.Listener(
        on_move=mouse_tracker.on_move,
        on_click=mouse_tracker.on_click
    )
    keyboard_listener = keyboard.Listener(
        on_press=keyboard_tracker.on_press
    )
    mouse_listener.start()
    keyboard_listener.start()
    
    print("桌面观察器已启动...")
    
    # 主循环（每 5 秒采集一次）
    while True:
        try:
            # 1. 采集数据
            active_window = get_active_app()
            mouse_activity = mouse_tracker.get_recent_activity(seconds=10)
            keyboard_activity = keyboard_tracker.get_activity(active_window['app'], seconds=10)
            window_capture = capture_active_window()
            
            # 更新键盘追踪器的当前应用
            keyboard_tracker.update_current_app(active_window['app'])
            
            # 2. 判断行为模式
            triggers = behavior_judge.judge(
                active_window, 
                mouse_activity, 
                keyboard_activity, 
                window_capture
            )
            
            # 3. 处理触发事件
            for trigger in triggers:
                trigger_handler.handle(trigger, window_capture)
                event_store.save(trigger)
            
            # 4. 休眠
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n正在停止...")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(5)
    
    # 停止监听
    mouse_listener.stop()
    keyboard_listener.stop()

if __name__ == "__main__":
    main()
```

---

## 配置文件

#### config.json

```json
{
  "vision": {
    "api_key": "your-anthropic-api-key",
    "model": "claude-sonnet-4-6"
  },
  "notifier": {
    "telegram": {
      "bot_token": "your-bot-token",
      "chat_id": "your-chat-id"
    }
  },
  "collectors": {
    "mouse_history_size": 100,
    "keyboard_history_size": 100,
    "capture_interval": 5
  },
  "triggers": {
    "reading_report": {
      "enabled": true,
      "mouse_idle_threshold": 5,
      "keyboard_idle_threshold": 10
    },
    "terminal_error": {
      "enabled": true,
      "terminal_apps": ["Terminal", "iTerm2", "Visual Studio Code"]
    },
    "stuck": {
      "enabled": true,
      "stuck_duration_threshold": 60
    }
  }
}
```

---

## macOS 权限说明

### 需要的权限

1. **辅助功能（Accessibility）**
   - 用于监听鼠标和键盘事件
   - 路径：系统偏好设置 → 安全性与隐私 → 辅助功能

2. **屏幕录制（Screen Recording）**
   - 用于截取窗口
   - 路径：系统偏好设置 → 安全性与隐私 → 屏幕录制

### 权限检查代码

```python
import subprocess

def check_permissions():
    """检查权限"""
    # 检查辅助功能权限
    script = '''
    tell application "System Events"
        return UI elements enabled
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    accessibility = result.stdout.strip() == 'true'
    
    if not accessibility:
        print("⚠️ 需要辅助功能权限，请在系统偏好设置中授权")
        return False
    
    print("✅ 权限检查通过")
    return True
```

---

## MVP 验收标准

### 第一版成功标准

能稳定识别以下 4 种状态：

1. **你在看报告** - 准确率 >80%
2. **你在终端看报错** - 准确率 >70%
3. **你卡住了** - 准确率 >60%
4. **你离开了** - 准确率 >90%

### 不在第一版范围内

- 自动执行操作
- 复杂的任务规划
- 多窗口协同
- 历史回溯分析

---

这版方案可以直接开写了。要我继续细化某个模块吗？
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "24987",
  "sender_id": "7986452220",
  "sender": "珊瑚海",
  "timestamp": "Fri 2026-03-13 16:36 GMT+8"
}
```

Sender (untrusted metadata):
```json
{
  "label": "珊瑚海 (7986452220)",
  "id": "7986452220",
  "name": "珊瑚海",
  "username": "shh7799"
}
```

我已经先给你把第一版骨架搭出来了，项目在：

desktop_rpa_master_servant

目前已经有这些东西：

• README：项目说明、运行方式、边界和后续计划
• docs/architecture.md：主仆协同整体架构
• docs/communication_protocol.md：主和仆怎么通信
• docs/learning_data_structures.md：学习系统怎么记“验证成功的经验”
• src/ 下面拆了：
• master/
• servant/
• vision/
• protocol/
• learning/
• runtime/

还顺手放了一个可跑的 Python MVP 骨架，里面已经有：

• 主控协调器 / 规划器 / 调度器
• 仆执行器
• 简单的视觉感知 mock
• 屏幕观察 → 动作 → 回传 → 学习记录 的闭环
• 一个示例任务文件

而且这套我已经让它跑通了一个 mock 流程：

• 仆注册
• 主派任务
• 观察屏幕
• 执行点击
• 回传结果
• 写入学习轨迹

另外我还顺手提交了一次代码。

有个小尾巴：

• 这次提交里混进了 __pycache__/*.pyc
• 不影响骨架本身
• 但后面最好补一个 .gitignore 清理掉

你刚才又补了新要求：
不要走 OCR 主线，改成轻量多模态模型：仆用豆包 1.6 Flash，主用豆包 2.0 Lite。

这个我已经记住了。
下一步我建议直接做这两个：

1. 把当前骨架改成“多模态主线，OCR 仅兜底”
2. 把你刚说的“表层行为映射”并进第一阶段 MVP

如果你点头，我下一轮就继续往下收：

• 补 .gitignore
• 改架构文档
• 把豆包主仆模型接口占位接进去
• 把行为映射采集器骨架也加上
assistant: 点头，继续。
assistant: 目录不存在，可能在别的位置。
assistant: 项目还没在本地，可能是你在另一台机器或者还没 push 到这里。没关系，我直接在 workspace 里建。
assistant: 现在写各模块。先写采集层：
assistant: 现在写视觉层（豆包接口占位）：
assistant: 最后写主循环和 requirements：
assistant: 现在写 README 和架构文档：
