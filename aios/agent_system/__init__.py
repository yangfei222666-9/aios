"""
AIOS Agent System - 自主 Agent 管理系统主入口

统一接口，整合 AgentManager 和 TaskRouter
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .core.agent_manager import AgentManager
from .core.task_router import TaskRouter


class AgentSystem:
    """自主 Agent 管理系统"""
    
    def __init__(self, data_dir: str = None, config_dir: str = None):
        self.manager = AgentManager(data_dir)
        self.router = TaskRouter(config_dir)
        
        self.log_file = self.manager.data_dir / "system.log"
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def handle_task(self, message: str, auto_create: bool = True) -> Dict:
        """
        处理任务（主入口）
        
        Args:
            message: 用户消息
            auto_create: 是否自动创建 Agent
        
        Returns:
            {
                'status': 'success' | 'error',
                'action': 'assigned' | 'created' | 'failed',
                'agent_id': str,
                'agent_name': str,
                'task_analysis': Dict,
                'message': str
            }
        """
        start_time = time.time()
        
        try:
            # 1. 获取可用 Agent
            available_agents = self.manager.list_agents(status='active')
            
            # 2. 路由任务
            routing = self.router.route_task(message, available_agents)
            
            self._log(f"Task routing: {routing['action']} - {routing['reason']}")
            
            # 3. 执行路由决策
            if routing['action'] == 'assign':
                agent_id = routing['agent_id']
                agent = self.manager.get_agent(agent_id)
                
                return {
                    'status': 'success',
                    'action': 'assigned',
                    'agent_id': agent_id,
                    'agent_name': agent['name'],
                    'agent_template': agent['template'],
                    'task_analysis': routing['task_analysis'],
                    'message': f"任务已分配给 {agent['name']} ({agent_id})"
                }
            
            elif routing['action'] == 'create' and auto_create:
                template = routing['template']
                agent = self.manager.create_agent(template, message)
                
                self._log(f"Created new agent: {agent['id']} (template: {template})")
                
                return {
                    'status': 'success',
                    'action': 'created',
                    'agent_id': agent['id'],
                    'agent_name': agent['name'],
                    'agent_template': agent['template'],
                    'task_analysis': routing['task_analysis'],
                    'message': f"已创建新 Agent: {agent['name']} ({agent['id']})"
                }
            
            else:
                return {
                    'status': 'error',
                    'action': 'failed',
                    'task_analysis': routing['task_analysis'],
                    'message': f"无法路由任务: {routing.get('reason', 'Unknown')}"
                }
        
        except Exception as e:
            self._log(f"Error handling task: {str(e)}", level="ERROR")
            return {
                'status': 'error',
                'action': 'failed',
                'message': f"处理任务时出错: {str(e)}"
            }
        
        finally:
            duration = time.time() - start_time
            self._log(f"Task handled in {duration:.2f}s")
    
    def report_task_result(self, agent_id: str, success: bool, duration_sec: float):
        """
        报告任务执行结果
        
        Args:
            agent_id: Agent ID
            success: 是否成功
            duration_sec: 耗时（秒）
        """
        self.manager.update_stats(agent_id, success, duration_sec)
        self._log(f"Task result: agent={agent_id}, success={success}, duration={duration_sec:.2f}s")
    
    def cleanup_idle_agents(self, idle_hours: int = 24) -> List[str]:
        """
        清理闲置 Agent
        
        Args:
            idle_hours: 闲置时长阈值（小时）
        
        Returns:
            归档的 Agent ID 列表
        """
        idle_agents = self.manager.find_idle_agents(idle_hours)
        
        for agent_id in idle_agents:
            self.manager.archive_agent(agent_id, f"Idle for {idle_hours}+ hours")
            self._log(f"Archived idle agent: {agent_id}")
        
        return idle_agents
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        summary = self.manager.get_agent_summary()
        active_agents = self.manager.list_agents(status='active')
        
        # 按模板分组
        by_template = {}
        for agent in active_agents:
            template = agent['template']
            if template not in by_template:
                by_template[template] = []
            by_template[template].append({
                'id': agent['id'],
                'name': agent['name'],
                'tasks_completed': agent['stats']['tasks_completed'],
                'success_rate': agent['stats']['success_rate'],
                'last_active': agent['stats'].get('last_active')
            })
        
        return {
            'summary': summary,
            'active_agents_by_template': by_template,
            'total_active': len(active_agents)
        }
    
    def list_agents(self, template: str = None, status: str = 'active') -> List[Dict]:
        """列出 Agent"""
        return self.manager.list_agents(status=status, template=template)
    
    def get_agent_detail(self, agent_id: str) -> Optional[Dict]:
        """获取 Agent 详情"""
        return self.manager.get_agent(agent_id)


# CLI 接口
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m aios.agent_system <command> [args]")
        print("\nCommands:")
        print("  status              - Show system status")
        print("  list [template]     - List agents")
        print("  create <template>   - Create agent")
        print("  route <message>     - Test task routing")
        print("  cleanup [hours]     - Cleanup idle agents")
        sys.exit(1)
    
    system = AgentSystem()
    command = sys.argv[1]
    
    if command == 'status':
        status = system.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif command == 'list':
        template = sys.argv[2] if len(sys.argv) > 2 else None
        agents = system.list_agents(template=template)
        print(json.dumps(agents, indent=2, ensure_ascii=False))
    
    elif command == 'create':
        if len(sys.argv) < 3:
            print("Usage: create <template>")
            sys.exit(1)
        template = sys.argv[2]
        agent = system.manager.create_agent(template)
        print(f"Created: {agent['id']}")
        print(json.dumps(agent, indent=2, ensure_ascii=False))
    
    elif command == 'route':
        if len(sys.argv) < 3:
            print("Usage: route <message>")
            sys.exit(1)
        message = ' '.join(sys.argv[2:])
        result = system.handle_task(message, auto_create=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == 'cleanup':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        archived = system.cleanup_idle_agents(hours)
        print(f"Archived {len(archived)} agents: {', '.join(archived)}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
