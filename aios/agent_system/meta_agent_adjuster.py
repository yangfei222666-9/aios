"""
Meta-Agent 自适应调整器
根据 Agent 执行数据自动调整任务频率和内容
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

class MetaAgentAdjuster:
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.agents_file = self.workspace / "aios" / "agent_system" / "data" / "agents.jsonl"
        self.execution_log = self.workspace / "aios" / "agent_system" / "data" / "execution_log.jsonl"
        self.adjustments_log = self.workspace / "aios" / "agent_system" / "data" / "meta_adjustments.jsonl"
        
    def analyze_agent_performance(self, agent_id: str, days: int = 7) -> dict:
        """分析 Agent 过去 N 天的表现"""
        cutoff = datetime.now() - timedelta(days=days)
        
        stats = {
            "total_runs": 0,
            "silent_runs": 0,  # 输出 *_OK 的次数
            "alert_runs": 0,   # 输出警告的次数
            "failed_runs": 0,
            "avg_duration": 0,
            "consecutive_silent": 0,
            "consecutive_alerts": 0
        }
        
        # 读取执行日志
        if not self.execution_log.exists():
            return stats
            
        with open(self.execution_log, 'r', encoding='utf-8') as f:
            recent_runs = []
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get('agent_id') == agent_id:
                    run_time = datetime.fromisoformat(entry.get('timestamp', ''))
                    if run_time > cutoff:
                        recent_runs.append(entry)
        
        if not recent_runs:
            return stats
            
        # 分析统计
        stats['total_runs'] = len(recent_runs)
        
        consecutive_silent = 0
        consecutive_alerts = 0
        
        for entry in reversed(recent_runs):  # 从最近的开始
            output = entry.get('output', '')
            duration = entry.get('duration_ms', 0)
            
            stats['avg_duration'] += duration
            
            if '_OK' in output or 'OK' == output.strip():
                stats['silent_runs'] += 1
                consecutive_silent += 1
                consecutive_alerts = 0
            elif 'WARNING' in output or 'ALERT' in output or 'CRITICAL' in output:
                stats['alert_runs'] += 1
                consecutive_alerts += 1
                consecutive_silent = 0
            elif 'FAILED' in output or 'ERROR' in output:
                stats['failed_runs'] += 1
                consecutive_silent = 0
                consecutive_alerts = 0
        
        stats['avg_duration'] = stats['avg_duration'] / stats['total_runs'] if stats['total_runs'] > 0 else 0
        stats['consecutive_silent'] = consecutive_silent
        stats['consecutive_alerts'] = consecutive_alerts
        
        return stats
    
    def suggest_adjustments(self, agent_id: str, agent_name: str, current_schedule: str) -> dict:
        """根据表现建议调整"""
        stats = self.analyze_agent_performance(agent_id)
        
        if stats['total_runs'] == 0:
            return None
            
        suggestion = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "current_schedule": current_schedule,
            "new_schedule": None,
            "reason": None,
            "confidence": 0.0
        }
        
        # 策略 1: 连续静默 → 降低频率
        if stats['consecutive_silent'] >= 10:
            suggestion['new_schedule'] = self._reduce_frequency(current_schedule)
            suggestion['reason'] = f"连续 {stats['consecutive_silent']} 次静默输出，降低检查频率"
            suggestion['confidence'] = 0.9
            
        # 策略 2: 连续告警 → 提高频率
        elif stats['consecutive_alerts'] >= 3:
            suggestion['new_schedule'] = self._increase_frequency(current_schedule)
            suggestion['reason'] = f"连续 {stats['consecutive_alerts']} 次告警，提高检查频率"
            suggestion['confidence'] = 0.95
            
        # 策略 3: 高失败率 → 需要人工介入
        elif stats['failed_runs'] / stats['total_runs'] > 0.3:
            suggestion['reason'] = f"失败率 {stats['failed_runs']/stats['total_runs']:.1%}，需要人工检查"
            suggestion['confidence'] = 0.8
            
        return suggestion if suggestion['new_schedule'] or suggestion['reason'] else None
    
    def _reduce_frequency(self, schedule: str) -> str:
        """降低频率（保守策略）"""
        # 简单实现：每小时 → 每2小时，每10分钟 → 每20分钟
        if "* * * *" in schedule:  # 每小时
            return schedule.replace("* * * *", "*/2 * * *")
        elif "*/10" in schedule:  # 每10分钟
            return schedule.replace("*/10", "*/20")
        return schedule
    
    def _increase_frequency(self, schedule: str) -> str:
        """提高频率（保守策略）"""
        # 简单实现：每2小时 → 每小时，每20分钟 → 每10分钟
        if "*/2 * * *" in schedule:
            return schedule.replace("*/2 * * *", "* * * *")
        elif "*/20" in schedule:
            return schedule.replace("*/20", "*/10")
        return schedule
    
    def log_adjustment(self, adjustment: dict):
        """记录调整日志"""
        self.adjustments_log.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            **adjustment
        }
        
        with open(self.adjustments_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    adjuster = MetaAgentAdjuster(Path.cwd())
    
    # 示例：分析 Monitor Agent
    stats = adjuster.analyze_agent_performance("monitor-agent", days=7)
    print(f"Monitor Agent 统计: {stats}")
    
    # 示例：建议调整
    suggestion = adjuster.suggest_adjustments("monitor-agent", "Monitor Agent", "0 * * * *")
    if suggestion:
        print(f"建议调整: {suggestion}")
