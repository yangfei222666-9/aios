#!/usr/bin/env python3
"""
Visualization Generator Agent
自动生成数据可视化图表
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class VisualizationGenerator:
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
    
    def generate_task_stats_chart(self) -> Dict[str, Any]:
        """生成任务统计图表（ASCII 艺术）"""
        task_queue = self.data_dir / "task_queue.jsonl"
        if not task_queue.exists():
            return {"error": "task_queue.jsonl not found"}
        
        # 统计数据
        tasks = []
        with open(task_queue, 'r', encoding='utf-8') as f:
            for line in f:
                tasks.append(json.loads(line))
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        failed = sum(1 for t in tasks if t.get('status') == 'failed')
        pending = sum(1 for t in tasks if t.get('status') == 'pending')
        running = sum(1 for t in tasks if t.get('status') == 'running')
        
        # 生成 ASCII 条形图
        max_width = 50
        chart = []
        chart.append("=" * 60)
        chart.append("任务状态统计")
        chart.append("=" * 60)
        
        def bar(label, count, total, color="█"):
            percentage = (count / total * 100) if total > 0 else 0
            bar_length = int(count / total * max_width) if total > 0 else 0
            bar_str = color * bar_length
            return f"{label:12} {bar_str} {count:3d} ({percentage:5.1f}%)"
        
        chart.append(bar("✅ 已完成", completed, total, "█"))
        chart.append(bar("❌ 失败", failed, total, "▓"))
        chart.append(bar("⏳ 待处理", pending, total, "░"))
        chart.append(bar("🔄 运行中", running, total, "▒"))
        chart.append("=" * 60)
        chart.append(f"总计: {total} 个任务")
        chart.append(f"成功率: {(completed/total*100):.1f}%" if total > 0 else "成功率: N/A")
        chart.append("=" * 60)
        
        return {
            "status": "success",
            "chart": "\n".join(chart),
            "data": {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "running": running
            }
        }
    
    def generate_type_distribution_chart(self) -> Dict[str, Any]:
        """生成任务类型分布图"""
        task_queue = self.data_dir / "task_queue.jsonl"
        if not task_queue.exists():
            return {"error": "task_queue.jsonl not found"}
        
        # 统计类型
        type_counts = {}
        with open(task_queue, 'r', encoding='utf-8') as f:
            for line in f:
                task = json.loads(line)
                task_type = task.get('type', 'unknown')
                type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        total = sum(type_counts.values())
        max_width = 50
        
        # 生成图表
        chart = []
        chart.append("=" * 60)
        chart.append("任务类型分布")
        chart.append("=" * 60)
        
        for task_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            bar_length = int(count / total * max_width) if total > 0 else 0
            bar_str = "█" * bar_length
            chart.append(f"{task_type:12} {bar_str} {count:3d} ({percentage:5.1f}%)")
        
        chart.append("=" * 60)
        chart.append(f"总计: {total} 个任务")
        chart.append("=" * 60)
        
        return {
            "status": "success",
            "chart": "\n".join(chart),
            "data": type_counts
        }
    
    def generate_performance_chart(self) -> Dict[str, Any]:
        """生成性能统计图表"""
        task_queue = self.data_dir / "task_queue.jsonl"
        if not task_queue.exists():
            return {"error": "task_queue.jsonl not found"}
        
        # 收集执行时间
        durations = []
        with open(task_queue, 'r', encoding='utf-8') as f:
            for line in f:
                task = json.loads(line)
                if 'result' in task and 'duration' in task['result']:
                    durations.append(task['result']['duration'])
        
        if not durations:
            return {
                "status": "success",
                "message": "No performance data available"
            }
        
        # 统计
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # 分桶统计
        buckets = {
            "0-5s": 0,
            "5-10s": 0,
            "10-20s": 0,
            "20-30s": 0,
            "30s+": 0
        }
        
        for d in durations:
            if d < 5:
                buckets["0-5s"] += 1
            elif d < 10:
                buckets["5-10s"] += 1
            elif d < 20:
                buckets["10-20s"] += 1
            elif d < 30:
                buckets["20-30s"] += 1
            else:
                buckets["30s+"] += 1
        
        total = len(durations)
        max_width = 50
        
        # 生成图表
        chart = []
        chart.append("=" * 60)
        chart.append("任务执行时间分布")
        chart.append("=" * 60)
        chart.append(f"平均: {avg_duration:.2f}s | 最快: {min_duration:.2f}s | 最慢: {max_duration:.2f}s")
        chart.append("-" * 60)
        
        for bucket, count in buckets.items():
            percentage = (count / total * 100) if total > 0 else 0
            bar_length = int(count / total * max_width) if total > 0 else 0
            bar_str = "█" * bar_length
            chart.append(f"{bucket:12} {bar_str} {count:3d} ({percentage:5.1f}%)")
        
        chart.append("=" * 60)
        
        return {
            "status": "success",
            "chart": "\n".join(chart),
            "data": {
                "avg_duration": avg_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "buckets": buckets
            }
        }
    
    def generate_agent_performance_chart(self) -> Dict[str, Any]:
        """生成 Agent 性能对比图"""
        agents_file = self.data_dir / "agents.json"
        if not agents_file.exists():
            return {"error": "agents.json not found"}
        
        with open(agents_file, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
        
        agents = agents_data.get('agents', [])
        
        # 收集 Agent 统计
        agent_stats = []
        for agent in agents:
            if 'stats' in agent or 'state' in agent:
                stats = agent.get('stats', agent.get('state', {}))
                agent_stats.append({
                    "name": agent.get('name', agent.get('id', 'unknown')),
                    "completed": stats.get('tasks_completed', 0),
                    "failed": stats.get('tasks_failed', 0),
                    "success_rate": stats.get('success_rate', 0.0)
                })
        
        # 按成功率排序
        agent_stats.sort(key=lambda x: x['success_rate'], reverse=True)
        
        max_width = 40
        chart = []
        chart.append("=" * 70)
        chart.append("Agent 性能排行（按成功率）")
        chart.append("=" * 70)
        
        for agent in agent_stats[:10]:  # 只显示前10个
            name = agent['name'][:20]  # 限制名称长度
            success_rate = agent['success_rate']
            completed = agent['completed']
            failed = agent['failed']
            
            bar_length = int(success_rate / 100 * max_width)
            bar_str = "█" * bar_length
            
            chart.append(f"{name:20} {bar_str} {success_rate:5.1f}% ({completed}✅/{failed}❌)")
        
        chart.append("=" * 70)
        
        return {
            "status": "success",
            "chart": "\n".join(chart),
            "data": agent_stats
        }
    
    def generate_html_dashboard(self) -> Dict[str, Any]:
        """生成 HTML 仪表板"""
        # 收集所有图表数据
        task_stats = self.generate_task_stats_chart()
        type_dist = self.generate_type_distribution_chart()
        performance = self.generate_performance_chart()
        agent_perf = self.generate_agent_performance_chart()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AIOS Dashboard</title>
    <style>
        body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
        .chart {{ background: #252526; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        pre {{ margin: 0; white-space: pre-wrap; }}
        h1 {{ color: #4ec9b0; }}
        h2 {{ color: #569cd6; }}
    </style>
</head>
<body>
    <h1>🚀 AIOS Dashboard</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="chart">
        <h2>任务状态统计</h2>
        <pre>{task_stats.get('chart', 'No data')}</pre>
    </div>
    
    <div class="chart">
        <h2>任务类型分布</h2>
        <pre>{type_dist.get('chart', 'No data')}</pre>
    </div>
    
    <div class="chart">
        <h2>执行时间分布</h2>
        <pre>{performance.get('chart', 'No data')}</pre>
    </div>
    
    <div class="chart">
        <h2>Agent 性能排行</h2>
        <pre>{agent_perf.get('chart', 'No data')}</pre>
    </div>
</body>
</html>"""
        
        # 保存 HTML
        dashboard_file = self.data_dir / "dashboard.html"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return {
            "status": "success",
            "dashboard_file": str(dashboard_file),
            "message": f"Dashboard generated at {dashboard_file}"
        }

def main():
    import sys
    
    generator = VisualizationGenerator()
    
    if len(sys.argv) < 2:
        print("Usage: python visualization_generator.py [task_stats|type_dist|performance|agent_perf|html]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "task_stats":
        result = generator.generate_task_stats_chart()
        if result.get("status") == "success":
            print(result["chart"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "type_dist":
        result = generator.generate_type_distribution_chart()
        if result.get("status") == "success":
            print(result["chart"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "performance":
        result = generator.generate_performance_chart()
        if result.get("status") == "success":
            print(result["chart"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "agent_perf":
        result = generator.generate_agent_performance_chart()
        if result.get("status") == "success":
            print(result["chart"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "html":
        result = generator.generate_html_dashboard()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
