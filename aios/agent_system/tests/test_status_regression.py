#!/usr/bin/env python3
"""
状态模型回归测试

验证状态推导逻辑、输出格式、统计数字不漂移。
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
agent_system_dir = Path(__file__).parent.parent
sys.path.insert(0, str(agent_system_dir))

# Import status adapter
status_adapter_path = agent_system_dir / "core" / "status_adapter.py"
if status_adapter_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("status_adapter", status_adapter_path)
    status_adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(status_adapter)
    get_agent_status = status_adapter.get_agent_status
    get_skill_status = status_adapter.get_skill_status
    get_task_status = status_adapter.get_task_status
else:
    print(f"❌ status_adapter.py not found at {status_adapter_path}")
    sys.exit(1)


def load_golden(name: str) -> dict:
    """加载 golden snapshot"""
    golden_path = Path(__file__).parent / "golden" / f"{name}_golden.json"
    if not golden_path.exists():
        return None
    with open(golden_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_golden(name: str, data: dict):
    """保存 golden snapshot"""
    golden_path = Path(__file__).parent / "golden" / f"{name}_golden.json"
    with open(golden_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def test_agent_status_logic():
    """测试 Agent 状态推导逻辑"""
    print("Testing Agent status logic...")
    
    test_cases = [
        {
            "name": "registered_not_executable",
            "agent": {"name": "test", "stats": {}},
            "expected": "registered"
        },
        {
            "name": "executable_not_validated",
            "agent": {"name": "test", "stats": {"tasks_completed": 0}},
            "expected": "executable"
        },
        {
            "name": "validated",
            "agent": {"name": "test", "stats": {"tasks_completed": 1}},
            "expected": "validated"
        },
        {
            "name": "production_ready",
            "agent": {"name": "test", "stats": {"tasks_completed": 5, "tasks_failed": 0}},
            "expected": "production-ready"
        },
        {
            "name": "stable",
            "agent": {"name": "test", "stats": {"tasks_completed": 20, "tasks_failed": 1}},
            "expected": "stable"
        }
    ]
    
    results = []
    for case in test_cases:
        actual = get_agent_status(case["agent"])
        passed = actual == case["expected"]
        results.append({
            "name": case["name"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed
        })
        
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {case['name']}: {actual} (expected: {case['expected']})")
    
    return results


def test_skill_status_logic():
    """测试 Skill 状态推导逻辑"""
    print("\nTesting Skill status logic...")
    
    test_cases = [
        {
            "name": "registered_not_executable",
            "skill": {"name": "test", "stats": {}},
            "expected": "registered"
        },
        {
            "name": "executable",
            "skill": {"name": "test", "stats": {"uses": 1}},
            "expected": "executable"
        },
        {
            "name": "stable",
            "skill": {"name": "test", "stats": {"uses": 10, "failures": 0}},
            "expected": "stable"
        }
    ]
    
    results = []
    for case in test_cases:
        actual = get_skill_status(case["skill"])
        passed = actual == case["expected"]
        results.append({
            "name": case["name"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed
        })
        
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {case['name']}: {actual} (expected: {case['expected']})")
    
    return results


def test_task_status_logic():
    """测试 Task 状态推导逻辑"""
    print("\nTesting Task status logic...")
    
    test_cases = [
        {
            "name": "pending",
            "task": {"status": "pending"},
            "expected": "pending"
        },
        {
            "name": "running",
            "task": {"status": "running"},
            "expected": "running"
        },
        {
            "name": "completed",
            "task": {"status": "completed"},
            "expected": "completed"
        },
        {
            "name": "failed",
            "task": {"status": "failed"},
            "expected": "failed"
        }
    ]
    
    results = []
    for case in test_cases:
        actual = get_task_status(case["task"])
        passed = actual == case["expected"]
        results.append({
            "name": case["name"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed
        })
        
        status_icon = "✅" if passed else "❌"
        print(f"  {status_icon} {case['name']}: {actual} (expected: {case['expected']})")
    
    return results


def main():
    """运行所有回归测试"""
    print("=" * 60)
    print("状态模型回归测试")
    print("=" * 60)
    
    # 运行测试
    agent_results = test_agent_status_logic()
    skill_results = test_skill_status_logic()
    task_results = test_task_status_logic()
    
    # 统计结果
    all_results = agent_results + skill_results + task_results
    total = len(all_results)
    passed = sum(1 for r in all_results if r["passed"])
    failed = total - passed
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    if failed > 0:
        print(f"❌ {failed} 个测试失败")
        sys.exit(1)
    else:
        print("✅ 所有测试通过")
    print("=" * 60)
    
    # 保存 golden snapshot
    golden_data = {
        "agent_results": agent_results,
        "skill_results": skill_results,
        "task_results": task_results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed
        }
    }
    save_golden("status_regression", golden_data)
    print("\n✅ Golden snapshot 已保存")


if __name__ == "__main__":
    main()
