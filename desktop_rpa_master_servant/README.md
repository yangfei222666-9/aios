# 桌面观察器 - 主仆协同 MVP

**目标：** 不是"自动帮你做事"，而是"正确判断你当前大致处于什么工作状态"。

能稳定识别：
- 你在看报告
- 你在终端看报错
- 你卡住了
- 你离开了

---

## 核心设计

### 三阶段架构

1. **Phase 1: 纯行为映射**
   - 采集：前台应用、窗口标题、鼠标轨迹、键盘活跃度
   - 判断：综合 4 个信号（鼠标停留 + 键盘低活跃 + 窗口标题命中 + 静止时长）
   - 输出：触发列表（type + confidence + context）

2. **Phase 2: 触发后截图**
   - 只在命中触发时截图（不做轮询截图）
   - 交给仆多模态模型（豆包 1.6 Flash）快速感知
   - 返回：页面类型、关键区域、是否疑似报错/报告/卡住

3. **Phase 3: 主代理判断**
   - 主（豆包 2.0 Lite）根据仆的分析结果做深层判断
   - 决定：要不要提醒你、要不要让仆执行下一步、这次经验值不值得入库

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制 `config.json` 为 `config.local.json`，填入你的 API Key：

```json
{
  "vision": {
    "api_key": "YOUR_ARK_API_KEY",
    "servant_model": "doubao-1.6-flash",
    "master_model": "doubao-2.0-lite"
  },
  "notifier": {
    "telegram": {
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    }
  }
}
```

### 3. 运行

```bash
python main.py --config config.local.json
```

---

## 目录结构

```
desktop_rpa_master_servant/
├── main.py                      # 主循环
├── config.json                  # 配置模板
├── requirements.txt             # 依赖
├── src/
│   ├── collectors/              # 数据采集层
│   │   ├── active_window.py     # 前台应用 + 窗口标题
│   │   ├── mouse_tracker.py     # 鼠标轨迹 + 点击
│   │   ├── keyboard_activity.py # 键盘活跃度
│   │   └── window_capture.py    # 活跃窗口截图
│   ├── master/                  # 主代理层
│   │   ├── behavior_judge.py    # 行为模式判断
│   │   └── trigger_handler.py   # 触发事件处理
│   ├── vision/                  # 视觉层
│   │   └── vision_client.py     # 豆包多模态接口
│   ├── runtime/                 # 运行时
│   │   └── telegram_notify.py   # Telegram 通知
│   └── learning/                # 学习层
│       └── event_store.py       # 事件存储
└── docs/                        # 文档
    ├── architecture.md          # 架构设计
    ├── communication_protocol.md
    └── learning_data_structures.md
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

## 技术栈

- **多模态主线：** 豆包 1.6 Flash（仆）+ 豆包 2.0 Lite（主）
- **OCR 兜底：** pytesseract（仅在多模态失败时启用）
- **输入监听：** pynput（跨平台）
- **截图：** mss（Windows/Linux）/ Quartz（macOS）
- **通知：** Telegram Bot API

---

## 后续计划

### Phase 4: 执行验证闭环
- 仆执行操作（点击、输入）
- 截图验证结果
- 回传给主判断是否成功

### Phase 5: 学习系统
- 记录"验证成功的经验"
- 构建行为模式库
- 自动改进触发条件

### Phase 6: 多窗口协同
- 跨应用任务流
- 上下文切换
- 任务队列

---

## 常见问题

### Q: Windows 上鼠标/键盘监听失败？

**A:** 需要管理员权限，或者在"隐私和安全性"中授权。

### Q: macOS 上截图失败？

**A:** 需要在"系统偏好设置 → 安全性与隐私 → 屏幕录制"中授权。

### Q: 豆包 API 调用失败？

**A:** 检查 `api_key` 和 `api_base` 是否正确，确认模型 ID 是否可用。

### Q: OCR 兜底不工作？

**A:** 需要先安装 Tesseract-OCR：
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

---

## 许可证

MIT License

---

**版本：** v0.1 MVP  
**最后更新：** 2026-03-13  
**维护者：** 小九 + 珊瑚海
