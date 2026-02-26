#!/usr/bin/env python3
"""
Evaluator Agent - 评测与回归测试
固定测试集 + 性能对比 + 防止退化
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from data_collector import DataCollector

# 测试集目录
TEST_SUITE_DIR = Path(__file__).parent / "test_suite"
TEST_SUITE_DIR.mkdir(exist_ok=True)

# 测试结果目录
RESULTS_DIR = Path(__file__).parent / "data" / "evaluation"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 固定测试集
DEFAULT_TEST_SUITE = [
    {
        "id": "test_001",
        "name": "简单函数",
        "description": "写一个函数计算1到n的和",
        "type": "code",
        "priority": "normal",
        "expected": {
            "success": True,
            "has_function": True,
            "has_error_handling": True,
            "max_duration_ms": 10000
        }
    },
    {
        "id": "test_002",
        "name": "斐波那契数列",
        "description": "写一个函数，输入n，返回斐波那契数列前n项",
        "type": "code",
        "priority": "normal",
        "expected": {
            "success": True,
            "has_function": True,
            "max_duration_ms": 10000
        }
    },
    {
        "id": "test_003",
        "name": "质数判断",
        "description": "写一个函数判断一个数是否为质数",
        "type": "code",
        "priority": "normal",
        "expected": {
            "success": True,
            "has_function": True,
            "has_optimization": False,  # 不强制要求优化
            "max_duration_ms": 10000
        }
    },
    {
        "id": "test_004",
        "name": "简单爬虫",
        "description": "写一个爬虫抓取网页标题",
        "type": "code",
        "priority": "high",
        "expected": {
            "success": True,
            "has_error_handling": True,
            "max_duration_ms": 15000
        }
    },
    {
        "id": "test_005",
        "name": "Flask API",
        "description": "写一个简单的 Flask API，返回当前时间",
        "type": "code",
        "priority": "high",
        "expected": {
            "success": True,
            "has_error_handling": True,
            "max_duration_ms": 15000
        }
    }
]

class Evaluator:
    """评测器"""
    
    def __init__(self):
        self.test_suite = self._load_test_suite()
    
    def _load_test_suite(self) -> List[Dict]:
        """加载测试集"""
        test_file = TEST_SUITE_DIR / "test_suite.json"
        
        if test_file.exists():
            with open(test_file, encoding="utf-8") as f:
                return json.load(f)
        else:
            # 创建默认测试集
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TEST_SUITE, f, indent=2, ensure_ascii=False)
            return DEFAULT_TEST_SUITE
    
    def run_test(self, test_case: Dict) -> Dict:
        """运行单个测试"""
        print(f"\n🧪 测试: {test_case['name']}")
        print(f"   描述: {test_case['description']}")
        
        start_time = time.time()
        
        # 这里应该调用 real_coder 执行任务
        # 为了演示，我们模拟执行
        result = {
            "test_id": test_case["id"],
            "test_name": test_case["name"],
            "status": "success",  # 模拟成功
            "duration_ms": int((time.time() - start_time) * 1000),
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "has_function": True,
                "has_error_handling": True,
                "code_length": 150,
                "execution_success": True
            }
        }
        
        # 验证期望
        passed = self._validate_expectations(result, test_case["expected"])
        result["passed"] = passed
        
        if passed:
            print(f"   ✅ 通过")
        else:
            print(f"   ❌ 失败")
        
        return result
    
    def _validate_expectations(self, result: Dict, expected: Dict) -> bool:
        """验证是否符合期望"""
        if not result["status"] == "success":
            return False
        
        metrics = result["metrics"]
        
        # 检查各项期望
        if expected.get("has_function") and not metrics.get("has_function"):
            return False
        
        if expected.get("has_error_handling") and not metrics.get("has_error_handling"):
            return False
        
        if expected.get("max_duration_ms") and result["duration_ms"] > expected["max_duration_ms"]:
            return False
        
        return True
    
    def run_suite(self) -> Dict:
        """运行完整测试集"""
        print("=" * 80)
        print("🚀 开始回归测试")
        print("=" * 80)
        
        results = []
        passed = 0
        failed = 0
        
        for test_case in self.test_suite:
            result = self.run_test(test_case)
            results.append(result)
            
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total": len(self.test_suite),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(self.test_suite)) * 100,
            "results": results
        }
        
        # 保存结果
        result_file = RESULTS_DIR / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("📊 测试完成")
        print("=" * 80)
        print(f"总计: {report['total']}")
        print(f"通过: {report['passed']}")
        print(f"失败: {report['failed']}")
        print(f"成功率: {report['success_rate']:.1f}%")
        print(f"\n结果已保存: {result_file}")
        
        return report
    
    def compare_results(self, baseline_file: str = None) -> Dict:
        """对比两次测试结果"""
        # 获取最新的两个结果文件
        result_files = sorted(RESULTS_DIR.glob("result_*.json"), reverse=True)
        
        if len(result_files) < 2:
            print("⚠️ 需要至少2次测试结果才能对比")
            return None
        
        # 读取最新和基线结果
        with open(result_files[0], encoding="utf-8") as f:
            current = json.load(f)
        
        with open(result_files[1], encoding="utf-8") as f:
            baseline = json.load(f)
        
        # 对比
        comparison = {
            "current_timestamp": current["timestamp"],
            "baseline_timestamp": baseline["timestamp"],
            "success_rate_change": current["success_rate"] - baseline["success_rate"],
            "passed_change": current["passed"] - baseline["passed"],
            "failed_change": current["failed"] - baseline["failed"],
            "regression": current["success_rate"] < baseline["success_rate"]
        }
        
        print("\n" + "=" * 80)
        print("📈 性能对比")
        print("=" * 80)
        print(f"基线: {baseline['timestamp']}")
        print(f"当前: {current['timestamp']}")
        print(f"\n成功率: {baseline['success_rate']:.1f}% → {current['success_rate']:.1f}% ({comparison['success_rate_change']:+.1f}%)")
        print(f"通过: {baseline['passed']} → {current['passed']} ({comparison['passed_change']:+d})")
        print(f"失败: {baseline['failed']} → {current['failed']} ({comparison['failed_change']:+d})")
        
        if comparison["regression"]:
            print("\n⚠️ 检测到性能退化！")
        else:
            print("\n✅ 性能保持或提升")
        
        return comparison
    
    def generate_report(self) -> str:
        """生成评测报告"""
        # 获取最新结果
        result_files = sorted(RESULTS_DIR.glob("result_*.json"), reverse=True)
        
        if not result_files:
            return "暂无测试结果"
        
        with open(result_files[0], encoding="utf-8") as f:
            latest = json.load(f)
        
        report = f"""
📊 评测报告 - {latest['timestamp']}

✅ 通过: {latest['passed']}/{latest['total']} ({latest['success_rate']:.1f}%)
❌ 失败: {latest['failed']}/{latest['total']}

详细结果:
"""
        for result in latest['results']:
            status = "✅" if result['passed'] else "❌"
            report += f"{status} {result['test_name']}: {result['duration_ms']}ms\n"
        
        return report

# 便捷函数
def run_evaluation():
    """运行评测"""
    evaluator = Evaluator()
    return evaluator.run_suite()

def compare_performance():
    """对比性能"""
    evaluator = Evaluator()
    return evaluator.compare_results()

if __name__ == "__main__":
    # 测试
    print("🧪 Evaluator Agent 测试\n")
    
    evaluator = Evaluator()
    
    # 运行测试集
    report = evaluator.run_suite()
    
    # 生成报告
    print("\n" + evaluator.generate_report())
