"""A/B Test Runner - 自动 A/B 测试不同策略"""
import json
from datetime import datetime
from pathlib import Path
import statistics

class ABTestRunner:
    def __init__(self):
        self.test_file = Path("data/ab_tests/test_results.jsonl")
        self.config_file = Path("data/ab_tests/test_config.json")
        
    def run_test(self, test_name, variant_a, variant_b, test_cases):
        """运行 A/B 测试"""
        print("=" * 80)
        print(f"A/B Test Runner - {test_name}")
        print("=" * 80)
        
        print(f"\n🧪 测试配置:")
        print(f"  变体 A: {variant_a.get('name')}")
        print(f"  变体 B: {variant_b.get('name')}")
        print(f"  测试用例: {len(test_cases)} 个\n")
        
        # 1. 运行变体 A
        print("🔵 运行变体 A...")
        results_a = self._run_variant(variant_a, test_cases)
        
        # 2. 运行变体 B
        print("🟢 运行变体 B...")
        results_b = self._run_variant(variant_b, test_cases)
        
        # 3. 对比结果
        comparison = self._compare_results(results_a, results_b)
        
        # 4. 显示结果
        self._display_results(variant_a, variant_b, results_a, results_b, comparison)
        
        # 5. 推荐决策
        recommendation = self._make_recommendation(comparison)
        print(f"\n💡 推荐: {recommendation}")
        
        # 6. 保存结果
        self._save_results(test_name, variant_a, variant_b, results_a, results_b, comparison, recommendation)
        
        print(f"\n{'=' * 80}")
        
        return recommendation
    
    def _run_variant(self, variant, test_cases):
        """运行单个变体"""
        results = {
            "success": 0,
            "failed": 0,
            "durations": [],
            "costs": [],
            "errors": []
        }
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"  测试 {i}/{len(test_cases)}...", end=" ")
            
            # 模拟执行（实际应该调用真实 Agent）
            result = self._simulate_execution(variant, test_case)
            
            if result["success"]:
                results["success"] += 1
                print("✓")
            else:
                results["failed"] += 1
                results["errors"].append(result.get("error", "未知错误"))
                print("✗")
            
            results["durations"].append(result["duration"])
            results["costs"].append(result["cost"])
        
        return results
    
    def _simulate_execution(self, variant, test_case):
        """模拟执行（实际应该调用真实 Agent）"""
        import random
        
        # 模拟不同变体的性能差异
        base_duration = 30
        base_cost = 0.01
        base_success_rate = 0.8
        
        # 变体 A 的调整
        if variant.get("model") == "claude-opus-4-5":
            duration_factor = 1.5
            cost_factor = 2.0
            success_factor = 1.1
        else:
            duration_factor = 1.0
            cost_factor = 1.0
            success_factor = 1.0
        
        duration = base_duration * duration_factor * random.uniform(0.8, 1.2)
        cost = base_cost * cost_factor * random.uniform(0.9, 1.1)
        success = random.random() < (base_success_rate * success_factor)
        
        return {
            "success": success,
            "duration": duration,
            "cost": cost,
            "error": None if success else "模拟错误"
        }
    
    def _compare_results(self, results_a, results_b):
        """对比结果"""
        comparison = {}
        
        # 成功率
        total_a = results_a["success"] + results_a["failed"]
        total_b = results_b["success"] + results_b["failed"]
        
        success_rate_a = results_a["success"] / total_a if total_a > 0 else 0
        success_rate_b = results_b["success"] / total_b if total_b > 0 else 0
        
        comparison["success_rate"] = {
            "a": success_rate_a,
            "b": success_rate_b,
            "diff": success_rate_b - success_rate_a,
            "winner": "B" if success_rate_b > success_rate_a else "A"
        }
        
        # 平均耗时
        avg_duration_a = statistics.mean(results_a["durations"]) if results_a["durations"] else 0
        avg_duration_b = statistics.mean(results_b["durations"]) if results_b["durations"] else 0
        
        comparison["duration"] = {
            "a": avg_duration_a,
            "b": avg_duration_b,
            "diff": avg_duration_b - avg_duration_a,
            "winner": "B" if avg_duration_b < avg_duration_a else "A"
        }
        
        # 平均成本
        avg_cost_a = statistics.mean(results_a["costs"]) if results_a["costs"] else 0
        avg_cost_b = statistics.mean(results_b["costs"]) if results_b["costs"] else 0
        
        comparison["cost"] = {
            "a": avg_cost_a,
            "b": avg_cost_b,
            "diff": avg_cost_b - avg_cost_a,
            "winner": "B" if avg_cost_b < avg_cost_a else "A"
        }
        
        return comparison
    
    def _display_results(self, variant_a, variant_b, results_a, results_b, comparison):
        """显示结果"""
        print(f"\n📊 测试结果:\n")
        
        # 成功率
        print(f"成功率:")
        print(f"  变体 A: {comparison['success_rate']['a']:.1%}")
        print(f"  变体 B: {comparison['success_rate']['b']:.1%}")
        print(f"  差异: {comparison['success_rate']['diff']:+.1%}")
        print(f"  胜者: 变体 {comparison['success_rate']['winner']} 🏆\n")
        
        # 耗时
        print(f"平均耗时:")
        print(f"  变体 A: {comparison['duration']['a']:.1f}秒")
        print(f"  变体 B: {comparison['duration']['b']:.1f}秒")
        print(f"  差异: {comparison['duration']['diff']:+.1f}秒")
        print(f"  胜者: 变体 {comparison['duration']['winner']} 🏆\n")
        
        # 成本
        print(f"平均成本:")
        print(f"  变体 A: ${comparison['cost']['a']:.4f}")
        print(f"  变体 B: ${comparison['cost']['b']:.4f}")
        print(f"  差异: ${comparison['cost']['diff']:+.4f}")
        print(f"  胜者: 变体 {comparison['cost']['winner']} 🏆")
    
    def _make_recommendation(self, comparison):
        """生成推荐"""
        # 计算综合得分（成功率 50%，耗时 30%，成本 20%）
        score_a = (
            comparison["success_rate"]["a"] * 0.5 +
            (1 - comparison["duration"]["a"] / 100) * 0.3 +
            (1 - comparison["cost"]["a"] / 0.1) * 0.2
        )
        
        score_b = (
            comparison["success_rate"]["b"] * 0.5 +
            (1 - comparison["duration"]["b"] / 100) * 0.3 +
            (1 - comparison["cost"]["b"] / 0.1) * 0.2
        )
        
        if score_b > score_a * 1.1:  # B 明显更好（>10%）
            return "强烈推荐使用变体 B"
        elif score_b > score_a:
            return "推荐使用变体 B"
        elif score_a > score_b * 1.1:
            return "强烈推荐使用变体 A"
        elif score_a > score_b:
            return "推荐使用变体 A"
        else:
            return "两个变体性能相近，可任选其一"
    
    def _save_results(self, test_name, variant_a, variant_b, results_a, results_b, comparison, recommendation):
        """保存结果"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "results_a": results_a,
            "results_b": results_b,
            "comparison": comparison,
            "recommendation": recommendation
        }
        
        self.test_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.test_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        print(f"\n✓ 结果已保存: {self.test_file}")

if __name__ == "__main__":
    runner = ABTestRunner()
    
    # 示例：测试不同模型
    test_name = "模型对比测试: Opus vs Sonnet"
    
    variant_a = {
        "name": "Opus 4.5",
        "model": "claude-opus-4-5",
        "thinking": "on"
    }
    
    variant_b = {
        "name": "Sonnet 4.5",
        "model": "claude-sonnet-4-5",
        "thinking": "off"
    }
    
    # 生成测试用例
    test_cases = [
        {"task": "写一个简单的 Python 函数"},
        {"task": "分析一段代码的性能"},
        {"task": "重构一个复杂的类"},
        {"task": "修复一个 Bug"},
        {"task": "生成单元测试"}
    ]
    
    runner.run_test(test_name, variant_a, variant_b, test_cases)
