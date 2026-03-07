"""
AIOS Smart Dispatcher - 智能调度器

整合全自动智能化功能，处理用户请求并自动执行。

使用方式：
    python smart_dispatcher.py "查看 Agent 执行情况"
    python smart_dispatcher.py "优化系统性能"
"""
import sys
import json
from pathlib import Path

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from core.auto_intelligence import process_user_request, format_result
from core.task_submitter import submit_task


def dispatch(user_input: str, auto_confirm: bool = False) -> dict:
    """
    智能调度用户请求
    
    Args:
        user_input: 用户输入
        auto_confirm: 是否自动确认（跳过人工确认）
        
    Returns:
        执行结果
    """
    # 1. 处理用户请求
    result = process_user_request(user_input)
    
    # 2. 输出分析结果
    print(format_result(result))
    
    # 3. 决定是否执行
    should_execute = result.auto_execute or auto_confirm
    
    if not should_execute:
        # 需要确认
        print("\n⚠️  此操作需要确认，是否继续？(y/n): ", end="")
        if not auto_confirm:
            response = input().strip().lower()
            should_execute = response in ["y", "yes", "是"]
    
    if not should_execute:
        print("\n❌ 操作已取消")
        return {
            "status": "cancelled",
            "reason": "用户取消",
        }
    
    # 4. 执行任务
    print("\n🚀 开始执行...")
    
    executed_tasks = []
    for subtask in result.plan.subtasks:
        print(f"\n📝 执行: {subtask.description} [{subtask.agent_type}]")
        
        # 提交任务到队列
        task_metadata = subtask.params.copy() if subtask.params else {}
        task_metadata["estimated_duration"] = subtask.estimated_duration
        
        task_id = submit_task(
            description=subtask.description,
            task_type=subtask.agent_type,
            priority=subtask.priority,
            metadata=task_metadata,
        )
        
        executed_tasks.append({
            "task_id": task_id,
            "description": subtask.description,
            "agent_type": subtask.agent_type,
        })
        
        print(f"   ✅ 已提交到队列: {task_id}")
    
    print(f"\n✅ 所有任务已提交！共 {len(executed_tasks)} 个任务")
    print(f"   任务将由 Heartbeat 自动执行")
    
    return {
        "status": "success",
        "tasks": executed_tasks,
        "total": len(executed_tasks),
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python smart_dispatcher.py <用户输入> [--auto-confirm]")
        print("\n示例:")
        print("  python smart_dispatcher.py \"查看 Agent 执行情况\"")
        print("  python smart_dispatcher.py \"优化系统性能\" --auto-confirm")
        sys.exit(1)
    
    user_input = sys.argv[1]
    auto_confirm = "--auto-confirm" in sys.argv
    
    try:
        result = dispatch(user_input, auto_confirm)
        
        # 输出 JSON 结果（方便脚本调用）
        print("\n" + "=" * 60)
        print("执行结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
