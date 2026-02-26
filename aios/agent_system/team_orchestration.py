"""
Team Orchestration - 统一入口
职责：整合 Router + Workflow + Self-Correction + History
"""

import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

from router_agent import RouterAgent
from workflow_engine import WorkflowEngine
from execution_history import ExecutionHistory


class TeamOrchestration:
    """团队协同 - 统一入口"""
    
    def __init__(self, agents_json_path: str = "agents.json"):
        self.agents_json_path = agents_json_path
        self.router = RouterAgent(agents_json_path)
        self.workflow = WorkflowEngine(agents_json_path)
        self.history = ExecutionHistory("execution_history.jsonl")  # 新增：历史记录
        
    def execute(
        self,
        user_input: str,
        max_retries: int = 3,
        timeout: int = 180
    ) -> Dict[str, Any]:
        """
        执行用户任务
        
        Args:
            user_input: 用户的自然语言指令
            max_retries: 最大重试次数
            timeout: 总超时时间（秒）
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        result = {
            "success": False,
            "user_input": user_input,
            "plan": None,
            "workflow_result": None,
            "retries": 0,
            "total_time": 0,
            "error": None
        }
        
        try:
            # 1. 路由 - 生成执行计划
            print(f"[Router] 分析任务: {user_input}")
            plan = self.router.route(user_input)
            result['plan'] = plan
            
            # 验证计划
            if not self.router.validate_plan(plan):
                raise ValueError("Invalid execution plan")
            
            print(f"[Router] 生成计划: {len(plan['steps'])} 步骤")
            
            # 2. 执行工作流
            print(f"[Workflow] 开始执行...")
            workflow_result = self.workflow.execute(plan)
            result['workflow_result'] = workflow_result
            
            # 3. 检查结果
            if workflow_result['success']:
                result['success'] = True
                print(f"[Success] 任务完成!")
            else:
                # 失败 - 尝试自我修正（Phase 2 后续实现）
                print(f"[Failed] 任务失败: {workflow_result['errors']}")
                result['error'] = workflow_result['errors']
            
        except Exception as e:
            result['error'] = str(e)
            print(f"[Error] {e}")
        
        finally:
            result['total_time'] = time.time() - start_time
            
            # 保存到历史记录
            self.history.save({
                "user_input": user_input,
                "plan": result.get('plan'),
                "result": result,
                "success": result.get('success', False),
                "duration": result['total_time']
            })
        
        return result
    
    def execute_simple(self, user_input: str) -> str:
        """
        简化接口 - 直接返回最终输出
        
        Args:
            user_input: 用户指令
            
        Returns:
            最终输出（字符串）
        """
        result = self.execute(user_input)
        
        if result['success']:
            workflow_result = result.get('workflow_result', {})
            return workflow_result.get('final_output', 'No output')
        else:
            return f"Error: {result.get('error', 'Unknown error')}"
    
    def get_history(self, limit: int = 10) -> list:
        """获取执行历史"""
        return self.history.get_recent(limit)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.history.get_stats()
    
    def search_history(self, **kwargs) -> list:
        """搜索执行历史"""
        return self.history.search(**kwargs)


# 测试代码
if __name__ == "__main__":
    team = TeamOrchestration("agents.json")
    
    # 测试场景 1：简单任务
    print("=" * 60)
    print("测试 1：健康检查")
    print("=" * 60)
    result1 = team.execute("检查系统健康")
    print(f"\n最终输出:\n{result1['workflow_result']['final_output']}")
    print(f"\n总耗时: {result1['total_time']:.2f}s")
    
    # 测试场景 2：复杂任务
    print("\n" + "=" * 60)
    print("测试 2：健康检查 + 生成报告")
    print("=" * 60)
    result2 = team.execute("检查系统状态并生成报告")
    print(f"\n成功: {result2['success']}")
    print(f"步骤数: {len(result2['plan']['steps'])}")
    print(f"总耗时: {result2['total_time']:.2f}s")
    
    # 测试场景 3：简化接口
    print("\n" + "=" * 60)
    print("测试 3：简化接口")
    print("=" * 60)
    output = team.execute_simple("检查系统健康")
    print(f"输出: {output[:200]}...")  # 只显示前 200 字符
