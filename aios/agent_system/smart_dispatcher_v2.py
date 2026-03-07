"""
AIOS Smart Dispatcher v2.0 - 集成自适应学习

新增功能：
1. 自动记录成功/失败模式
2. 使用历史最佳模式
3. 避免已知失败模式
4. 学习用户偏好
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
from core.adaptive_learning import get_adaptive_learning
from core.smart_recommender import SmartRecommender


def dispatch_v2(user_input: str, auto_confirm: bool = False) -> dict:
    """
    智能调度用户请求（v2.0 - 集成自适应学习 + 智能推荐）
    
    Args:
        user_input: 用户输入
        auto_confirm: 是否自动确认
        
    Returns:
        执行结果
    """
    al = get_adaptive_learning()
    recommender = SmartRecommender()
    
    # 1. 处理用户请求
    result = process_user_request(user_input)
    
    # 2. 生成智能推荐
    context = {
        "action": result.intent.action,
        "target": result.intent.target,
        **result.intent.params
    }
    
    print("\n" + "=" * 60)
    print("🤖 智能推荐")
    print("=" * 60)
    
    # 2.1 执行路径推荐
    path_rec = recommender.recommend_execution_path(
        task_type=result.plan.task_type.value,
        intent_action=result.intent.action,
        intent_target=result.intent.target,
    )
    if path_rec:
        print(f"\n💡 历史最佳路径:")
        print(f"   成功率: {path_rec['confidence'] * 100:.1f}%")
        print(f"   平均耗时: {path_rec['avg_duration']:.1f}秒")
        print(f"   使用次数: {path_rec['success_count']}次")
    
    # 2.2 耗时预测
    predicted_duration, duration_msg = recommender.predict_duration(
        task_type=result.plan.task_type.value,
        intent_action=result.intent.action,
        intent_target=result.intent.target,
        default_duration=result.plan.total_estimated_duration
    )
    print(f"\n⏱️ {duration_msg}")
    
    # 2.3 风险检查
    risks = recommender.check_risks(context)
    if risks:
        print(f"\n⚠️ 发现 {len(risks)} 个潜在风险:")
        for i, risk in enumerate(risks, 1):
            level_emoji = "🔴" if risk["level"] == "high" else "🟡"
            print(f"   {level_emoji} {risk['message']}")
            print(f"      建议: {risk['suggestion']}")
    
    # 2.4 参数建议
    param_suggestions = recommender.suggest_parameters(
        task_type=result.plan.task_type.value,
        current_params=result.intent.params
    )
    if param_suggestions:
        print(f"\n🔧 参数优化建议:")
        for key, value in param_suggestions.items():
            print(f"   {key} = {value}")
    
    print("=" * 60)
    
    # 3. 检查失败模式
    failure_pattern = al.should_avoid(context)
    
    if failure_pattern:
        print(f"\n⚠️  警告：检测到已知失败模式")
        print(f"   错误类型: {failure_pattern.error_type}")
        print(f"   发生次数: {failure_pattern.occurrence_count}次")
        print(f"   错误信息: {failure_pattern.error_message}")
        if failure_pattern.suggested_fix:
            print(f"   建议修复: {failure_pattern.suggested_fix}")
        
        # 高频失败模式（>= 5次）直接拒绝
        if failure_pattern.occurrence_count >= 5:
            print(f"\n❌ 此操作失败次数过多，已自动拒绝")
            return {
                "status": "rejected",
                "reason": f"已知失败模式（{failure_pattern.occurrence_count}次）",
                "error_type": failure_pattern.error_type,
            }
    
    # 4. 应用用户偏好
    output_format = al.get_preference("output_format", "default", "detailed")
    if output_format == "brief":
        print(f"\n📝 使用简洁输出格式（用户偏好）")
    
    # 5. 输出分析结果
    print(format_result(result))
    
    # 6. 决定是否执行
    should_execute = result.auto_execute or auto_confirm
    
    if not should_execute:
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
    
    # 7. 执行任务
    print("\n🚀 开始执行...")
    
    executed_tasks = []
    start_time = time.time()
    
    try:
        for subtask in result.plan.subtasks:
            print(f"\n📝 执行: {subtask.description} [{subtask.agent_type}]")
            
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
        
        duration = time.time() - start_time
        
        # 8. 记录成功模式
        al.record_success(
            task_type=result.plan.task_type.value,
            intent_action=result.intent.action,
            intent_target=result.intent.target,
            agent_sequence=[st.agent_type for st in result.plan.subtasks],
            duration=duration,
        )
        
        # 9. 学习用户偏好（如果用户选择了自动执行）
        if auto_confirm:
            al.learn_preference("auto_confirm", result.intent.risk, True)
        
        print(f"\n✅ 所有任务已提交！共 {len(executed_tasks)} 个任务")
        print(f"   任务将由 Heartbeat 自动执行")
        print(f"\n📊 已记录成功模式（用于未来优化）")
        
        return {
            "status": "success",
            "tasks": executed_tasks,
            "total": len(executed_tasks),
            "duration": duration,
        }
        
    except Exception as e:
        # 10. 记录失败模式
        al.record_failure(
            task_description=user_input,
            error_type=type(e).__name__,
            error_message=str(e),
            context=context,
        )
        
        print(f"\n❌ 执行失败: {e}")
        print(f"📊 已记录失败模式（避免未来重复）")
        
        return {
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
        }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python smart_dispatcher_v2.py <用户输入> [--auto-confirm]")
        print("\n示例:")
        print("  python smart_dispatcher_v2.py \"查看 Agent 执行情况\"")
        print("  python smart_dispatcher_v2.py \"优化系统性能\" --auto-confirm")
        sys.exit(1)
    
    user_input = sys.argv[1]
    auto_confirm = "--auto-confirm" in sys.argv
    
    try:
        result = dispatch_v2(user_input, auto_confirm)
        
        # 输出 JSON 结果
        print("\n" + "=" * 60)
        print("执行结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 显示学习统计
        al = get_adaptive_learning()
        stats = al.get_stats()
        print("\n" + "=" * 60)
        print("学习统计:")
        print(f"  成功模式: {stats['success_patterns']}")
        print(f"  失败模式: {stats['failure_patterns']}")
        print(f"  用户偏好: {stats['user_preferences']}")
        print(f"  总成功: {stats['total_successes']}次")
        print(f"  总失败: {stats['total_failures']}次")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import time
    main()
