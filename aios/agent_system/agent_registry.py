"""
Agent Registry - Agent 注册表增强
职责：管理 Agent 元数据，支持 LLM 驱动的路由
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class AgentRegistry:
    """Agent 注册表"""
    
    def __init__(self, agents_json_path: str = "agents.json"):
        self.agents_json_path = Path(agents_json_path)
        self.agents = self._load_agents()
    
    def _load_agents(self) -> List[Dict[str, Any]]:
        """加载 Agent 配置"""
        if not self.agents_json_path.exists():
            return []
        
        with open(self.agents_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('agents', [])
    
    def get_agent_metadata(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取 Agent 元数据"""
        for agent in self.agents:
            if agent.get('name') == agent_name or agent.get('id') == agent_name:
                return self._extract_metadata(agent)
        return None
    
    def _extract_metadata(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """提取 Agent 元数据（用于 LLM）"""
        return {
            "name": agent.get('name') or agent.get('id'),
            "description": agent.get('goal') or agent.get('description', ''),
            "capabilities": agent.get('capabilities', self._infer_capabilities(agent)),
            "risk_level": agent.get('risk_level', self._infer_risk_level(agent)),
            "max_concurrency": agent.get('max_concurrency', 5),
            "timeout_default": agent.get('timeout_default', 60)
        }
    
    def _infer_capabilities(self, agent: Dict[str, Any]) -> List[str]:
        """推断 Agent 能力（基于现有字段）"""
        capabilities = []
        
        # 基于 type 推断
        agent_type = agent.get('type', '')
        if agent_type == 'monitoring':
            capabilities.extend(['read_metrics', 'check_status'])
        elif agent_type == 'analysis':
            capabilities.extend(['analyze_data', 'generate_report'])
        elif agent_type == 'development':
            capabilities.extend(['write_code', 'create_file'])
        
        # 基于 goal 推断
        goal = agent.get('goal', '').lower()
        if 'health' in goal or 'monitor' in goal:
            capabilities.append('read_metrics')
        if 'document' in goal or 'report' in goal:
            capabilities.append('format_markdown')
        if 'create' in goal or 'generate' in goal:
            capabilities.append('create_file')
        
        return list(set(capabilities)) or ['execute']
    
    def _infer_risk_level(self, agent: Dict[str, Any]) -> str:
        """推断风险等级"""
        # 基于 capabilities 推断
        capabilities = agent.get('capabilities', [])
        if 'restart_service' in capabilities or 'delete_file' in capabilities:
            return 'high'
        elif 'write_file' in capabilities or 'shell' in capabilities:
            return 'medium'
        else:
            return 'low'
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """获取所有 Agent 元数据（用于 LLM）"""
        return [self._extract_metadata(agent) for agent in self.agents]
    
    def search_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """根据能力搜索 Agent"""
        results = []
        for agent in self.agents:
            metadata = self._extract_metadata(agent)
            if capability in metadata['capabilities']:
                results.append(metadata)
        return results
    
    def search_by_description(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """根据描述关键词搜索 Agent"""
        results = []
        for agent in self.agents:
            metadata = self._extract_metadata(agent)
            description = metadata['description'].lower()
            if any(kw.lower() in description for kw in keywords):
                results.append(metadata)
        return results
    
    def to_llm_context(self) -> str:
        """
        生成 LLM 上下文（用于 Router）
        
        Returns:
            格式化的 Agent 列表描述
        """
        metadata_list = self.get_all_metadata()
        
        context = "Available Agents:\n\n"
        for i, metadata in enumerate(metadata_list, 1):
            context += f"{i}. {metadata['name']}\n"
            context += f"   Description: {metadata['description']}\n"
            context += f"   Capabilities: {', '.join(metadata['capabilities'])}\n"
            context += f"   Risk Level: {metadata['risk_level']}\n"
            context += f"   Default Timeout: {metadata['timeout_default']}s\n"
            context += "\n"
        
        return context


# 测试代码
if __name__ == "__main__":
    registry = AgentRegistry("agents.json")
    
    # 测试 1：获取所有元数据
    print("=== 测试 1: 获取所有 Agent 元数据 ===")
    all_metadata = registry.get_all_metadata()
    print(f"Total agents: {len(all_metadata)}")
    for metadata in all_metadata[:3]:  # 只显示前 3 个
        print(f"\n{metadata['name']}:")
        print(f"  Description: {metadata['description'][:50]}...")
        print(f"  Capabilities: {metadata['capabilities']}")
        print(f"  Risk Level: {metadata['risk_level']}")
    
    # 测试 2：根据能力搜索
    print("\n=== 测试 2: 搜索具有 'read_metrics' 能力的 Agent ===")
    results = registry.search_by_capability('read_metrics')
    print(f"Found {len(results)} agents:")
    for agent in results:
        print(f"  - {agent['name']}")
    
    # 测试 3：根据描述搜索
    print("\n=== 测试 3: 搜索描述中包含 'health' 的 Agent ===")
    results = registry.search_by_description(['health', 'monitor'])
    print(f"Found {len(results)} agents:")
    for agent in results:
        print(f"  - {agent['name']}: {agent['description'][:50]}...")
    
    # 测试 4：生成 LLM 上下文
    print("\n=== 测试 4: 生成 LLM 上下文 ===")
    llm_context = registry.to_llm_context()
    print(llm_context[:500] + "...")
