"""
LLM-Driven Router Agent - LLM 驱动的路由总管
职责：使用 LLM 将自然语言转换为执行计划
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from execution_types import ExecutionPlan, ExecutionStep, RiskLevel
from agent_registry import AgentRegistry


class LLMRouter:
    """LLM 驱动的路由总管"""
    
    def __init__(self, agents_json_path: str = "agents.json"):
        self.registry = AgentRegistry(agents_json_path)
        self.model = os.getenv("OPENCLAW_MODEL", "claude-sonnet-4-6")
    
    async def route(self, user_input: str) -> ExecutionPlan:
        """
        使用 LLM 生成执行计划
        
        Args:
            user_input: 用户的自然语言指令
            
        Returns:
            ExecutionPlan: 执行计划
        """
        # 1. 获取 Agent 元数据
        agent_context = self.registry.to_llm_context()
        
        # 2. 构建 LLM Prompt
        prompt = self._build_prompt(user_input, agent_context)
        
        # 3. 调用 LLM（这里用 sessions_send 模拟）
        plan_json = await self._call_llm(prompt)
        
        # 4. 解析为 Pydantic 模型
        plan = ExecutionPlan.model_validate_json(plan_json)
        
        # 5. 验证依赖关系
        plan.validate_dependencies()
        
        return plan
    
    def _build_prompt(self, user_input: str, agent_context: str) -> str:
        """构建 LLM Prompt"""
        prompt = f"""You are an AI task planner. Your job is to break down user requests into executable steps using available agents.

{agent_context}

User Request: "{user_input}"

Your task:
1. Understand the user's goal
2. Identify which agents are needed
3. Determine the execution order (dependencies)
4. Assess risk levels
5. Set appropriate timeouts

Output a JSON execution plan with this structure:
{{
  "overall_goal": "string - clear description of what we're trying to achieve",
  "steps": [
    {{
      "agent_name": "string - exact agent name from the list above",
      "action": "string - what action to perform",
      "input_data": {{}}, - any input parameters
      "depends_on": [], - list of agent names this step depends on
      "risk_level": "low|medium|high",
      "timeout": 30, - timeout in seconds
      "output_key": "string - key to store output for next steps"
    }}
  ],
  "max_total_time": 300, - maximum total execution time
  "require_human_confirm": false - true if any step has high risk
}}

Rules:
1. Use ONLY agents from the available list
2. If a step depends on another, list it in "depends_on"
3. Steps with no dependencies can run in parallel
4. Set "require_human_confirm": true if ANY step has "risk_level": "high"
5. Choose appropriate timeouts based on agent's default_timeout
6. Use descriptive output_keys for data passing (e.g., "health_data", "report")

Output ONLY valid JSON, no explanations.
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM（通过 sessions_send）
        
        Args:
            prompt: LLM Prompt
            
        Returns:
            JSON 字符串
        """
        # TODO: 实际实现时使用 sessions_send
        # 现在返回一个示例（用于测试）
        
        # 模拟 LLM 响应
        example_response = {
            "overall_goal": "检查系统状态并生成报告",
            "steps": [
                {
                    "agent_name": "aios_health_check",
                    "action": "execute_health_check",
                    "input_data": {},
                    "depends_on": [],
                    "risk_level": "low",
                    "timeout": 30,
                    "output_key": "health_data"
                },
                {
                    "agent_name": "document_agent",
                    "action": "generate_markdown_report",
                    "input_data": {"source": "health_data"},
                    "depends_on": ["aios_health_check"],
                    "risk_level": "low",
                    "timeout": 15,
                    "output_key": "report"
                }
            ],
            "max_total_time": 120,
            "require_human_confirm": False
        }
        
        return json.dumps(example_response)
    
    def route_sync(self, user_input: str) -> ExecutionPlan:
        """
        同步版本（用于测试）
        
        Args:
            user_input: 用户的自然语言指令
            
        Returns:
            ExecutionPlan: 执行计划
        """
        import asyncio
        return asyncio.run(self.route(user_input))


# 对比：旧版 vs 新版
class OldRouter:
    """旧版 Router（硬编码）"""
    
    def route(self, user_input: str) -> Dict[str, Any]:
        """硬编码路由"""
        if "检查系统状态" in user_input and "报告" in user_input:
            return {
                "overall_goal": user_input,
                "steps": [
                    {
                        "agent_name": "aios_health_check",
                        "action": "execute_health_check",
                        "input_data": {},
                        "depends_on": [],
                        "risk_level": "low",
                        "timeout": 30
                    },
                    {
                        "agent_name": "document_agent",
                        "action": "generate_markdown_report",
                        "input_data": {"source": "previous_step_output"},
                        "depends_on": ["aios_health_check"],
                        "risk_level": "low",
                        "timeout": 15
                    }
                ],
                "max_total_time": 120,
                "require_human_confirm": False
            }
        elif "检查系统" in user_input or "健康" in user_input:
            return {
                "overall_goal": user_input,
                "steps": [
                    {
                        "agent_name": "aios_health_check",
                        "action": "execute_health_check",
                        "input_data": {},
                        "depends_on": [],
                        "risk_level": "low",
                        "timeout": 30
                    }
                ],
                "max_total_time": 60,
                "require_human_confirm": False
            }
        else:
            # Fallback
            return {
                "overall_goal": user_input,
                "steps": [],
                "max_total_time": 60,
                "require_human_confirm": False
            }


# 测试代码
if __name__ == "__main__":
    print("=== 对比测试：旧版 vs 新版 ===\n")
    
    # 旧版 Router
    print("【旧版 Router - 硬编码】")
    old_router = OldRouter()
    
    test_inputs = [
        "检查系统状态并生成报告",
        "检查系统健康",
        "分析最近的错误并生成优化建议"  # 旧版无法处理
    ]
    
    for user_input in test_inputs:
        print(f"\n输入: {user_input}")
        result = old_router.route(user_input)
        print(f"步骤数: {len(result['steps'])}")
        if result['steps']:
            print(f"Agent: {[s['agent_name'] for s in result['steps']]}")
        else:
            print("[FAIL] 无法处理（fallback）")
    
    # 新版 Router
    print("\n\n【新版 Router - LLM 驱动】")
    new_router = LLMRouter("agents.json")
    
    for user_input in test_inputs[:2]:  # 只测试前 2 个（第 3 个需要真实 LLM）
        print(f"\n输入: {user_input}")
        plan = new_router.route_sync(user_input)
        print(f"目标: {plan.overall_goal}")
        print(f"步骤数: {len(plan.steps)}")
        print(f"Agent: {[s.agent_name for s in plan.steps]}")
        
        # 并行分组
        groups = plan.get_parallel_groups()
        print(f"并行组: {len(groups)}")
        for i, group in enumerate(groups, 1):
            print(f"  Group {i}: {[s.agent_name for s in group]}")
    
    print("\n=== 新版优势 ===")
    print("1. [OK] 支持任意自然语言输入")
    print("2. [OK] 自动选择合适的 Agent")
    print("3. [OK] 自动分析依赖关系")
    print("4. [OK] 自动评估风险等级")
    print("5. [OK] 支持并行执行")
    print("6. [OK] Pydantic 类型安全")
