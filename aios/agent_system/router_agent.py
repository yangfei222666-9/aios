"""
Router Agent - 路由总管
职责：理解用户意图，生成执行计划
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class RouterAgent:
    """路由总管 - 将自然语言转换为执行计划"""
    
    def __init__(self, agents_json_path: str = "agents.json"):
        self.agents_json_path = Path(agents_json_path)
        self.agents = self._load_agents()
        
    def _load_agents(self) -> Dict[str, Any]:
        """加载 Agent 配置"""
        if not self.agents_json_path.exists():
            return {}
        
        with open(self.agents_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            agents = {}
            for agent in data.get('agents', []):
                # 兼容有 id 和没有 id 的 Agent
                agent_id = agent.get('id') or agent.get('name')
                if agent_id:
                    agents[agent_id] = agent
            return agents
    
    def route(self, user_input: str) -> Dict[str, Any]:
        """
        路由用户输入，生成执行计划
        
        Args:
            user_input: 用户的自然语言指令
            
        Returns:
            执行计划（JSON）
        """
        # 1. 意图识别
        intent = self._identify_intent(user_input)
        
        # 2. 任务拆解
        steps = self._decompose_task(user_input, intent)
        
        # 3. 生成计划
        plan = {
            "intent": intent,
            "user_input": user_input,
            "steps": steps,
            "estimated_time": sum(step.get("timeout", 60) for step in steps)
        }
        
        return plan
    
    def _identify_intent(self, user_input: str) -> str:
        """识别用户意图"""
        user_lower = user_input.lower()
        
        # 关键词匹配
        intent_keywords = {
            "health_check": ["健康", "状态", "检查", "health", "status", "check"],
            "document_process": ["文档", "处理", "分析", "document", "process", "analyze"],
            "skill_create": ["创建", "技能", "skill", "create"],
            "report_generate": ["报告", "生成", "report", "generate"],
            "multi_task": ["并且", "然后", "接着", "and", "then"]
        }
        
        matched_intents = []
        for intent, keywords in intent_keywords.items():
            if any(kw in user_lower for kw in keywords):
                matched_intents.append(intent)
        
        # 多意图 → 组合任务
        if len(matched_intents) > 1:
            return "_".join(matched_intents)
        elif matched_intents:
            return matched_intents[0]
        else:
            return "unknown"
    
    def _decompose_task(self, user_input: str, intent: str) -> List[Dict[str, Any]]:
        """任务拆解"""
        steps = []
        
        # 预定义的任务模板
        task_templates = {
            "health_check": [
                {
                    "agent": "aios-health-check_agent",  # 使用完整 ID
                    "action": "execute",
                    "params": {},
                    "output_key": "health_data",
                    "timeout": 30
                }
            ],
            "document_process": [
                {
                    "agent": "document-agent_agent",  # 使用完整 ID
                    "action": "process",
                    "params": self._extract_file_path(user_input),
                    "output_key": "document_result",
                    "timeout": 60
                }
            ],
            "health_check_report_generate": [
                {
                    "agent": "aios-health-check_agent",  # 使用完整 ID
                    "action": "execute",
                    "params": {},
                    "output_key": "health_data",
                    "timeout": 30
                }
                # 注意：document-agent 需要文件路径，暂时只执行健康检查
                # TODO: 实现基于内存数据的报告生成
            ]
        }
        
        # 匹配模板
        if intent in task_templates:
            steps = task_templates[intent]
        else:
            # 未知意图 → 尝试智能匹配
            steps = self._smart_match(user_input)
        
        return steps
    
    def _extract_file_path(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取文件路径"""
        # 匹配常见路径格式
        path_patterns = [
            r'[A-Za-z]:\\[^\s]+',  # Windows 路径
            r'/[^\s]+',             # Unix 路径
            r'[^\s]+\.(txt|pdf|docx|md)'  # 文件扩展名
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, user_input)
            if match:
                return {"file_path": match.group(0)}
        
        return {}
    
    def _smart_match(self, user_input: str) -> List[Dict[str, Any]]:
        """智能匹配 Agent（基于能力描述）"""
        user_lower = user_input.lower()
        matched_agents = []
        
        for agent_id, agent_config in self.agents.items():
            # 检查 Agent 的能力描述
            capabilities = agent_config.get('capabilities', [])
            description = agent_config.get('description', '').lower()
            
            # 关键词匹配
            if any(cap.lower() in user_lower for cap in capabilities):
                matched_agents.append({
                    "agent": agent_id,
                    "action": "execute",
                    "params": {},
                    "output_key": f"{agent_id}_result",
                    "timeout": 60,
                    "confidence": 0.8
                })
            elif any(word in description for word in user_lower.split()):
                matched_agents.append({
                    "agent": agent_id,
                    "action": "execute",
                    "params": {},
                    "output_key": f"{agent_id}_result",
                    "timeout": 60,
                    "confidence": 0.5
                })
        
        # 按置信度排序
        matched_agents.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # 返回最匹配的 Agent（最多 3 个）
        return matched_agents[:3]
    
    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """验证执行计划的有效性"""
        if not plan.get('steps'):
            return False
        
        for step in plan['steps']:
            # 检查 Agent 是否存在
            agent_id = step.get('agent')
            if agent_id not in self.agents:
                return False
            
            # 检查必需字段
            if not all(k in step for k in ['action', 'output_key']):
                return False
        
        return True


# 测试代码
if __name__ == "__main__":
    router = RouterAgent("agents.json")
    
    # 测试场景 1：简单任务
    print("=== 测试 1：健康检查 ===")
    plan1 = router.route("检查系统健康")
    print(json.dumps(plan1, indent=2, ensure_ascii=False))
    
    # 测试场景 2：复杂任务
    print("\n=== 测试 2：健康检查 + 生成报告 ===")
    plan2 = router.route("检查系统状态并生成报告")
    print(json.dumps(plan2, indent=2, ensure_ascii=False))
    
    # 测试场景 3：文档处理
    print("\n=== 测试 3：文档处理 ===")
    plan3 = router.route("分析文档 C:\\Users\\A\\test.pdf")
    print(json.dumps(plan3, indent=2, ensure_ascii=False))
    
    # 验证计划
    print("\n=== 验证计划 ===")
    print(f"Plan 1 valid: {router.validate_plan(plan1)}")
    print(f"Plan 2 valid: {router.validate_plan(plan2)}")
    print(f"Plan 3 valid: {router.validate_plan(plan3)}")
