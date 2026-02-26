"""
Workflow Engine - 工作流引擎
职责：执行计划，管理数据流
"""

import json
import subprocess
import time
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

from self_correction import SelfCorrection


class WorkflowEngine:
    """工作流引擎 - 执行多步骤任务"""
    
    def __init__(self, agents_json_path: str = "agents.json"):
        self.agents_json_path = Path(agents_json_path)
        self.agents = self._load_agents()
        self.context = {}  # 共享上下文（存储中间结果）
        self.corrector = SelfCorrection()  # 自我修正
        
    def _load_agents(self) -> Dict[str, Any]:
        """加载 Agent 配置"""
        if not self.agents_json_path.exists():
            return {}
        
        with open(self.agents_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            agents = {}
            for agent in data.get('agents', []):
                agent_id = agent.get('id') or agent.get('name')
                if agent_id:
                    agents[agent_id] = agent
            return agents
    
    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工作流计划
        
        Args:
            plan: Router 生成的执行计划
            
        Returns:
            执行结果
        """
        start_time = time.time()
        results = {
            "success": True,
            "steps_executed": 0,
            "steps_failed": 0,
            "final_output": None,
            "execution_time": 0,
            "errors": [],
            "context": {}
        }
        
        # 重置上下文
        self.context = {}
        
        # 顺序执行每个步骤
        for i, step in enumerate(plan.get('steps', [])):
            step_num = i + 1
            print(f"\n[Step {step_num}/{len(plan['steps'])}] 执行 {step['agent']}...")
            
            max_retries = 3
            attempt = 0
            step_success = False
            
            while attempt < max_retries and not step_success:
                try:
                    # 1. 解析参数（替换 {{变量}}）
                    params = self._resolve_params(step.get('params', {}))
                    
                    # 2. 执行 Agent
                    step_result = self._execute_agent(
                        agent_id=step['agent'],
                        action=step.get('action', 'execute'),
                        params=params,
                        timeout=step.get('timeout', 60)
                    )
                    
                    # 3. 保存输出到上下文
                    output_key = step.get('output_key', f'step_{step_num}_output')
                    self.context[output_key] = step_result
                    
                    # 4. 记录结果
                    results['steps_executed'] += 1
                    results['final_output'] = step_result.get('output')
                    
                    print(f"  [OK] 成功 (耗时: {step_result.get('execution_time', 0):.2f}s)")
                    step_success = True
                    
                except Exception as e:
                    attempt += 1
                    error_msg = f"Step {step_num} failed (attempt {attempt}/{max_retries}): {str(e)}"
                    print(f"  [FAIL] {error_msg}")
                    
                    # 自我修正
                    if attempt < max_retries:
                        print(f"  [CORRECTION] 分析失败原因...")
                        analysis = self.corrector.analyze_failure(step, str(e), self.context)
                        
                        if analysis['can_auto_fix']:
                            print(f"  [CORRECTION] 应用自动修复...")
                            step = self.corrector.apply_fix(step, analysis['suggested_fix'])
                            print(f"  [CORRECTION] 重试中...")
                        else:
                            print(f"  [CORRECTION] 无法自动修复: {analysis['root_cause']}")
                            break
                    else:
                        # 最终失败
                        results['success'] = False
                        results['steps_failed'] += 1
                        results['errors'].append({
                            "step": step_num,
                            "agent": step['agent'],
                            "error": str(e),
                            "attempts": attempt
                        })
                        
                        # 失败后是否继续？（默认中断）
                        if not step.get('continue_on_error', False):
                            break
        
        # 计算总耗时
        results['execution_time'] = time.time() - start_time
        results['context'] = self.context
        
        return results
    
    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析参数中的变量引用（{{variable}}）
        
        Args:
            params: 原始参数
            
        Returns:
            解析后的参数
        """
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and '{{' in value:
                # 提取变量名
                var_pattern = r'\{\{(\w+)\}\}'
                matches = re.findall(var_pattern, value)
                
                # 替换变量
                resolved_value = value
                for var_name in matches:
                    if var_name in self.context:
                        var_value = self.context[var_name]
                        # 如果是完整替换（整个字符串就是 {{var}}）
                        if value == f'{{{{{var_name}}}}}':
                            resolved_value = var_value
                        else:
                            # 部分替换
                            resolved_value = resolved_value.replace(
                                f'{{{{{var_name}}}}}',
                                str(var_value)
                            )
                
                resolved[key] = resolved_value
            else:
                resolved[key] = value
        
        return resolved
    
    def _execute_agent(
        self,
        agent_id: str,
        action: str,
        params: Dict[str, Any],
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        执行单个 Agent
        
        Args:
            agent_id: Agent ID
            action: 动作类型
            params: 参数
            timeout: 超时时间（秒）
            
        Returns:
            执行结果
        """
        # 1. 获取 Agent 配置
        agent_config = self.agents.get(agent_id)
        if not agent_config:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # 2. 获取脚本路径
        script_path = agent_config.get('script_path')
        if not script_path or not Path(script_path).exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # 3. 构建命令
        cmd = self._build_command(script_path, action, params)
        
        # 4. 执行命令
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'  # 忽略编码错误
            )
            
            execution_time = time.time() - start_time
            
            # 5. 解析输出
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip(),
                    "execution_time": execution_time,
                    "exit_code": 0
                }
            else:
                raise RuntimeError(
                    f"Command failed (exit code {result.returncode}): {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Agent execution timeout ({timeout}s)")
    
    def _build_command(
        self,
        script_path: str,
        action: str,
        params: Dict[str, Any]
    ) -> List[str]:
        """构建执行命令"""
        cmd = [
            "C:\\Program Files\\Python312\\python.exe",
            script_path
        ]
        
        # 添加参数
        for key, value in params.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])
        
        return cmd


# 测试代码
if __name__ == "__main__":
    from router_agent import RouterAgent
    
    # 初始化
    router = RouterAgent("agents.json")
    engine = WorkflowEngine("agents.json")
    
    # 测试场景 1：简单任务
    print("=== 测试 1：健康检查 ===")
    plan1 = router.route("检查系统健康")
    result1 = engine.execute(plan1)
    print(f"\n结果: {json.dumps(result1, indent=2, ensure_ascii=False)}")
    
    # 测试场景 2：复杂任务（需要数据传递）
    print("\n\n=== 测试 2：健康检查 + 生成报告 ===")
    plan2 = router.route("检查系统状态并生成报告")
    result2 = engine.execute(plan2)
    print(f"\n结果: {json.dumps(result2, indent=2, ensure_ascii=False)}")
