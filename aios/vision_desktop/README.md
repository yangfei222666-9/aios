# 视觉管理桌面 v0.1

基于 UI-TARS + UIVisionAgent 的最小原型。

## 功能

1. 截取当前屏幕 / 加载图片文件
2. 输入任务描述（如"点击登录按钮"）
3. 调用 UIVisionAgent 分析
4. 显示分析结果（推理、操作、置信度）
5. 手动确认后执行操作
6. 低置信度（<0.7）自动拦截

## 依赖

```bash
pip install PyQt5 pillow pyautogui transformers torch
```

## 运行

```powershell
cd C:\Users\A\.openclaw\workspace\aios\vision_desktop
& "C:\Program Files\Python312\python.exe" main.py
```

## 目录结构

```
vision_desktop/
├── main.py          # 主程序
└── README.md        # 本文件
```

## 复用模块

- `../agent_system/ui_vision_agent.py` - UIVisionAgent 核心
- `../agent_system/ui_vision_agent.py` - UITARSEngine 模型封装
- `../agent_system/ui_vision_agent.py` - ActionExecutor 执行器

## 安全边界

- 置信度 < 0.7 → 不允许执行
- 执行前必须手动确认
- pyautogui.FAILSAFE = True（鼠标移到左上角可中断）

## 下一步

- [ ] 在截图上标注识别的坐标
- [ ] 操作历史记录
- [ ] 支持多步任务
- [ ] 执行后自动验证
