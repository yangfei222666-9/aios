"""
Decide and Dispatch - 统一入口编排器

作用：把 task/event/alert/heartbeat 统一收进一个入口，走完主链：
ingest → route → policy check → dispatch → observe → writeback

必须回答的 5 句：
1. 这次输入被识别成什么情况
2. router 选了谁，为什么
3. policy 是否放行，为什么
4. 执行计划是什么
5. 结果写回了什么，后续怎么复盘
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from decide_and_dispatch_schema import (
    TaskContext, ExecutionPlan, DispatchResult, DecisionRecord, DispatchDecision,
    FinalStatus, DispatchMode
)
from skill_router import SkillRouter
from skill_router_schema import TaskContext as RouterTaskContext
from policy_decision import PolicyDecisionEngine
from policy_decision_schema import PolicyInput


class DecideAndDispatch:
    """统一入口编排器 v1.0"""
    
    VERSION = "1.0.0"
    
    def __init__(
        self,
        router: Optional[SkillRouter] = None,
        policy_engine: Optional[PolicyDecisionEngine] = None,
        log_path: Optional[Path] = None
    ):
        """
        初始化编排器
        
        Args:
            router: 技能路由器（可选）
            policy_engine: 策略引擎（可选）
            log_path: 日志路径（可选）
        """
        self.router = router or SkillRouter()
        self.policy_engine = policy_engine or PolicyDecisionEngine()
        self.log_path = log_path or Path(__file__).parent / "data" / "dispatch_log.jsonl"
        
    def process(self, task_context: TaskContext) -> DecisionRecord:
        """
        处理任务（完整主链）
        
        Args:
            task_context: 任务上下文
            
        Returns:
            DecisionRecord: 决策记录
        """
        # 1. Ingest - 标准化输入（已经是 TaskContext）
        
        # 2. Route - 路由决策
        router_task_context = RouterTaskContext(
            source=task_context.source,
            task_type=task_context.task_type,
            content=task_context.content,
            priority=task_context.priority,
            risk_level=task_context.risk_level,
            system_state=task_context.system_state,
            recent_history=task_context.recent_history,
            available_handlers=task_context.available_handlers
        )
        
        router_output = self.router.route(router_task_context)
        
        # 3. Policy Check - 策略检查
        if router_output.chosen_handler:
            policy_input = PolicyInput(
                operation_type=task_context.task_type,
                handler_type="skill",  # 第一版默认 skill
                handler_name=router_output.chosen_handler,
                risk_level=task_context.risk_level,
                system_health=task_context.system_state.get('health_status', 'healthy'),
                known_failure_patterns=self._extract_failure_patterns(task_context),
                user_policy={},
                router_decision={
                    'confidence': router_output.confidence,
                    'fallback_handlers': router_output.fallback_handlers
                }
            )
            
            policy_output = self.policy_engine.decide(policy_input)
        else:
            # 无候选处理器，直接失败
            policy_output = None
        
        # 4. Dispatch - 生成执行计划并派发
        execution_plan, dispatch_result = self._dispatch(
            task_context, router_output, policy_output
        )
        
        # 5. Observe - 观测
        observation = self._observe(task_context, router_output, policy_output, dispatch_result)
        
        # 6. Writeback - 记忆回写
        memory_writeback = self._writeback(
            task_context, router_output, policy_output, execution_plan, dispatch_result
        )
        
        # 确定最终状态
        final_status = self._determine_final_status(policy_output, dispatch_result)
        
        return DecisionRecord(
            current_situation=router_output.situation_type if router_output else "unknown",
            router_result=router_output.to_dict() if router_output else {},
            policy_result=policy_output.to_dict() if policy_output else {},
            chosen_handler=router_output.chosen_handler if router_output else None,
            execution_plan=execution_plan,
            dispatch_result=dispatch_result,
            observation=observation,
            memory_writeback=memory_writeback,
            final_status=final_status
        )
    
    def _extract_failure_patterns(self, task_context: TaskContext) -> list:
        """从历史中提取失败模式"""
        patterns = []
        for item in task_context.recent_history:
            if item.get('status') == 'failed':
                error_type = item.get('error_type', 'unknown')
                if error_type not in patterns:
                    patterns.append(error_type)
        return patterns
    
    def _dispatch(
        self,
        task_context: TaskContext,
        router_output,
        policy_output
    ) -> tuple:
        """
        派发执行
        
        Returns:
            (execution_plan, dispatch_result)
        """
        start_time = time.time()
        
        # 无候选处理器
        if not router_output or not router_output.chosen_handler:
            execution_plan = None
            dispatch_result = DispatchResult(
                status=FinalStatus.FAILED.value,
                handler_used=None,
                execution_time=time.time() - start_time,
                output=None,
                error="无可用处理器",
                fallback_triggered=False
            )
            return execution_plan, dispatch_result
        
        # 策略拒绝
        if policy_output and policy_output.policy_result == "reject":
            execution_plan = ExecutionPlan(
                handler=router_output.chosen_handler,
                mode=DispatchMode.REAL.value,
                steps=["策略拒绝，未执行"],
                fallback=policy_output.fallback_action,
                expected_output="无"
            )
            dispatch_result = DispatchResult(
                status=FinalStatus.BLOCKED.value,
                handler_used=None,
                execution_time=time.time() - start_time,
                output=None,
                error=f"策略拒绝: {policy_output.policy_reason}",
                fallback_triggered=False
            )
            return execution_plan, dispatch_result
        
        # 策略要求确认
        if policy_output and policy_output.policy_result == "require_confirmation":
            execution_plan = ExecutionPlan(
                handler=router_output.chosen_handler,
                mode=DispatchMode.REAL.value,
                steps=["等待用户确认"],
                fallback=policy_output.fallback_action,
                expected_output="待确认"
            )
            dispatch_result = DispatchResult(
                status=FinalStatus.BLOCKED.value,
                handler_used=None,
                execution_time=time.time() - start_time,
                output=None,
                error=f"需要确认: {policy_output.policy_reason}",
                fallback_triggered=False
            )
            return execution_plan, dispatch_result
        
        # 策略降级
        if policy_output and policy_output.policy_result == "degrade":
            # 使用备用处理器
            if policy_output.fallback_action == "use_backup_handler" and router_output.fallback_handlers:
                handler_used = router_output.fallback_handlers[0]
                execution_plan = ExecutionPlan(
                    handler=handler_used,
                    mode=DispatchMode.DEGRADED.value,
                    steps=[f"降级使用备用处理器: {handler_used}"],
                    fallback=policy_output.fallback_action,
                    expected_output="降级执行结果"
                )
                dispatch_result = DispatchResult(
                    status=FinalStatus.DEGRADED.value,
                    handler_used=handler_used,
                    execution_time=time.time() - start_time,
                    output=f"[真实] 使用备用处理器 {handler_used} 执行",
                    error=None,
                    fallback_triggered=True
                )
            else:
                # 其他降级策略
                execution_plan = ExecutionPlan(
                    handler=router_output.chosen_handler,
                    mode=DispatchMode.DEGRADED.value,
                    steps=[f"降级策略: {policy_output.fallback_action}"],
                    fallback=policy_output.fallback_action,
                    expected_output="降级执行结果"
                )
                dispatch_result = DispatchResult(
                    status=FinalStatus.DEGRADED.value,
                    handler_used=router_output.chosen_handler,
                    execution_time=time.time() - start_time,
                    output=f"[真实] 降级执行: {policy_output.fallback_action}",
                    error=None,
                    fallback_triggered=True
                )
            return execution_plan, dispatch_result
        
        # 正常执行（第一版模拟）
        execution_plan = ExecutionPlan(
            handler=router_output.chosen_handler,
            mode=DispatchMode.REAL.value,
            steps=[
                f"1. 准备执行环境",
                f"2. 调用 {router_output.chosen_handler}",
                f"3. 收集执行结果",
                f"4. 回写状态"
            ],
            fallback=policy_output.fallback_action if policy_output else None,
            expected_output="执行成功"
        )
        
        dispatch_result = DispatchResult(
            status=FinalStatus.DISPATCHED.value,
            handler_used=router_output.chosen_handler,
            execution_time=time.time() - start_time,
            output=f"[真实] {router_output.chosen_handler} 执行成功",
            error=None,
            fallback_triggered=False
        )
        
        return execution_plan, dispatch_result
    
    def _observe(
        self,
        task_context: TaskContext,
        router_output,
        policy_output,
        dispatch_result: DispatchResult
    ) -> Dict[str, Any]:
        """观测执行结果"""
        return {
            'task_type': task_context.task_type,
            'priority': task_context.priority,
            'risk_level': task_context.risk_level,
            'router_confidence': router_output.confidence if router_output else 0,
            'policy_result': policy_output.policy_result if policy_output else None,
            'dispatch_status': dispatch_result.status,
            'execution_time': dispatch_result.execution_time,
            'fallback_triggered': dispatch_result.fallback_triggered
        }
    
    def _writeback(
        self,
        task_context: TaskContext,
        router_output,
        policy_output,
        execution_plan: Optional[ExecutionPlan],
        dispatch_result: DispatchResult
    ) -> Dict[str, Any]:
        """记忆回写"""
        writeback = {
            'timestamp': datetime.now().isoformat(),
            'input_summary': {
                'source': task_context.source,
                'task_type': task_context.task_type,
                'priority': task_context.priority,
                'risk_level': task_context.risk_level
            },
            'router_decision': {
                'situation': router_output.situation_type if router_output else None,
                'chosen_handler': router_output.chosen_handler if router_output else None,
                'confidence': router_output.confidence if router_output else 0,
                'reason': router_output.decision_reason if router_output else None
            },
            'policy_decision': {
                'result': policy_output.policy_result if policy_output else None,
                'reason': policy_output.policy_reason if policy_output else None,
                'fallback': policy_output.fallback_action if policy_output else None
            } if policy_output else None,
            'execution_plan': execution_plan.to_dict() if execution_plan else None,
            'dispatch_result': {
                'status': dispatch_result.status,
                'handler_used': dispatch_result.handler_used,
                'execution_time': dispatch_result.execution_time,
                'error': dispatch_result.error,
                'fallback_triggered': dispatch_result.fallback_triggered
            },
            'failure_reason': dispatch_result.error if dispatch_result.error else None
        }
        
        return writeback
    
    def _determine_final_status(self, policy_output, dispatch_result: DispatchResult) -> str:
        """确定最终状态"""
        return dispatch_result.status
    
    def process_and_log(self, task_context: TaskContext) -> DispatchDecision:
        """
        处理任务并记录
        
        Args:
            task_context: 任务上下文
            
        Returns:
            DispatchDecision: 完整派发决策记录
        """
        decision_record = self.process(task_context)
        
        decision = DispatchDecision(
            task_context=task_context,
            decision_record=decision_record,
            timestamp=datetime.now().isoformat(),
            dispatch_version=self.VERSION
        )
        
        # 记录日志
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(decision.to_dict(), ensure_ascii=False) + '\n')
        
        return decision
    
    def explain_decision(self, decision_record: DecisionRecord) -> str:
        """
        解释决策（回答5句话）
        
        1. 这次输入被识别成什么情况
        2. router 选了谁，为什么
        3. policy 是否放行，为什么
        4. 执行计划是什么
        5. 结果写回了什么，后续怎么复盘
        """
        lines = []
        
        # 1. 这次输入被识别成什么情况
        lines.append(f"【情况】{decision_record.current_situation}")
        
        # 2. router 选了谁，为什么
        if decision_record.chosen_handler:
            router_reason = decision_record.router_result.get('decision_reason', '未知')
            lines.append(f"【路由】选中 {decision_record.chosen_handler} - {router_reason}")
        else:
            lines.append("【路由】无可用处理器")
        
        # 3. policy 是否放行，为什么
        if decision_record.policy_result:
            policy_result = decision_record.policy_result.get('policy_result', 'unknown')
            policy_reason = decision_record.policy_result.get('policy_reason', '未知')
            
            result_map = {
                'auto_execute': '✅ 放行',
                'require_confirmation': '⚠️ 需要确认',
                'degrade': '⬇️ 降级',
                'reject': '❌ 拒绝'
            }
            lines.append(f"【策略】{result_map.get(policy_result, policy_result)} - {policy_reason}")
        else:
            lines.append("【策略】未执行策略检查")
        
        # 4. 执行计划是什么
        if decision_record.execution_plan:
            plan = decision_record.execution_plan
            lines.append(f"【计划】{plan.mode} 模式，{len(plan.steps)} 步骤")
        else:
            lines.append("【计划】无执行计划")
        
        # 5. 结果写回了什么，后续怎么复盘
        if decision_record.dispatch_result:
            result = decision_record.dispatch_result
            status_map = {
                'dispatched': '✅ 已派发',
                'degraded': '⬇️ 已降级',
                'blocked': '🚫 已拦截',
                'failed': '❌ 失败'
            }
            status_text = status_map.get(result.status, result.status)
            lines.append(f"【结果】{status_text}，耗时 {result.execution_time:.2f}s")
            
            if result.error:
                lines.append(f"【复盘】失败原因: {result.error}")
            elif result.fallback_triggered:
                lines.append(f"【复盘】触发降级，使用 {result.handler_used}")
            else:
                lines.append(f"【复盘】正常执行，记录已写回")
        else:
            lines.append("【结果】无派发结果")
        
        return '\n'.join(lines)


def main():
    """测试入口"""
    dispatcher = DecideAndDispatch()
    
    # 测试用例：普通监控任务
    task_context = TaskContext(
        source="heartbeat",
        task_type="monitor",
        content="检查系统健康状态",
        priority="normal",
        risk_level="low",
        system_state={"health_status": "healthy", "health_score": 85},
        recent_history=[],
        available_handlers=["aios-health-monitor", "pattern-detector"]
    )
    
    decision_record = dispatcher.process(task_context)
    print(dispatcher.explain_decision(decision_record))


if __name__ == "__main__":
    main()

