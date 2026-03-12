"""
UIVision Task Executor - 处理 GUI 视觉任务
直接调用 UIVisionAgent，不通过 sessions_spawn
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image
import pyautogui

# 导入 UIVisionAgent
sys.path.insert(0, str(Path(__file__).parent))
from ui_vision_agent import UIVisionAgent, ActionExecutor
from test_ui_vision_mock import MockEngine

BASE_DIR = Path(__file__).resolve().parent
QUEUE_PATH = BASE_DIR / "data" / "task_queue.jsonl"
EXEC_LOG = BASE_DIR / "data" / "task_executions_v2.jsonl"


def get_ui_vision_tasks():
    """获取 type=ui-vision 的待执行任务"""
    if not QUEUE_PATH.exists():
        return []
    
    tasks = []
    for line in QUEUE_PATH.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                t = json.loads(line)
                if t.get("status") == "running" and t.get("type") == "ui-vision":
                    tasks.append(t)
            except json.JSONDecodeError:
                continue
    return tasks


def execute_ui_vision_task(task):
    """执行单个 UI Vision 任务"""
    task_id = task["id"]
    desc = task["description"]
    screenshot_path = task.get("screenshot_path")
    
    print(f"[UI-VISION] 执行任务: {task_id}")
    print(f"  描述: {desc}")
    
    start_time = datetime.now(timezone.utc)
    
    try:
        # 1. 加载截图
        if screenshot_path and Path(screenshot_path).exists():
            screenshot = Image.open(screenshot_path)
        else:
            # 如果没有提供截图，自动截屏
            screenshot = pyautogui.screenshot()
        
        # 2. 初始化 Agent（使用 Mock 引擎）
        agent = UIVisionAgent(engine=MockEngine())
        executor = ActionExecutor()
        
        # 3. 感知
        result = agent.perceive(desc, screenshot)
        
        print(f"  Status: {result.status}")
        print(f"  Thought: {result.thought}")
        print(f"  Action: {result.action.to_dict()}")
        print(f"  Confidence: {result.confidence}")
        
        # 4. 执行（如果置信度足够）
        if result.status == "ok" and result.confidence >= 0.8:
            exec_result = executor.execute(result.action)
            if exec_result["success"]:
                print(f"  ✅ 执行成功")
                status = "completed"
                error = None
            else:
                print(f"  ❌ 执行失败: {exec_result['error']}")
                status = "failed"
                error = exec_result["error"]
        else:
            print(f"  ⚠️ 置信度不足，不执行")
            status = "failed"
            error = "置信度不足或状态不确定"
        
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 5. 记录执行结果
        write_execution_record(
            task_id=task_id,
            agent_id="ui-vision",
            status=status,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_ms=duration_ms,
            result=result.to_dict() if status == "completed" else None,
            error=error
        )
        
        return status == "completed"
    
    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        write_execution_record(
            task_id=task_id,
            agent_id="ui-vision",
            status="failed",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_ms=duration_ms,
            error=str(e)
        )
        
        return False


def write_execution_record(task_id, agent_id, status, start_time, end_time, 
                           duration_ms, result=None, error=None):
    """写入执行记录"""
    record = {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": status,
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": duration_ms,
        "retry_count": 0,
        "side_effects": {"files_written": [], "tasks_created": [], "api_calls": 0},
    }
    
    if status == "completed" and result:
        record["result"] = result
    if status == "failed" and error:
        record["error"] = error
    
    with open(EXEC_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def mark_tasks_completed(task_ids, status):
    """标记任务为已完成/失败"""
    if not QUEUE_PATH.exists():
        return
    
    lines = QUEUE_PATH.read_text(encoding="utf-8").strip().split("\n")
    new_lines = []
    for line in lines:
        if line.strip():
            try:
                t = json.loads(line)
                if t.get("id") in task_ids:
                    t["status"] = status
                    t["completed_at"] = datetime.now(timezone.utc).isoformat()
                new_lines.append(json.dumps(t, ensure_ascii=False))
            except json.JSONDecodeError:
                new_lines.append(line)
    
    QUEUE_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main():
    tasks = get_ui_vision_tasks()
    
    if not tasks:
        print("[UI-VISION] 没有待执行的 UI Vision 任务")
        return
    
    print(f"[UI-VISION] 发现 {len(tasks)} 个待执行任务")
    
    completed = []
    failed = []
    
    for task in tasks:
        success = execute_ui_vision_task(task)
        if success:
            completed.append(task["id"])
        else:
            failed.append(task["id"])
    
    # 更新任务状态
    if completed:
        mark_tasks_completed(completed, "completed")
    if failed:
        mark_tasks_completed(failed, "failed")
    
    print(f"\n[UI-VISION] 执行完成: {len(completed)} 成功, {len(failed)} 失败")


if __name__ == "__main__":
    main()
