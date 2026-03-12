"""
测试 UIVisionAgent 集成到太极OS 主流程
"""

import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent
QUEUE_PATH = BASE_DIR / "data" / "task_queue.jsonl"

# 创建测试任务
test_tasks = [
    {
        "id": "task-ui-vision-001",
        "type": "ui-vision",
        "description": "点击登录按钮",
        "priority": "normal",
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "screenshot_path": None  # 自动截屏
    },
    {
        "id": "task-ui-vision-002",
        "type": "ui-vision",
        "description": "输入用户名",
        "priority": "normal",
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "screenshot_path": None
    },
    {
        "id": "task-ui-vision-003",
        "type": "ui-vision",
        "description": "向下滚动页面",
        "priority": "normal",
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "screenshot_path": None
    }
]

# 写入队列
QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(QUEUE_PATH, "a", encoding="utf-8") as f:
    for task in test_tasks:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")

print(f"✅ 已创建 {len(test_tasks)} 个测试任务")
print(f"队列文件: {QUEUE_PATH}")
print("\n任务列表:")
for task in test_tasks:
    print(f"  - {task['id']}: {task['description']}")

print("\n下一步：运行 ui_vision_executor.py 执行任务")
