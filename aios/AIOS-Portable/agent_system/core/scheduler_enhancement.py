"""
Scheduler Enhancement - 基于卦象的调度决策增强
集成 PatternRecognizer 到任务调度系统
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加 agents 路径
agents_path = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(agents_path))

from pattern_recognizer_agent import PatternRecognizerAgent


class SchedulerEnhancement:
    """调度增强器 - 根据卦象调整任务选择策略"""
    
    def __init__(self):
        self.pattern_agent = PatternRecognizerAgent()
        self.current_pattern = None
        self.current_strategy = None
    
    def update_pattern(self) -> Dict:
        """更新当前卦象和策略"""
        result = self.pattern_agent.run()
        
        if result["status"] == "success":
            self.current_pattern = result["pattern"]
            self.current_strategy = result["strategy"]
        
        return result
    
    def should_accept_task(self, task: Dict) -> bool:
        """
        判断是否应该接受任务
        
        Args:
            task: 任务信息
                {
                    "type": "code" | "analysis" | "monitor",
                    "priority": "low" | "normal" | "high",
                    "complexity": "simple" | "medium" | "complex",
                    "risk": "low" | "medium" | "high",
                }
        
        Returns:
            True - 接受任务
            False - 拒绝任务
        """
        if not self.current_strategy:
            # 没有策略信息，默认接受
            return True
        
        risk_tolerance = self.current_strategy.get("risk_tolerance", "medium")
        task_risk = task.get("risk", "low")
        
        # 根据风险容忍度判断
        if risk_tolerance == "zero":
            # 零风险容忍度：只接受低风险任务
            return task_risk == "low"
        elif risk_tolerance == "very_low":
            # 极低风险容忍度：只接受低风险和部分中风险任务
            return task_risk in ["low", "medium"] and task.get("complexity") != "complex"
        elif risk_tolerance == "low":
            # 低风险容忍度：接受低风险和中风险任务
            return task_risk in ["low", "medium"]
        elif risk_tolerance == "medium":
            # 中等风险容忍度：接受所有任务，但优先低风险
            return True
        elif risk_tolerance == "high":
            # 高风险容忍度：接受所有任务，优先高风险高回报
            return True
        
        return True
    
    def adjust_task_priority(self, task: Dict) -> str:
        """
        调整任务优先级
        
        Args:
            task: 任务信息
        
        Returns:
            调整后的优先级 ("low" | "normal" | "high")
        """
        if not self.current_strategy:
            return task.get("priority", "normal")
        
        priority_mode = self.current_strategy.get("priority", "normal")
        original_priority = task.get("priority", "normal")
        task_type = task.get("type", "unknown")
        
        # 根据策略优先级调整
        if priority_mode == "survival":
            # 生存模式：只关注核心任务
            if task_type in ["monitor", "fix"]:
                return "high"
            else:
                return "low"
        
        elif priority_mode == "defense":
            # 防守模式：优先修复和监控
            if task_type in ["fix", "rollback", "monitor"]:
                return "high"
            elif task_type == "code":
                return "low"  # 暂停新开发
            else:
                return original_priority
        
        elif priority_mode == "growth":
            # 增长模式：优先新功能和优化
            if task_type in ["code", "optimize", "explore"]:
                return "high"
            else:
                return original_priority
        
        elif priority_mode == "expansion":
            # 扩张模式：优先挑战性任务
            if task.get("complexity") == "complex":
                return "high"
            else:
                return original_priority
        
        return original_priority
    
    def select_model(self, task: Dict) -> str:
        """
        选择合适的模型
        
        Args:
            task: 任务信息
        
        Returns:
            模型名称 ("haiku" | "sonnet" | "opus")
        """
        if not self.current_strategy:
            return "sonnet"  # 默认
        
        model_preference = self.current_strategy.get("model_preference", "sonnet")
        task_complexity = task.get("complexity", "medium")
        
        # 根据策略和任务复杂度选择模型
        if model_preference == "haiku":
            # 快速模式：优先使用 haiku
            if task_complexity == "complex":
                return "sonnet"  # 复杂任务升级到 sonnet
            else:
                return "haiku"
        
        elif model_preference == "sonnet":
            # 平衡模式：根据复杂度选择
            if task_complexity == "simple":
                return "haiku"
            elif task_complexity == "complex":
                return "opus"
            else:
                return "sonnet"
        
        elif model_preference == "opus":
            # 高性能模式：优先使用 opus
            if task_complexity == "simple":
                return "sonnet"  # 简单任务降级到 sonnet
            else:
                return "opus"
        
        return "sonnet"
    
    def get_recommended_actions(self) -> List[str]:
        """获取当前推荐的行动列表"""
        if not self.current_strategy:
            return []
        
        return self.current_strategy.get("actions", [])
    
    def get_status_summary(self) -> Dict:
        """获取当前状态摘要"""
        return {
            "pattern": self.current_pattern,
            "strategy": self.current_strategy.get("priority") if self.current_strategy else None,
            "risk_tolerance": self.current_strategy.get("risk_tolerance") if self.current_strategy else None,
            "model_preference": self.current_strategy.get("model_preference") if self.current_strategy else None,
        }


# 测试
if __name__ == "__main__":
    print("=== Scheduler Enhancement 测试 ===\n")
    
    enhancer = SchedulerEnhancement()
    
    # 更新卦象
    print("1. 更新当前卦象...")
    result = enhancer.update_pattern()
    print(f"   状态: {result['status']}")
    print(f"   消息: {result.get('message', 'N/A')}")
    
    if result["status"] == "success":
        print(f"\n2. 当前策略:")
        summary = enhancer.get_status_summary()
        print(f"   卦象: {summary['pattern']}")
        print(f"   策略: {summary['strategy']}")
        print(f"   风险容忍度: {summary['risk_tolerance']}")
        print(f"   模型偏好: {summary['model_preference']}")
        
        # 测试任务决策
        print(f"\n3. 测试任务决策:")
        
        test_tasks = [
            {"type": "code", "priority": "normal", "complexity": "complex", "risk": "high"},
            {"type": "fix", "priority": "high", "complexity": "simple", "risk": "low"},
            {"type": "monitor", "priority": "low", "complexity": "simple", "risk": "low"},
        ]
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n   任务{i}: {task['type']} (复杂度: {task['complexity']}, 风险: {task['risk']})")
            accept = enhancer.should_accept_task(task)
            priority = enhancer.adjust_task_priority(task)
            model = enhancer.select_model(task)
            print(f"     接受: {accept}")
            print(f"     优先级: {task['priority']} → {priority}")
            print(f"     模型: {model}")
