#!/usr/bin/env python3
"""重新触发 Docs_Unified_Writer"""

import json
from pathlib import Path
from datetime import datetime

# 创建新的 smoke test 任务
task = {
    "task_id": f"smoke-Docs_Unified_Writer-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "agent_id": "Docs_Unified_Writer",
    "type": "learning",
    "description": "统一 AIOS 主文档到 README.md（合并 INSTALL/API/TUTORIAL）",
    "priority": "normal",
    "status": "pending",
    "created_at": datetime.now().isoformat(),
    "retry_count": 0,
    "smoke_test": True,
    "note": "重新触发以获取真实耗时数据"
}

# 追加到队列
queue_file = Path("data/task_queue.jsonl")
with open(queue_file, 'a', encoding='utf-8') as f:
    f.write(json.dumps(task, ensure_ascii=False) + '\n')

print("✅ 已创建 Docs_Unified_Writer 重试任务")
print(f"Task ID: {task['task_id']}")
print("\n下一步：运行 heartbeat 触发执行")
print("  cd C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system")
print("  python heartbeat_v5.py")
