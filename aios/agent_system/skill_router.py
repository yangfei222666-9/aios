"""
Skill Router - 技能路由器

作用：回答"现在发生了什么，该由谁处理，为什么这么处理"

三层判定：
- L0：信号过滤
- L1：上下文匹配
- L2：最终路由决策
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from skill_router_schema import (
    TaskContext, RouterOutput, CandidateHandler, RoutingDecision,
    TaskType, Priority, RiskLevel
)


class SkillRouter:
    """技能路由器 v1.0"""
    
    VERSION = "1.0.0"
    
    def __init__(self, skills_registry_path: Optional[Path] = None):
        """
        初始化路由器
        
        Args:
            skills_registry_path: 技能注册表路径（可选）
        """
        self.skills_registry_path = skills_registry_path or Path(__file__).parent / "data" / "skills_registry.json"
        self.skills_registry = self._load_skills_registry()
        
    def _load_skills_registry(self) -> Dict[str, Any]:
        """加载技能注册表"""
        if not self.skills_registry_path.exists():
            # 默认注册表
            return {
                "github-repo-analyzer": {
                    "capabilities": ["github_analysis", "repo_structure", "architecture_review"],
                    "task_types": ["learning", "analysis"],
                    "risk_level": "safe",
                    "success_rate": 0.95,
                    "avg_duration": 30
                },
                "pattern-detector": {
                    "capabilities": ["pattern_detection", "anomaly_detection", "trend_analysis"],
                    "task_types": ["analysis", "monitor"],
                    "risk_level": "safe",
                    "success_rate": 0.88,
                    "avg_duration": 15
                },
                "lesson-extractor": {
                    "capabilities": ["lesson_extraction", "knowledge_synthesis", "experience_distillation"],
                    "task_types": ["learning", "analysis"],
                    "risk_level": "safe",
                    "success_rate": 0.92,
                    "avg_duration": 20
                },
                "aios-health-monitor": {
                    "capabilities": ["health_check", "system_diagnosis", "metric_analysis"],
                    "task_types": ["monitor", "alert"],
                    "risk_level": "safe",
                    "success_rate": 0.98,
                    "avg_duration": 10
                },
                "agent-performance-analyzer": {
                    "capabilities": ["performance_analysis", "agent_evaluation", "optimization_recommendation"],
                    "task_types": ["analysis", "monitor"],
                    "risk_level": "safe",
                    "success_rate": 0.90,
                    "avg_duration": 25
                },
                "backup-restore-manager": {
                    "capabilities": ["backup", "restore", "disaster_recovery", "data_integrity"],
                    "task_types": ["backup", "monitor"],
                    "risk_level": "medium",
                    "success_rate": 0.96,
                    "avg_duration": 45
                }
            }
        
        with open(self.skills_registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def route(self, task_context: TaskContext) -> RouterOutput:
        """
        执行路由决策
        
        Args:
            task_context: 任务上下文
            
        Returns:
            RouterOutput: 路由决策结果
        """
        # L0: 信号过滤
        situation_type = self._classify_situation(task_context)
        
        # L1: 上下文匹配
        candidates = self._match_candidates(task_context)
        
        # L2: 最终路由决策
        chosen_handler, decision_reason, rejected_handlers, confidence, fallback_handlers = \
            self._make_final_decision(task_context, candidates)
        
        return RouterOutput(
            situation_type=situation_type,
            candidates=candidates,
            chosen_handler=chosen_handler,
            decision_reason=decision_reason,
            rejected_handlers=rejected_handlers,
            confidence=confidence,
            fallback_handlers=fallback_handlers,
            routing_metadata={
                "router_version": self.VERSION,
                "timestamp": datetime.now().isoformat(),
                "total_candidates": len(candidates),
                "filtered_count": len(task_context.available_handlers) - len(candidates)
            }
        )
    
    def _classify_situation(self, task_context: TaskContext) -> str:
        """
        L0: 信号过滤 - 分类当前情况
        
        Args:
            task_context: 任务上下文
            
        Returns:
            str: 情况类型
        """
        # 根据任务类型、优先级、风险等级分类
        task_type = task_context.task_type
        priority = task_context.priority
        risk_level = task_context.risk_level
        
        # 紧急情况
        if priority == Priority.CRITICAL.value:
            return f"critical_{task_type}"
        
        # 高风险情况
        if risk_level == RiskLevel.HIGH.value:
            return f"high_risk_{task_type}"
        
        # 常规情况
        return f"routine_{task_type}"
    
    def _match_candidates(self, task_context: TaskContext) -> List[CandidateHandler]:
        """
        L1: 上下文匹配 - 找出所有候选处理器
        
        Args:
            task_context: 任务上下文
            
        Returns:
            List[CandidateHandler]: 候选处理器列表
        """
        candidates = []
        
        for handler_name in task_context.available_handlers:
            if handler_name not in self.skills_registry:
                continue
            
            skill_info = self.skills_registry[handler_name]
            
            # 能力匹配
            capability_match = self._check_capability_match(task_context, skill_info)
            
            # 上下文匹配
            context_match = self._check_context_match(task_context, skill_info)
            
            # 历史表现分数
            history_score = skill_info.get('success_rate', 0.5) * 100
            
            # 计算匹配分数
            l0_score = 0.0  # L0 暂不单独计分
            l1_score = self._calculate_l1_score(capability_match, context_match)
            l2_score = history_score * 0.3
            match_score = self._calculate_match_score(
                capability_match, context_match, history_score, task_context, skill_info
            )
            
            # 匹配原因
            match_reasons = self._get_match_reasons(
                capability_match, context_match, history_score, task_context, skill_info
            )
            
            # 拒绝原因（如果有）
            reject_reasons = self._get_reject_reasons(
                capability_match, context_match, task_context, skill_info
            )
            
            candidates.append(CandidateHandler(
                handler_name=handler_name,
                match_score=match_score,
                match_reasons=match_reasons,
                reject_reasons=reject_reasons,
                capability_match=capability_match,
                context_match=context_match,
                history_score=history_score,
                l0_score=l0_score,
                l1_score=l1_score,
                l2_score=l2_score,
                final_score=match_score
            ))
        
        # 按匹配分数排序
        candidates.sort(key=lambda c: c.match_score, reverse=True)
        
        return candidates
    
    def _check_capability_match(self, task_context: TaskContext, skill_info: Dict[str, Any]) -> bool:
        """检查能力匹配"""
        task_type = task_context.task_type
        skill_task_types = skill_info.get('task_types', [])
        return task_type in skill_task_types
    
    def _check_context_match(self, task_context: TaskContext, skill_info: Dict[str, Any]) -> bool:
        """检查上下文匹配"""
        # 风险等级匹配
        task_risk = task_context.risk_level
        skill_risk = skill_info.get('risk_level', 'safe')
        
        # 高风险任务不能由低风险技能处理
        risk_order = {'safe': 0, 'low': 1, 'medium': 2, 'high': 3}
        if risk_order.get(task_risk, 0) > risk_order.get(skill_risk, 0):
            return False
        
        return True
    
    def _calculate_l1_score(self, capability_match: bool, context_match: bool) -> float:
        """计算 L1 上下文匹配分数"""
        score = 0.0
        if capability_match:
            score += 40.0
        if context_match:
            score += 30.0
        return score
    
    def _calculate_match_score(
        self, 
        capability_match: bool, 
        context_match: bool, 
        history_score: float,
        task_context: TaskContext,
        skill_info: Dict[str, Any]
    ) -> float:
        """计算匹配分数（0-100）"""
        score = 0.0
        
        # 能力匹配（40分）
        if capability_match:
            score += 40.0
        
        # 上下文匹配（30分）
        if context_match:
            score += 30.0
        
        # 历史表现（30分）
        score += history_score * 0.3
        
        # 优先级加权
        if task_context.priority == Priority.CRITICAL.value:
            # 关键任务优先选择高成功率的
            score = score * 0.7 + history_score * 0.3
        
        return round(score, 2)
    
    def _get_match_reasons(
        self,
        capability_match: bool,
        context_match: bool,
        history_score: float,
        task_context: TaskContext,
        skill_info: Dict[str, Any]
    ) -> List[str]:
        """获取匹配原因"""
        reasons = []
        
        if capability_match:
            reasons.append(f"支持任务类型: {task_context.task_type}")
        
        if context_match:
            reasons.append(f"风险等级匹配: {skill_info.get('risk_level', 'safe')}")
        
        if history_score >= 90:
            reasons.append(f"历史表现优秀: {history_score:.1f}%")
        elif history_score >= 70:
            reasons.append(f"历史表现良好: {history_score:.1f}%")
        
        return reasons
    
    def _get_reject_reasons(
        self,
        capability_match: bool,
        context_match: bool,
        task_context: TaskContext,
        skill_info: Dict[str, Any]
    ) -> List[str]:
        """获取拒绝原因"""
        reasons = []
        
        if not capability_match:
            reasons.append(f"[能力不匹配] 不支持任务类型: {task_context.task_type}")
        
        if not context_match:
            reasons.append(f"[场景不匹配] 风险等级不匹配: 任务{task_context.risk_level} vs 技能{skill_info.get('risk_level', 'safe')}")
        
        return reasons
    
    def _make_final_decision(
        self,
        task_context: TaskContext,
        candidates: List[CandidateHandler]
    ) -> tuple:
        """
        L2: 最终路由决策
        
        Returns:
            (chosen_handler, decision_reason, rejected_handlers, confidence, fallback_handlers)
        """
        if not candidates:
            return (
                None,
                "无可用处理器",
                [],
                0.0,
                []
            )
        
        # 过滤掉匹配分数过低的候选
        valid_candidates = [c for c in candidates if c.match_score >= 40.0]
        
        if not valid_candidates:
            return (
                None,
                f"所有候选匹配分数过低（最高: {candidates[0].match_score:.1f}）",
                [{"handler": c.handler_name, "reasons": c.reject_reasons or ["匹配分数过低"]} for c in candidates],
                0.0,
                []
            )
        
        # 选择最高分
        chosen = valid_candidates[0]
        
        # 决策原因
        decision_reason = f"选择 {chosen.handler_name}（匹配分数: {chosen.match_score:.1f}）- " + \
                         "; ".join(chosen.match_reasons)
        
        # 被拒绝的处理器
        rejected_handlers = []
        for c in valid_candidates[1:]:
            rejected_handlers.append({
                "handler": c.handler_name,
                "score": c.match_score,
                "reasons": [f"分数低于首选（{c.match_score:.1f} < {chosen.match_score:.1f}）"]
            })
        
        # 置信度
        confidence = chosen.match_score
        
        # 备选处理器
        fallback_handlers = [c.handler_name for c in valid_candidates[1:3]]  # 最多2个备选
        
        return (
            chosen.handler_name,
            decision_reason,
            rejected_handlers,
            confidence,
            fallback_handlers
        )
    
    def route_and_log(self, task_context: TaskContext, log_path: Optional[Path] = None) -> RoutingDecision:
        """
        执行路由并记录决策
        
        Args:
            task_context: 任务上下文
            log_path: 日志路径（可选）
            
        Returns:
            RoutingDecision: 完整路由决策记录
        """
        router_output = self.route(task_context)
        
        decision = RoutingDecision(
            task_context=task_context,
            router_output=router_output,
            timestamp=datetime.now().isoformat(),
            router_version=self.VERSION
        )
        
        # 记录日志
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(decision.to_dict(), ensure_ascii=False) + '\n')
        
        return decision
    
    def explain_decision(self, router_output: RouterOutput) -> str:
        """
        解释路由决策（回答4句话）
        
        1. 现在发生了什么
        2. 哪些 handler 入围了
        3. 为什么选这个
        4. 为什么别的没选
        """
        lines = []
        
        # 1. 现在发生了什么
        lines.append(f"【情况】{router_output.situation_type}")
        
        # 2. 哪些 handler 入围了
        if router_output.candidates:
            candidate_names = [c.handler_name for c in router_output.candidates if c.match_score >= 40.0]
            lines.append(f"【候选】{len(candidate_names)} 个入围: {', '.join(candidate_names)}")
        else:
            lines.append("【候选】无入围")
        
        # 3. 为什么选这个
        if router_output.chosen_handler:
            lines.append(f"【选中】{router_output.decision_reason}")
        else:
            lines.append(f"【选中】无 - {router_output.decision_reason}")
        
        # 4. 为什么别的没选
        if router_output.rejected_handlers:
            reject_summary = []
            for r in router_output.rejected_handlers[:3]:  # 最多显示3个
                reasons = ', '.join(r.get('reasons', []))
                reject_summary.append(f"{r['handler']}: {reasons}")
            lines.append(f"【拒绝】{'; '.join(reject_summary)}")
        else:
            lines.append("【拒绝】无其他候选")
        
        return '\n'.join(lines)


def main():
    """测试入口"""
    router = SkillRouter()
    
    # 测试用例
    task_context = TaskContext(
        source="heartbeat",
        task_type="monitor",
        content="检查系统健康状态",
        priority="normal",
        risk_level="safe",
        system_state={"health_score": 85},
        recent_history=[],
        available_handlers=list(router.skills_registry.keys())
    )
    
    output = router.route(task_context)
    print(router.explain_decision(output))


if __name__ == "__main__":
    main()
