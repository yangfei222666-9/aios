"""Performance Optimizer - 性能优化建议"""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class PerformanceOptimizer:
    def __init__(self):
        self.agents_file = Path("agents.json")
        self.events_file = Path("data/events/events.jsonl")
        
    def analyze(self):
        """分析性能并生成优化建议"""
        print("=" * 80)
        print("Performance Optimizer - 性能优化分析")
        print("=" * 80)
        
        # 1. 分析 Agent 性能
        agent_perf = self._analyze_agents()
        
        # 2. 分析任务性能
        task_perf = self._analyze_tasks()
        
        # 3. 生成优化建议
        recommendations = self._generate_recommendations(agent_perf, task_perf)
        
        # 4. 显示建议
        print(f"\n🚀 优化建议 ({len(recommendations)} 条):\n")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['title']}")
            print(f"   问题: {rec['problem']}")
            print(f"   影响: {rec['impact']}")
            print(f"   建议: {rec['solution']}")
            print(f"   预期收益: {rec['benefit']}\n")
        
        # 5. 保存报告
        self._save_report(agent_perf, task_perf, recommendations)
        
        print(f"{'=' * 80}")
    
    def _analyze_agents(self):
        """分析 Agent 性能"""
        print("\n📊 Agent 性能分析:")
        
        if not self.agents_file.exists():
            print("  ✗ agents.json 不存在")
            return {}
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        perf = {}
        for agent in agents:
            name = agent.get("name", "unknown")
            stats = agent.get("stats", {})
            
            avg_duration = stats.get("avg_duration", 0)
            success_rate = stats.get("success_rate", 0)
            
            perf[name] = {
                "avg_duration": avg_duration,
                "success_rate": success_rate,
                "total_tasks": stats.get("tasks_total", 0)
            }
            
            if avg_duration > 0:
                print(f"  {name}: {avg_duration:.1f}秒 (成功率 {success_rate:.1f}%)")
        
        return perf
    
    def _analyze_tasks(self):
        """分析任务性能"""
        print("\n📋 任务性能分析:")
        
        if not self.events_file.exists():
            print("  ✗ events.jsonl 不存在")
            return {}
        
        task_durations = defaultdict(list)
        
        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                event = json.loads(line)
                if event.get("type") == "task_completed":
                    task_type = event.get("task_type", "unknown")
                    duration = event.get("duration", 0)
                    task_durations[task_type].append(duration)
        
        perf = {}
        for task_type, durations in task_durations.items():
            avg = sum(durations) / len(durations)
            max_dur = max(durations)
            perf[task_type] = {
                "avg": avg,
                "max": max_dur,
                "count": len(durations)
            }
            print(f"  {task_type}: 平均 {avg:.1f}秒, 最大 {max_dur:.1f}秒 ({len(durations)} 次)")
        
        return perf
    
    def _generate_recommendations(self, agent_perf, task_perf):
        """生成优化建议"""
        recommendations = []
        
        # 1. 慢 Agent 优化
        for agent, perf in agent_perf.items():
            if perf["avg_duration"] > 60:
                recommendations.append({
                    "title": f"优化 {agent} 的执行速度",
                    "problem": f"平均耗时 {perf['avg_duration']:.1f} 秒，超过 60 秒阈值",
                    "impact": "影响用户体验，增加 API 成本",
                    "solution": "1) 切换到更快的模型（Sonnet）；2) 拆分复杂任务；3) 增加缓存",
                    "benefit": f"预计可减少 {(perf['avg_duration'] - 30):.1f} 秒"
                })
        
        # 2. 低成功率 Agent 优化
        for agent, perf in agent_perf.items():
            if perf["success_rate"] < 50 and perf["total_tasks"] > 0:
                recommendations.append({
                    "title": f"提升 {agent} 的成功率",
                    "problem": f"成功率仅 {perf['success_rate']:.1f}%",
                    "impact": "浪费 API 调用，降低系统可靠性",
                    "solution": "1) 优化 Prompt；2) 增加错误处理；3) 添加重试机制",
                    "benefit": f"预计可提升到 80%+ 成功率"
                })
        
        # 3. 慢任务类型优化
        for task_type, perf in task_perf.items():
            if perf["avg"] > 90:
                recommendations.append({
                    "title": f"优化 {task_type} 任务类型",
                    "problem": f"平均耗时 {perf['avg']:.1f} 秒",
                    "impact": "阻塞任务队列，影响整体吞吐量",
                    "solution": "1) 并行执行；2) 拆分子任务；3) 使用更快的模型",
                    "benefit": f"预计可减少 {(perf['avg'] - 45):.1f} 秒"
                })
        
        # 4. 通用优化
        if not recommendations:
            recommendations.append({
                "title": "系统性能良好",
                "problem": "未发现明显性能瓶颈",
                "impact": "无",
                "solution": "继续监控，保持当前配置",
                "benefit": "维持当前性能水平"
            })
        
        return recommendations
    
    def _save_report(self, agent_perf, task_perf, recommendations):
        """保存优化报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "agent_performance": agent_perf,
            "task_performance": task_perf,
            "recommendations": recommendations
        }
        
        report_file = Path("data/performance/optimization_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 报告已保存: {report_file}")

if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    optimizer.analyze()
