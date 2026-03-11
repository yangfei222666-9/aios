"""
State Vocabulary Adapter v1.0
统一状态推导入口，防止多个消费者各自推导导致状态漂移

职责：
1. 从旧字段推导新词表（readiness / run / health / derivation）
2. 处理边界值（no-sample / unknown / not-evaluable）
3. 提供统一 helper（get_agent_state / get_task_state / get_lesson_state）

设计原则：
- 单一真相源（Single Source of Truth）
- 边界值优先（no-sample / unknown / not-evaluable 先判断）
- 语义稳定（不同消费者调用同一逻辑，保证口径一致）
"""

from typing import Dict, Any, Optional
from datetime import datetime


class StateVocabularyAdapter:
    """状态词表适配器"""
    
    # ==================== Agent 状态推导 ====================
    
    @staticmethod
    def get_agent_state(agent: Dict[str, Any]) -> Dict[str, str]:
        """
        从 Agent 数据推导三维状态
        
        返回：
        {
            "readiness": "registered / executable / validated / production-ready / stable",
            "run": "never-run / idle / running / completed / failed",
            "health": "healthy / degraded / critical / no-sample / not-evaluable"
        }
        """
        readiness = StateVocabularyAdapter._infer_agent_readiness(agent)
        run = StateVocabularyAdapter._infer_agent_run(agent)
        health = StateVocabularyAdapter._infer_agent_health(agent)
        
        return {
            "readiness": readiness,
            "run": run,
            "health": health
        }
    
    @staticmethod
    def _infer_agent_readiness(agent: Dict[str, Any]) -> str:
        """推导 Agent readiness 状态"""
        # 1. 检查是否已注册（有 name 或 id）
        if not agent.get("name") and not agent.get("id"):
            return "not-registered"
        
        # 2. 检查是否被禁用或归档
        if not agent.get("enabled", False) or agent.get("mode") == "disabled":
            return "archived"
        
        # 3. 检查是否是 shadow 模式
        if agent.get("mode") == "shadow":
            return "shadow"
        
        # 4. 检查是否可执行（有 entry_point 或 run_script）
        has_entry = agent.get("entry_point") or agent.get("run_script")
        
        # 5. 检查是否已验证（有验证记录或 production_ready 标记）
        is_validated = agent.get("validated_at") or agent.get("production_ready", False)
        
        # 6. 检查是否生产就绪（有成功执行记录）
        stats = agent.get("stats", {})
        has_runs = stats.get("tasks_completed", 0) > 0
        
        # 7. 检查是否稳定（连续成功 >= 3 次）
        is_stable = stats.get("consecutive_success", 0) >= 3
        
        # 状态判断逻辑
        if is_stable and has_runs:
            return "stable"
        elif is_validated and has_runs:
            return "production-ready"
        elif is_validated:
            return "validated"
        elif has_entry:
            return "executable"
        else:
            return "registered"
    
    @staticmethod
    def _infer_agent_run(agent: Dict[str, Any]) -> str:
        """推导 Agent run 状态"""
        stats = agent.get("stats", {})
        
        # 1. 检查是否从未运行
        if stats.get("tasks_completed", 0) == 0 and stats.get("tasks_failed", 0) == 0:
            return "never-run"
        
        # 2. 检查最近执行状态
        last_run = agent.get("last_run")
        if not last_run:
            return "idle"
        
        # 3. 检查是否正在运行（最近 5 分钟内有执行记录）
        try:
            last_run_time = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            now = datetime.now(last_run_time.tzinfo)
            if (now - last_run_time).total_seconds() < 300:  # 5 分钟
                return "running"
        except:
            pass
        
        # 4. 检查最后一次执行结果
        if stats.get("tasks_failed", 0) > stats.get("tasks_completed", 0):
            return "failed"
        
        return "completed"
    
    @staticmethod
    def _infer_agent_health(agent: Dict[str, Any]) -> str:
        """推导 Agent health 状态"""
        stats = agent.get("stats", {})
        
        # 1. 边界值：无样本（从未运行）
        if stats.get("tasks_completed", 0) == 0 and stats.get("tasks_failed", 0) == 0:
            return "no-sample"
        
        # 2. 边界值：不可评估（数据不足）
        total_tasks = stats.get("tasks_completed", 0) + stats.get("tasks_failed", 0)
        if total_tasks < 3:
            return "not-evaluable"
        
        # 3. 计算成功率
        success_rate = stats.get("tasks_completed", 0) / total_tasks if total_tasks > 0 else 0
        
        # 4. 判断健康度
        if success_rate >= 0.8:
            return "healthy"
        elif success_rate >= 0.5:
            return "degraded"
        else:
            return "critical"
    
    # ==================== Task 状态推导 ====================
    
    @staticmethod
    def get_task_state(task: Dict[str, Any]) -> Dict[str, str]:
        """
        从 Task 数据推导状态
        
        返回：
        {
            "status": "pending / queued / running / completed / failed / unknown",
            "health": "healthy / degraded / critical / no-sample / not-evaluable"
        }
        """
        status = task.get("status", "unknown")
        health = StateVocabularyAdapter._infer_task_health(task)
        
        return {
            "status": status,
            "health": health
        }
    
    @staticmethod
    def _infer_task_health(task: Dict[str, Any]) -> str:
        """推导 Task health 状态"""
        status = task.get("status", "unknown")
        
        # 1. 边界值：未执行
        if status in ["pending", "queued"]:
            return "no-sample"
        
        # 2. 边界值：执行中
        if status == "running":
            return "not-evaluable"
        
        # 3. 判断健康度
        if status == "completed":
            return "healthy"
        elif status == "failed":
            return "critical"
        else:
            return "unknown"
    
    # ==================== Lesson 状态推导 ====================
    
    @staticmethod
    def get_lesson_state(lesson: Dict[str, Any]) -> Dict[str, str]:
        """
        从 Lesson 数据推导状态
        
        返回：
        {
            "derivation": "pending / extracted / validated / applied / archived",
            "health": "healthy / degraded / critical / no-sample / not-evaluable"
        }
        """
        derivation = lesson.get("status", "pending")
        health = StateVocabularyAdapter._infer_lesson_health(lesson)
        
        return {
            "derivation": derivation,
            "health": health
        }
    
    @staticmethod
    def _infer_lesson_health(lesson: Dict[str, Any]) -> str:
        """推导 Lesson health 状态"""
        status = lesson.get("status", "pending")
        
        # 1. 边界值：未提炼
        if status == "pending":
            return "no-sample"
        
        # 2. 边界值：已提炼但未验证
        if status == "extracted":
            return "not-evaluable"
        
        # 3. 判断健康度
        if status in ["validated", "applied"]:
            return "healthy"
        elif status == "archived":
            return "degraded"
        else:
            return "unknown"
    
    # ==================== 批量处理 ====================
    
    @staticmethod
    def get_agents_states(agents: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """批量推导 Agent 状态"""
        return [
            {**agent, "state": StateVocabularyAdapter.get_agent_state(agent)}
            for agent in agents
        ]
    
    @staticmethod
    def get_tasks_states(tasks: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """批量推导 Task 状态"""
        return [
            {**task, "state": StateVocabularyAdapter.get_task_state(task)}
            for task in tasks
        ]
    
    @staticmethod
    def get_lessons_states(lessons: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """批量推导 Lesson 状态"""
        return [
            {**lesson, "state": StateVocabularyAdapter.get_lesson_state(lesson)}
            for lesson in lessons
        ]


# ==================== 便捷函数 ====================

def get_agent_state(agent: Dict[str, Any]) -> Dict[str, str]:
    """便捷函数：推导 Agent 状态"""
    return StateVocabularyAdapter.get_agent_state(agent)


def get_task_state(task: Dict[str, Any]) -> Dict[str, str]:
    """便捷函数：推导 Task 状态"""
    return StateVocabularyAdapter.get_task_state(task)


def get_lesson_state(lesson: Dict[str, Any]) -> Dict[str, str]:
    """便捷函数：推导 Lesson 状态"""
    return StateVocabularyAdapter.get_lesson_state(lesson)


def get_agents_states(agents: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """便捷函数：批量推导 Agent 状态"""
    return StateVocabularyAdapter.get_agents_states(agents)


def get_tasks_states(tasks: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """便捷函数：批量推导 Task 状态"""
    return StateVocabularyAdapter.get_tasks_states(tasks)


def get_lessons_states(lessons: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """便捷函数：批量推导 Lesson 状态"""
    return StateVocabularyAdapter.get_lessons_states(lessons)
