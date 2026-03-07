"""
AIOS Agent Evolution System - Phase 1
Agent 自主进化系统

核心功能：
1. 任务执行追踪
2. 失败分析和改进建议
3. Prompt 自动优化
4. 进化历史记录
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


class AgentEvolution:
    """Agent 进化引擎"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path.home() / ".openclaw" / "workspace" / "aios" / "agent_system" / "data"
        
        self.data_dir = Path(data_dir)
        self.evolution_dir = self.data_dir / "evolution"
        self.evolution_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件
        self.task_log_file = self.evolution_dir / "task_executions.jsonl"
        self.evolution_log_file = self.evolution_dir / "evolution_history.jsonl"
        self.suggestions_file = self.evolution_dir / "improvement_suggestions.jsonl"

    def log_task_execution(
        self,
        agent_id: str,
        task_type: str,
        success: bool,
        duration_sec: float,
        error_msg: str = None,
        context: Dict = None
    ):
        """
        记录任务执行结果

        Args:
            agent_id: Agent ID
            task_type: 任务类型（code/analysis/monitor/research）
            success: 是否成功
            duration_sec: 执行时长
            error_msg: 错误信息（如果失败）
            context: 额外上下文（工具使用、模型调用等）
        """
        record = {
            "timestamp": int(time.time()),
            "agent_id": agent_id,
            "task_type": task_type,
            "success": success,
            "duration_sec": duration_sec,
            "error_msg": error_msg,
            "context": context or {}
        }

        with open(self.task_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def analyze_failures(self, agent_id: str, lookback_hours: int = 24) -> Dict:
        """
        分析 Agent 的失败模式

        Args:
            agent_id: Agent ID
            lookback_hours: 回溯时间（小时）

        Returns:
            {
                'total_tasks': int,
                'failed_tasks': int,
                'failure_rate': float,
                'failure_patterns': {
                    'task_type': {'count': int, 'errors': [str]},
                    ...
                },
                'suggestions': [str]
            }
        """
        if not self.task_log_file.exists():
            return {"total_tasks": 0, "failed_tasks": 0, "failure_rate": 0.0}

        cutoff_time = int(time.time()) - (lookback_hours * 3600)
        
        total_tasks = 0
        failed_tasks = 0
        failure_patterns = defaultdict(lambda: {"count": 0, "errors": []})

        with open(self.task_log_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                
                if record["agent_id"] != agent_id:
                    continue
                
                if record["timestamp"] < cutoff_time:
                    continue
                
                total_tasks += 1
                
                if not record["success"]:
                    failed_tasks += 1
                    task_type = record["task_type"]
                    failure_patterns[task_type]["count"] += 1
                    if record.get("error_msg"):
                        failure_patterns[task_type]["errors"].append(record["error_msg"])

        failure_rate = failed_tasks / total_tasks if total_tasks > 0 else 0.0

        # 生成改进建议
        suggestions = self._generate_suggestions(failure_patterns, failure_rate)

        return {
            "total_tasks": total_tasks,
            "failed_tasks": failed_tasks,
            "failure_rate": failure_rate,
            "failure_patterns": dict(failure_patterns),
            "suggestions": suggestions
        }

    def _generate_suggestions(self, failure_patterns: Dict, failure_rate: float) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 高失败率 → 建议调整 thinking level
        if failure_rate > 0.3:
            suggestions.append("失败率过高（>30%），建议提升 thinking level 到 'medium' 或 'high'")

        # 特定任务类型失败多 → 建议添加技能或调整工具权限
        for task_type, data in failure_patterns.items():
            if data["count"] >= 3:
                suggestions.append(f"{task_type} 任务失败 {data['count']} 次，建议：")
                
                if task_type == "code":
                    suggestions.append("  - 添加 'coding-agent' 技能")
                    suggestions.append("  - 确保 'exec', 'read', 'write', 'edit' 工具权限")
                
                elif task_type == "analysis":
                    suggestions.append("  - 添加数据分析相关技能")
                    suggestions.append("  - 确保 'web_search', 'web_fetch' 工具权限")
                
                elif task_type == "monitor":
                    suggestions.append("  - 添加 'system-resource-monitor' 技能")
                    suggestions.append("  - 确保 'exec' 工具权限")

        # 常见错误模式分析
        all_errors = []
        for data in failure_patterns.values():
            all_errors.extend(data["errors"])
        
        if any("timeout" in err.lower() for err in all_errors):
            suggestions.append("检测到超时错误，建议增加任务超时时间")
        
        if any("permission" in err.lower() for err in all_errors):
            suggestions.append("检测到权限错误，建议检查工具权限配置")
        
        if any("502" in err or "rate limit" in err.lower() for err in all_errors):
            suggestions.append("检测到 API 限流，建议添加重试机制或降低请求频率")

        return suggestions

    def save_suggestion(self, agent_id: str, suggestion: Dict):
        """
        保存改进建议

        Args:
            agent_id: Agent ID
            suggestion: {
                'type': 'prompt_update' | 'tool_permission' | 'skill_install' | 'parameter_tune',
                'description': str,
                'changes': Dict,
                'status': 'pending' | 'approved' | 'rejected' | 'applied'
            }
        """
        record = {
            "timestamp": int(time.time()),
            "agent_id": agent_id,
            **suggestion
        }

        with open(self.suggestions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_pending_suggestions(self, agent_id: str = None) -> List[Dict]:
        """获取待审核的改进建议"""
        if not self.suggestions_file.exists():
            return []

        suggestions = []
        with open(self.suggestions_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                
                if agent_id and record["agent_id"] != agent_id:
                    continue
                
                if record.get("status") == "pending":
                    suggestions.append(record)

        return suggestions

    def apply_evolution(self, agent_id: str, evolution: Dict) -> bool:
        """
        应用进化改进

        Args:
            agent_id: Agent ID
            evolution: {
                'type': str,
                'changes': Dict,
                'reason': str
            }

        Returns:
            是否成功
        """
        # 记录进化历史
        record = {
            "timestamp": int(time.time()),
            "agent_id": agent_id,
            "evolution_type": evolution["type"],
            "changes": evolution["changes"],
            "reason": evolution.get("reason", ""),
            "applied_at": datetime.now().isoformat()
        }

        with open(self.evolution_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return True

    def get_evolution_history(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """获取 Agent 的进化历史"""
        if not self.evolution_log_file.exists():
            return []

        history = []
        with open(self.evolution_log_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                
                if record["agent_id"] == agent_id:
                    history.append(record)

        # 按时间倒序
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]

    def generate_evolution_report(self, agent_id: str) -> str:
        """生成 Agent 进化报告"""
        analysis = self.analyze_failures(agent_id, lookback_hours=24)
        history = self.get_evolution_history(agent_id, limit=5)
        pending = self.get_pending_suggestions(agent_id)

        report = f"# Agent {agent_id} 进化报告\n\n"
        report += f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 性能分析
        report += "## [REPORT] 性能分析（最近24小时）\n\n"
        report += f"- 总任务数：{analysis['total_tasks']}\n"
        report += f"- 失败任务数：{analysis['failed_tasks']}\n"
        report += f"- 失败率：{analysis['failure_rate']:.1%}\n\n"

        # 失败模式
        if analysis['failure_patterns']:
            report += "## [WARN] 失败模式\n\n"
            for task_type, data in analysis['failure_patterns'].items():
                report += f"- **{task_type}**：失败 {data['count']} 次\n"
            report += "\n"

        # 改进建议
        if analysis['suggestions']:
            report += "## [IDEA] 改进建议\n\n"
            for i, suggestion in enumerate(analysis['suggestions'], 1):
                report += f"{i}. {suggestion}\n"
            report += "\n"

        # 待审核建议
        if pending:
            report += "## 📋 待审核建议\n\n"
            for suggestion in pending:
                report += f"- **{suggestion['type']}**：{suggestion['description']}\n"
            report += "\n"

        # 进化历史
        if history:
            report += "## 📜 进化历史（最近5次）\n\n"
            for record in history:
                time_str = datetime.fromtimestamp(record['timestamp']).strftime('%Y-%m-%d %H:%M')
                report += f"- **{time_str}** - {record['evolution_type']}\n"
                report += f"  原因：{record['reason']}\n"
            report += "\n"

        return report


# CLI 接口
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python -m aios.agent_system.evolution <command> [args]")
        print("\n命令：")
        print("  analyze <agent_id>     - 分析 Agent 失败模式")
        print("  report <agent_id>      - 生成进化报告")
        print("  suggestions [agent_id] - 查看待审核建议")
        print("  history <agent_id>     - 查看进化历史")
        return

    evolution = AgentEvolution()
    command = sys.argv[1]

    if command == "analyze":
        if len(sys.argv) < 3:
            print("错误：需要提供 agent_id")
            return
        
        agent_id = sys.argv[2]
        analysis = evolution.analyze_failures(agent_id)
        print(json.dumps(analysis, ensure_ascii=False, indent=2))

    elif command == "report":
        if len(sys.argv) < 3:
            print("错误：需要提供 agent_id")
            return
        
        agent_id = sys.argv[2]
        report = evolution.generate_evolution_report(agent_id)
        print(report)

    elif command == "suggestions":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        suggestions = evolution.get_pending_suggestions(agent_id)
        print(json.dumps(suggestions, ensure_ascii=False, indent=2))

    elif command == "history":
        if len(sys.argv) < 3:
            print("错误：需要提供 agent_id")
            return
        
        agent_id = sys.argv[2]
        history = evolution.get_evolution_history(agent_id)
        print(json.dumps(history, ensure_ascii=False, indent=2))

    else:
        print(f"未知命令：{command}")


if __name__ == "__main__":
    main()
