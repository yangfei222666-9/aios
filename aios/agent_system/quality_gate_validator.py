"""
质量门控验证器
自动验证工作流执行是否满足质量标准
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class QualityGateValidator:
    """质量门控验证器"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.validation_log = self.workspace / "aios" / "agent_system" / "quality_gate_validations.jsonl"
        self.validation_log.parent.mkdir(parents=True, exist_ok=True)
    
    def validate(self, execution_id: str, workflow: Dict, 
                stage_output: Any, metrics: Dict) -> Dict:
        """
        验证质量门控
        
        Args:
            execution_id: 执行ID
            workflow: 工作流定义
            stage_output: 阶段输出
            metrics: 阶段指标
        
        Returns:
            {
                "passed": bool,
                "failed_gates": List[str],
                "details": Dict
            }
        """
        quality_gates = workflow.get("quality_gates", {})
        if not quality_gates:
            return {"passed": True, "failed_gates": [], "details": {}}
        
        failed_gates = []
        details = {}
        
        for gate_name, expected_value in quality_gates.items():
            result = self._validate_gate(gate_name, expected_value, metrics, stage_output)
            details[gate_name] = result
            
            if not result["passed"]:
                failed_gates.append(gate_name)
        
        validation_result = {
            "execution_id": execution_id,
            "workflow_id": workflow["workflow_id"],
            "passed": len(failed_gates) == 0,
            "failed_gates": failed_gates,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录验证结果
        self._log_validation(validation_result)
        
        return validation_result
    
    def _validate_gate(self, gate_name: str, expected_value: Any, 
                      metrics: Dict, output: Any) -> Dict:
        """验证单个门控"""
        
        # 测试覆盖率
        if gate_name == "test_coverage":
            actual = metrics.get("test_coverage", 0.0)
            passed = actual >= expected_value
            return {
                "passed": passed,
                "expected": f">= {expected_value}",
                "actual": actual,
                "message": f"测试覆盖率 {actual:.1%} {'✓' if passed else '✗ 低于'} {expected_value:.1%}"
            }
        
        # 最大复杂度
        elif gate_name == "max_complexity":
            actual = metrics.get("complexity", 0)
            passed = actual <= expected_value
            return {
                "passed": passed,
                "expected": f"<= {expected_value}",
                "actual": actual,
                "message": f"代码复杂度 {actual} {'✓' if passed else '✗ 超过'} {expected_value}"
            }
        
        # 无安全问题
        elif gate_name == "no_security_issues":
            actual = metrics.get("security_issues", 0)
            passed = actual == 0
            return {
                "passed": passed,
                "expected": "0",
                "actual": actual,
                "message": f"安全问题 {actual} 个 {'✓' if passed else '✗'}"
            }
        
        # 最少数据点
        elif gate_name == "min_data_points":
            actual = metrics.get("data_points", 0)
            passed = actual >= expected_value
            return {
                "passed": passed,
                "expected": f">= {expected_value}",
                "actual": actual,
                "message": f"数据点 {actual} {'✓' if passed else '✗ 少于'} {expected_value}"
            }
        
        # 置信度
        elif gate_name == "confidence_level":
            actual = metrics.get("confidence", 0.0)
            passed = actual >= expected_value
            return {
                "passed": passed,
                "expected": f">= {expected_value}",
                "actual": actual,
                "message": f"置信度 {actual:.1%} {'✓' if passed else '✗ 低于'} {expected_value:.1%}"
            }
        
        # 无数据泄漏
        elif gate_name == "no_data_leakage":
            actual = metrics.get("data_leakage", False)
            passed = not actual
            return {
                "passed": passed,
                "expected": "False",
                "actual": actual,
                "message": f"数据泄漏 {'✓ 无' if passed else '✗ 检测到'}"
            }
        
        # 误报率
        elif gate_name == "false_positive_rate":
            actual = metrics.get("false_positive_rate", 1.0)
            passed = actual <= expected_value
            return {
                "passed": passed,
                "expected": f"<= {expected_value}",
                "actual": actual,
                "message": f"误报率 {actual:.1%} {'✓' if passed else '✗ 超过'} {expected_value:.1%}"
            }
        
        # 告警延迟
        elif gate_name == "alert_latency_sec":
            actual = metrics.get("alert_latency_sec", 999)
            passed = actual <= expected_value
            return {
                "passed": passed,
                "expected": f"<= {expected_value}s",
                "actual": actual,
                "message": f"告警延迟 {actual}s {'✓' if passed else '✗ 超过'} {expected_value}s"
            }
        
        # 不漏报 critical
        elif gate_name == "no_missed_critical":
            actual = metrics.get("missed_critical", 0)
            passed = actual == 0
            return {
                "passed": passed,
                "expected": "0",
                "actual": actual,
                "message": f"漏报 critical {actual} 个 {'✓' if passed else '✗'}"
            }
        
        # 未知门控
        else:
            return {
                "passed": True,
                "expected": "unknown",
                "actual": "unknown",
                "message": f"未知门控: {gate_name}"
            }
    
    def _log_validation(self, result: Dict):
        """记录验证结果"""
        with open(self.validation_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    def get_validation_history(self, execution_id: Optional[str] = None, 
                              limit: int = 100) -> List[Dict]:
        """获取验证历史"""
        if not self.validation_log.exists():
            return []
        
        results = []
        with open(self.validation_log, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if execution_id is None or record.get("execution_id") == execution_id:
                        results.append(record)
        
        return results[-limit:]
    
    def get_pass_rate(self, workflow_id: Optional[str] = None) -> float:
        """获取通过率"""
        history = self.get_validation_history()
        
        if workflow_id:
            history = [h for h in history if h.get("workflow_id") == workflow_id]
        
        if not history:
            return 0.0
        
        passed = len([h for h in history if h["passed"]])
        return passed / len(history)


def main():
    """测试质量门控验证"""
    workspace = Path("C:/Users/A/.openclaw/workspace")
    validator = QualityGateValidator(workspace)
    
    # 模拟 coder 工作流验证
    workflow = {
        "workflow_id": "coder-standard",
        "quality_gates": {
            "test_coverage": 0.8,
            "max_complexity": 10,
            "no_security_issues": True
        }
    }
    
    # 测试1：通过
    print("=== 测试1：全部通过 ===")
    result1 = validator.validate(
        execution_id="test-001",
        workflow=workflow,
        stage_output={"code": "..."},
        metrics={
            "test_coverage": 0.85,
            "complexity": 8,
            "security_issues": 0
        }
    )
    print(f"通过: {result1['passed']}")
    for gate, detail in result1['details'].items():
        print(f"  {gate}: {detail['message']}")
    print()
    
    # 测试2：失败
    print("=== 测试2：部分失败 ===")
    result2 = validator.validate(
        execution_id="test-002",
        workflow=workflow,
        stage_output={"code": "..."},
        metrics={
            "test_coverage": 0.65,  # 不达标
            "complexity": 15,        # 超标
            "security_issues": 0
        }
    )
    print(f"通过: {result2['passed']}")
    print(f"失败门控: {result2['failed_gates']}")
    for gate, detail in result2['details'].items():
        print(f"  {gate}: {detail['message']}")
    print()
    
    # 查看通过率
    print(f"=== 通过率 ===")
    print(f"总体通过率: {validator.get_pass_rate():.1%}")
    print(f"coder-standard 通过率: {validator.get_pass_rate('coder-standard'):.1%}")


if __name__ == "__main__":
    main()
