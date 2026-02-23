"""
并行协作示例：研究一个新技术

多个 Agent 同时工作，最后汇总结果
"""

task = {
    "name": "研究 Transformer 架构",
    "parallel_tasks": [
        {
            "agent": "researcher",
            "task": "搜索 Transformer 的论文和教程",
            "output": "research_report.md"
        },
        {
            "agent": "analyst",
            "task": "分析 Transformer 的性能数据和应用场景",
            "output": "analysis_report.md"
        },
        {
            "agent": "coder",
            "task": "写一个简单的 Transformer 实现示例",
            "output": "transformer_demo.py"
        }
    ],
    "aggregation": {
        "agent": "coder",
        "task": "汇总所有结果，生成完整的学习报告",
        "output": "transformer_complete_guide.md"
    }
}

# 并行执行
import asyncio

async def execute_parallel(task):
    # 并行启动所有 Agent
    tasks = []
    for subtask in task["parallel_tasks"]:
        tasks.append(
            spawn_agent_async(
                agent_type=subtask["agent"],
                task=subtask["task"]
            )
        )
    
    # 等待所有完成
    results = await asyncio.gather(*tasks)
    
    # 汇总结果
    final_result = spawn_agent(
        agent_type=task["aggregation"]["agent"],
        task=task["aggregation"]["task"],
        input_data=results
    )
    
    return final_result
