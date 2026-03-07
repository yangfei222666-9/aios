"""
Experience Library - Phase 3 适配层
桥接 camera.py 和 AIOS experience_learner_v3.py
"""

import sys
from pathlib import Path

# 添加 AIOS agent_system 到路径
aios_path = Path(__file__).parent.parent.parent / "aios" / "agent_system"
sys.path.insert(0, str(aios_path))

try:
    from experience_learner_v3 import learner_v3
    EXPERIENCE_AVAILABLE = True
except ImportError:
    EXPERIENCE_AVAILABLE = False
    print("[WARN] experience_learner_v3 not available, Phase 3 learning disabled")


class ExperienceLibrary:
    """经验库适配器"""
    
    def __init__(self):
        self.learner = learner_v3 if EXPERIENCE_AVAILABLE else None
    
    def record_failure(self, task_id: str, error: Exception, context: dict):
        """
        记录失败并触发学习
        
        Args:
            task_id: 任务ID（如 "camera_analyze"）
            error: 异常对象
            context: 上下文信息（delay, suggest, prompt_used 等）
        """
        if not self.learner:
            print(f"[EXPERIENCE] Learning disabled, failure recorded locally only")
            return
        
        # 构造任务字典（适配 experience_learner_v3 的格式）
        task = {
            'id': task_id,
            'error_type': type(error).__name__,
            'prompt': context.get('prompt_used', ''),
            'delay': context.get('delay', 0),
            'suggest': context.get('suggest', '')
        }
        
        # 推荐策略（从历史成功轨迹学习）
        enhanced_task = self.learner.recommend(task)
        
        print(f"[EXPERIENCE] Failure recorded: {task_id}")
        print(f"[EXPERIENCE] Error type: {task['error_type']}")
        print(f"[EXPERIENCE] Recommended strategy: {enhanced_task.get('enhanced_prompt', 'N/A')}")
        
        # 注意：这里只是记录失败，实际的重生逻辑由 LowSuccess_Agent 处理
        # 如果需要立即重试，可以在这里调用 learner.save_success()
    
    def record_success(self, task_id: str, strategy: str, duration: float, success_rate: float = 1.0):
        """
        记录成功轨迹
        
        Args:
            task_id: 任务ID
            strategy: 使用的策略
            duration: 执行时长
            success_rate: 成功率（0-1）
        """
        if not self.learner:
            return
        
        task_result = {
            'id': task_id,
            'error_type': 'camera_error',  # 通用类型
            'strategy': strategy,
            'duration': duration,
            'success_rate': success_rate,
            'prompt': f"Camera task {task_id} completed successfully"
        }
        
        self.learner.save_success(task_result)
        print(f"[EXPERIENCE] Success recorded: {task_id} (strategy: {strategy})")


# 全局单例
experience = ExperienceLibrary()
