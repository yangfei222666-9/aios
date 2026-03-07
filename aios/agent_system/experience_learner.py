# experience_learner.py - Phase 3: 从经验库学习并自动应用
import json
from collections import defaultdict
from datetime import datetime

class ExperienceLearner:
    def __init__(self):
        self.library_file = 'experience_library.jsonl'
        self.patterns = self.load_patterns()
    
    def load_patterns(self):
        """加载历史成功模式"""
        patterns = defaultdict(list)
        try:
            with open(self.library_file, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get('success'):
                        key = entry.get('error_type', 'unknown')
                        patterns[key].append(entry.get('strategy_used', 'default'))
        except:
            pass
        return patterns
    
    def learn_and_recommend(self, task):
        """自动学习 + 推荐历史成功策略"""
        error_type = task.get('error_type', 'unknown')
        if error_type in self.patterns and self.patterns[error_type]:
            # 投票选最优策略
            recommended = max(set(self.patterns[error_type]), 
                            key=self.patterns[error_type].count)
            task['enhanced_prompt'] = f"[LEARNED_FROM_HISTORY] 历史相同错误类型成功策略: {recommended}\n原prompt: {task.get('prompt', '')}"
            print(f"✅ [LEARN] 为 {error_type} 类型任务推荐历史策略: {recommended}")
            return task
        return task
    
    def save_success(self, task_result):
        """成功后永久保存新轨迹"""
        with open(self.library_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "error_type": task_result.get('error_type'),
                "strategy_used": task_result.get('strategy'),
                "task_id": task_result.get('id'),
                "regen_time": task_result.get('duration', 0)
            }, ensure_ascii=False) + '\n')
        print(f"📚 [SAVE] 新成功轨迹已存入experience_library.jsonl")

# 全局实例
learner = ExperienceLearner()
