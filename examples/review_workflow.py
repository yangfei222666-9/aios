"""
评审协作示例：高质量代码开发

包含反馈循环，直到达到质量标准
"""

task = {
    "name": "开发高质量的数据处理模块",
    "max_iterations": 3,
    "workflow": [
        {
            "agent": "coder",
            "task": "编写数据处理模块",
            "output": "data_processor.py"
        },
        {
            "agent": "tester",
            "task": "测试数据处理模块",
            "quality_gates": {
                "coverage": 0.9,
                "pass_rate": 1.0
            }
        },
        {
            "agent": "reviewer",
            "task": "代码审查",
            "quality_gates": {
                "code_quality": 0.8,
                "documentation": 0.9,
                "best_practices": 0.85
            }
        }
    ]
}

def execute_with_review(task):
    iteration = 0
    
    while iteration < task["max_iterations"]:
        iteration += 1
        print(f"\n=== Iteration {iteration} ===")
        
        # Step 1: Coder 写代码
        code_result = spawn_agent("coder", task["workflow"][0]["task"])
        
        # Step 2: Tester 测试
        test_result = spawn_agent("tester", task["workflow"][1]["task"])
        
        if not meets_quality_gates(test_result, task["workflow"][1]["quality_gates"]):
            print("❌ 测试未通过，返回修改")
            feedback = generate_feedback(test_result)
            continue
        
        # Step 3: Reviewer 审查
        review_result = spawn_agent("reviewer", task["workflow"][2]["task"])
        
        if not meets_quality_gates(review_result, task["workflow"][2]["quality_gates"]):
            print("❌ 代码审查未通过，返回修改")
            feedback = generate_feedback(review_result)
            continue
        
        print("✅ 所有质量门槛通过！")
        return {"success": True, "iterations": iteration}
    
    return {"success": False, "reason": "超过最大迭代次数"}
