#!/usr/bin/env python3
"""
AIOS Learning Orchestrator - 学习 Agent 调度器

职责：
1. 统一调度 5 个学习 Agent
2. 控制执行频率和顺序
3. 汇总学习结果
4. 生成综合报告
5. 触发改进行动

5 个学习 Agent：
1. Provider Learner - 学习 Provider 性能
2. Playbook Learner - 学习 Playbook 效果
3. Agent Behavior Learner - 学习 Agent 行为
4. Error Pattern Learner - 学习错误模式
5. Optimization Learner - 学习优化效果

执行策略：
- 每天运行一次（凌晨 4:00）
- 按顺序执行，避免资源冲突
- 汇总所有建议，按优先级排序
- 生成综合学习报告
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import subprocess

# 添加 AIOS 路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

class LearningOrchestrator:
    """学习 Agent 调度器"""

    def __init__(self):
        self.data_dir = AIOS_ROOT / "agent_system" / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 5 个学习 Agent
        self.learners = [
            {
                "name": "Provider Learner",
                "script": AIOS_ROOT / "agent_system" / "learner_provider.py",
                "priority": 1
            },
            {
                "name": "Playbook Learner",
                "script": AIOS_ROOT / "agent_system" / "learner_playbook.py",
                "priority": 2
            },
            {
                "name": "Agent Behavior Learner",
                "script": AIOS_ROOT / "agent_system" / "learner_agent_behavior.py",
                "priority": 3
            },
            {
                "name": "Error Pattern Learner",
                "script": AIOS_ROOT / "agent_system" / "learner_error_pattern.py",
                "priority": 4
            },
            {
                "name": "Optimization Learner",
                "script": AIOS_ROOT / "agent_system" / "learner_optimization.py",
                "priority": 5
            }
        ]

    def run(self) -> Dict:
        """运行所有学习 Agent"""
        print("=" * 80)
        print("  AIOS Learning Orchestrator")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        report = {
            "timestamp": datetime.now().isoformat(),
            "learners": [],
            "all_suggestions": [],
            "summary": {}
        }

        # 按顺序执行每个学习 Agent
        for i, learner in enumerate(self.learners, 1):
            print(f"[{i}/{len(self.learners)}] 运行 {learner['name']}...")
            print("-" * 80)
            
            result = self._run_learner(learner)
            report["learners"].append(result)
            
            # 收集建议
            if result.get("suggestions"):
                report["all_suggestions"].extend(result["suggestions"])
            
            print()

        # 汇总结果
        print("=" * 80)
        print("  汇总学习结果")
        print("=" * 80)
        
        summary = self._generate_summary(report)
        report["summary"] = summary
        
        # 打印摘要
        print(f"\n总建议数：{summary['total_suggestions']}")
        print(f"高优先级：{summary['high_priority']}")
        print(f"中优先级：{summary['medium_priority']}")
        print(f"低优先级：{summary['low_priority']}")
        
        if summary["top_suggestions"]:
            print("\n🔥 Top 3 建议：")
            for i, suggestion in enumerate(summary["top_suggestions"][:3], 1):
                print(f"  {i}. [{suggestion['priority'].upper()}] {suggestion['description']}")
        
        # 保存报告
        self._save_report(report)

        print()
        print("=" * 80)
        print(f"  完成！共生成 {summary['total_suggestions']} 条建议")
        print("=" * 80)

        return report

    def _run_learner(self, learner: Dict) -> Dict:
        """运行单个学习 Agent"""
        result = {
            "name": learner["name"],
            "script": str(learner["script"]),
            "start_time": datetime.now().isoformat(),
            "success": False,
            "suggestions": [],
            "error": None
        }

        try:
            # 运行 Python 脚本（使用 GBK 编码避免 Windows 终端乱码）
            process = subprocess.run(
                [sys.executable, str(learner["script"])],
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
                encoding='gbk',
                errors='ignore'  # 忽略编码错误
            )
            
            result["success"] = process.returncode == 0
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            
            # 解析输出
            if result["success"]:
                # 查找最新的报告文件
                report_pattern = learner["script"].stem + "_*.json"
                report_files = sorted(self.data_dir.glob(report_pattern))
                
                if report_files:
                    latest_report = report_files[-1]
                    with open(latest_report, 'r', encoding='utf-8') as f:
                        learner_report = json.load(f)
                    
                    result["suggestions"] = learner_report.get("suggestions", [])
                    result["report_file"] = str(latest_report)
            else:
                result["error"] = process.stderr
        
        except subprocess.TimeoutExpired:
            result["error"] = "Timeout (>5 minutes)"
        except Exception as e:
            result["error"] = str(e)
        
        result["end_time"] = datetime.now().isoformat()
        
        # 打印结果
        if result["success"]:
            print(f"✅ 成功！生成 {len(result['suggestions'])} 条建议")
        else:
            print(f"❌ 失败：{result['error']}")
        
        return result

    def _generate_summary(self, report: Dict) -> Dict:
        """生成汇总报告"""
        all_suggestions = report.get("all_suggestions", [])
        
        # 按优先级分类
        high_priority = [s for s in all_suggestions if s.get("priority") == "high"]
        medium_priority = [s for s in all_suggestions if s.get("priority") == "medium"]
        low_priority = [s for s in all_suggestions if s.get("priority") == "low"]
        
        # 按优先级排序（high > medium > low）
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_suggestions = sorted(
            all_suggestions,
            key=lambda x: priority_order.get(x.get("priority", "low"), 2)
        )
        
        return {
            "total_suggestions": len(all_suggestions),
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
            "top_suggestions": sorted_suggestions[:10],  # Top 10
            "by_type": self._group_by_type(all_suggestions)
        }

    def _group_by_type(self, suggestions: List[Dict]) -> Dict:
        """按类型分组建议"""
        by_type = {}
        for suggestion in suggestions:
            suggestion_type = suggestion.get("type", "unknown")
            if suggestion_type not in by_type:
                by_type[suggestion_type] = []
            by_type[suggestion_type].append(suggestion)
        
        return by_type

    def _save_report(self, report: Dict):
        """保存综合报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"orchestrator_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 综合报告已保存: {report_file}")


def main():
    """主函数"""
    orchestrator = LearningOrchestrator()
    report = orchestrator.run()
    
    summary = report.get("summary", {})
    total_suggestions = summary.get("total_suggestions", 0)
    
    if total_suggestions > 0:
        print(f"\nLEARNING_ORCHESTRATOR_SUGGESTIONS:{total_suggestions}")
    else:
        print("\nLEARNING_ORCHESTRATOR_OK")


if __name__ == "__main__":
    main()
