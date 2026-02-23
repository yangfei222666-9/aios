"""
多 Agent 协作示例：开发一个计算器功能

工作流：
1. coder Agent 写代码
2. tester Agent 写测试
3. automation Agent 打包部署
"""

# 示例任务定义
task = {
    "name": "开发计算器功能",
    "description": "创建一个支持加减乘除的计算器",
    "workflow": [
        {
            "step": 1,
            "agent": "coder",
            "task": "编写 calculator.py，实现加减乘除功能",
            "output": "calculator.py",
            "success_criteria": "代码能运行，有注释"
        },
        {
            "step": 2,
            "agent": "tester",
            "task": "为 calculator.py 编写测试用例",
            "input": "calculator.py",
            "output": "test_calculator.py",
            "success_criteria": "测试覆盖率 > 90%，全部通过"
        },
        {
            "step": 3,
            "agent": "automation",
            "task": "打包成可执行文件并创建安装脚本",
            "input": ["calculator.py", "test_calculator.py"],
            "output": "calculator.exe + setup.ps1",
            "success_criteria": "可以一键安装和运行"
        }
    ]
}

# 执行流程
def execute_workflow(task):
    results = []
    
    for step in task["workflow"]:
        print(f"Step {step['step']}: {step['agent']} - {step['task']}")
        
        # 调用对应的 Agent
        result = spawn_agent(
            agent_type=step["agent"],
            task=step["task"],
            input_files=step.get("input"),
            success_criteria=step["success_criteria"]
        )
        
        # 检查是否成功
        if not result["success"]:
            print(f"❌ Step {step['step']} 失败: {result['error']}")
            return {"success": False, "failed_at": step['step']}
        
        results.append(result)
        print(f"✅ Step {step['step']} 完成")
    
    return {"success": True, "results": results}
