"""Coder Failure Analyzer - 分析 Coder Agent 失败原因"""
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

class CoderFailureAnalyzer:
    def __init__(self):
        self.agents_file = Path("agents.json")
        self.execution_file = Path("task_executions.jsonl")
        self.events_file = Path("data/events/events.jsonl")
        
    def analyze(self):
        """分析 Coder Agent 失败原因"""
        print("=" * 80)
        print("Coder Failure Analyzer - 失败原因分析")
        print("=" * 80)
        
        # 1. 读取 Coder Agent 状态
        coder_stats = self._get_coder_stats()
        if not coder_stats:
            print("\n✗ 未找到 Coder Agent")
            return
        
        print(f"\n📊 Coder Agent 统计:")
        print(f"  成功: {coder_stats.get('tasks_completed', 0)}")
        print(f"  失败: {coder_stats.get('tasks_failed', 0)}")
        print(f"  总计: {coder_stats.get('tasks_total', 0)}")
        print(f"  成功率: {coder_stats.get('success_rate', 0):.1f}%")
        print(f"  平均耗时: {coder_stats.get('avg_duration', 0):.1f}秒")
        
        # 2. 分析失败事件
        failures = self._get_failure_events()
        if not failures:
            print("\n✓ 未找到失败记录")
            return
        
        print(f"\n🔍 失败事件分析 (共 {len(failures)} 条):")
        
        # 3. 失败原因分类
        error_types = Counter()
        error_messages = []
        
        for failure in failures:
            error = failure.get("error", "")
            error_type = self._classify_error(error)
            error_types[error_type] += 1
            error_messages.append({
                "type": error_type,
                "message": error[:200],
                "timestamp": failure.get("timestamp", "")
            })
        
        print("\n📋 失败原因分布:")
        for error_type, count in error_types.most_common():
            print(f"  {error_type}: {count} 次")
        
        # 4. 详细错误信息
        print("\n📝 详细错误信息:")
        for i, error in enumerate(error_messages[:3], 1):
            print(f"\n  [{i}] {error['type']}")
            print(f"      时间: {error['timestamp']}")
            print(f"      信息: {error['message']}")
        
        # 5. 生成诊断报告
        diagnosis = self._generate_diagnosis(error_types, coder_stats)
        
        print(f"\n{'=' * 80}")
        print("🔧 诊断报告:")
        print(f"{'=' * 80}")
        for i, item in enumerate(diagnosis, 1):
            print(f"\n{i}. {item['problem']}")
            print(f"   原因: {item['cause']}")
            print(f"   建议: {item['solution']}")
        
        # 6. 保存报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": coder_stats,
            "error_types": dict(error_types),
            "diagnosis": diagnosis
        }
        
        report_file = Path("data/analysis/coder_failure_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 报告已保存: {report_file}")
    
    def _get_coder_stats(self):
        """获取 Coder Agent 统计"""
        if not self.agents_file.exists():
            return None
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 支持两种格式
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        for agent in agents:
            if agent.get("name") == "coder-dispatcher":
                return agent.get("stats", {})
        return None
    
    def _get_failure_events(self):
        """获取失败事件"""
        failures = []
        
        # 从 events.jsonl 读取
        if self.events_file.exists():
            with open(self.events_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event.get("type") == "task_failed" and "coder" in event.get("agent", "").lower():
                            failures.append(event)
        
        # 从 task_executions.jsonl 读取
        if self.execution_file.exists():
            with open(self.execution_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        exec_record = json.loads(line)
                        if exec_record.get("status") == "failed" and "coder" in exec_record.get("agent", "").lower():
                            failures.append(exec_record)
        
        return failures
    
    def _classify_error(self, error):
        """分类错误类型"""
        error_lower = error.lower()
        
        if "timeout" in error_lower or "超时" in error_lower:
            return "超时错误"
        elif "api" in error_lower or "rate limit" in error_lower:
            return "API 错误"
        elif "syntax" in error_lower or "语法" in error_lower:
            return "语法错误"
        elif "import" in error_lower or "module" in error_lower:
            return "依赖错误"
        elif "permission" in error_lower or "权限" in error_lower:
            return "权限错误"
        elif "memory" in error_lower or "内存" in error_lower:
            return "内存错误"
        else:
            return "其他错误"
    
    def _generate_diagnosis(self, error_types, stats):
        """生成诊断建议"""
        diagnosis = []
        
        # 超时问题
        if "超时错误" in error_types:
            diagnosis.append({
                "problem": "任务超时",
                "cause": f"当前超时设置 120 秒，平均耗时 {stats.get('avg_duration', 0):.1f} 秒",
                "solution": "建议：1) 增加超时到 180 秒；2) 拆分复杂任务；3) 使用更快的模型"
            })
        
        # API 错误
        if "API 错误" in error_types:
            diagnosis.append({
                "problem": "API 调用失败",
                "cause": "可能是 API Key 无效、余额不足或速率限制",
                "solution": "建议：1) 检查 API Key；2) 检查余额；3) 添加重试机制"
            })
        
        # 成功率低
        if stats.get("success_rate", 0) < 50:
            diagnosis.append({
                "problem": "成功率过低",
                "cause": f"当前成功率 {stats.get('success_rate', 0):.1f}%",
                "solution": "建议：1) 简化任务描述；2) 添加示例代码；3) 使用更强的模型"
            })
        
        # 如果没有明确问题
        if not diagnosis:
            diagnosis.append({
                "problem": "未知问题",
                "cause": "需要查看详细日志",
                "solution": "建议：查看 logs/ 目录的详细日志文件"
            })
        
        return diagnosis

if __name__ == "__main__":
    analyzer = CoderFailureAnalyzer()
    analyzer.analyze()
