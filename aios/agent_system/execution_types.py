"""
Execution Plan Types - Pydantic 模型
职责：定义执行计划的数据结构
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StepAction(str, Enum):
    """步骤动作类型"""
    EXECUTE = "execute"
    EXECUTE_HEALTH_CHECK = "execute_health_check"
    GENERATE_MARKDOWN_REPORT = "generate_markdown_report"
    ANALYZE_DATA = "analyze_data"
    PROCESS_DOCUMENT = "process_document"


class ExecutionStep(BaseModel):
    """执行步骤"""
    agent_name: str = Field(..., description="Agent 名称")
    action: str = Field(..., description="动作类型")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    depends_on: List[str] = Field(default_factory=list, description="依赖的步骤（Agent 名称）")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="风险等级")
    timeout: int = Field(default=60, description="超时时间（秒）")
    output_key: Optional[str] = Field(None, description="输出键名（用于数据传递）")
    
    class Config:
        use_enum_values = True


class ExecutionPlan(BaseModel):
    """执行计划"""
    overall_goal: str = Field(..., description="总体目标")
    steps: List[ExecutionStep] = Field(..., description="执行步骤列表")
    max_total_time: int = Field(default=300, description="最大总耗时（秒）")
    require_human_confirm: bool = Field(default=False, description="是否需要人工确认")
    
    def get_parallel_groups(self) -> List[List[ExecutionStep]]:
        """
        根据依赖关系分组，返回可并行执行的步骤组
        
        Returns:
            List[List[ExecutionStep]]: 每组内的步骤可以并行执行
        """
        groups = []
        remaining_steps = self.steps.copy()
        completed = set()
        
        while remaining_steps:
            # 找出所有依赖已满足的步骤
            ready_steps = []
            for step in remaining_steps:
                if all(dep in completed for dep in step.depends_on):
                    ready_steps.append(step)
            
            if not ready_steps:
                # 循环依赖或无法满足的依赖
                raise ValueError(f"Circular dependency or unsatisfied dependency detected")
            
            # 这一组可以并行执行
            groups.append(ready_steps)
            
            # 标记为已完成
            for step in ready_steps:
                completed.add(step.agent_name)
                remaining_steps.remove(step)
        
        return groups
    
    def validate_dependencies(self) -> bool:
        """验证依赖关系是否有效"""
        agent_names = {step.agent_name for step in self.steps}
        
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in agent_names:
                    raise ValueError(f"Step '{step.agent_name}' depends on unknown agent '{dep}'")
        
        return True


class ExecutionResult(BaseModel):
    """执行结果"""
    success: bool = Field(..., description="是否成功")
    plan: ExecutionPlan = Field(..., description="执行计划")
    steps_executed: int = Field(default=0, description="已执行步骤数")
    steps_failed: int = Field(default=0, description="失败步骤数")
    total_time: float = Field(default=0, description="总耗时（秒）")
    final_output: Optional[Any] = Field(None, description="最终输出")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")


# 测试代码
if __name__ == "__main__":
    import json
    
    # 测试场景 1：简单任务（无依赖）
    print("=== 测试 1: 简单任务 ===")
    plan1 = ExecutionPlan(
        overall_goal="检查系统健康",
        steps=[
            ExecutionStep(
                agent_name="aios_health_check",
                action="execute_health_check",
                input_data={},
                depends_on=[],
                risk_level=RiskLevel.LOW,
                timeout=30
            )
        ],
        max_total_time=60,
        require_human_confirm=False
    )
    
    print(f"Goal: {plan1.overall_goal}")
    print(f"Steps: {len(plan1.steps)}")
    print(f"Parallel groups: {len(plan1.get_parallel_groups())}")
    
    # 测试场景 2：复杂任务（有依赖）
    print("\n=== 测试 2: 复杂任务（有依赖） ===")
    plan2 = ExecutionPlan(
        overall_goal="检查系统状态并生成报告",
        steps=[
            ExecutionStep(
                agent_name="aios_health_check",
                action="execute_health_check",
                input_data={},
                depends_on=[],
                risk_level=RiskLevel.LOW,
                timeout=30,
                output_key="health_data"
            ),
            ExecutionStep(
                agent_name="document_agent",
                action="generate_markdown_report",
                input_data={"source": "previous_step_output"},
                depends_on=["aios_health_check"],
                risk_level=RiskLevel.LOW,
                timeout=15,
                output_key="report"
            )
        ],
        max_total_time=120,
        require_human_confirm=False
    )
    
    print(f"Goal: {plan2.overall_goal}")
    print(f"Steps: {len(plan2.steps)}")
    groups = plan2.get_parallel_groups()
    print(f"Parallel groups: {len(groups)}")
    for i, group in enumerate(groups, 1):
        print(f"  Group {i}: {[step.agent_name for step in group]}")
    
    # 测试场景 3：并行任务（无依赖）
    print("\n=== 测试 3: 并行任务（无依赖） ===")
    plan3 = ExecutionPlan(
        overall_goal="同时检查系统、磁盘和网络",
        steps=[
            ExecutionStep(
                agent_name="system_check",
                action="execute",
                depends_on=[],
                timeout=30
            ),
            ExecutionStep(
                agent_name="disk_check",
                action="execute",
                depends_on=[],
                timeout=20
            ),
            ExecutionStep(
                agent_name="network_check",
                action="execute",
                depends_on=[],
                timeout=10
            )
        ],
        max_total_time=60
    )
    
    print(f"Goal: {plan3.overall_goal}")
    print(f"Steps: {len(plan3.steps)}")
    groups = plan3.get_parallel_groups()
    print(f"Parallel groups: {len(groups)}")
    for i, group in enumerate(groups, 1):
        print(f"  Group {i}: {[step.agent_name for step in group]} (可并行)")
    
    # 测试 JSON 序列化
    print("\n=== 测试 4: JSON 序列化 ===")
    plan_json = plan2.model_dump_json(indent=2)
    print(plan_json[:500] + "...")
