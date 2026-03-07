"""Model Router Agent - 根据任务自动选择最优模型"""
import json
from datetime import datetime
from pathlib import Path

class ModelRouter:
    def __init__(self):
        self.agents_file = Path("agents.json")
        self.routing_log = Path("data/model_routing/routing_log.jsonl")
        
        # 模型能力和成本
        self.models = {
            "claude-haiku-4-5": {
                "speed": 10,       # 最快
                "quality": 6,      # 一般
                "cost": 1,         # 最便宜
                "context": 200000,
                "best_for": ["simple", "short", "classification", "extraction"]
            },
            "claude-sonnet-4-5": {
                "speed": 7,
                "quality": 8,
                "cost": 4,
                "context": 200000,
                "best_for": ["analysis", "monitor", "review", "summary"]
            },
            "claude-sonnet-4-6": {
                "speed": 7,
                "quality": 9,
                "cost": 4,
                "context": 200000,
                "best_for": ["analysis", "code", "research"]
            },
            "claude-opus-4-5": {
                "speed": 4,
                "quality": 10,     # 最强
                "cost": 10,        # 最贵
                "context": 200000,
                "best_for": ["complex_code", "architecture", "deep_analysis", "creative"]
            }
        }
        
        # 任务类型 → 模型映射规则
        self.routing_rules = {
            "simple": "claude-haiku-4-5",
            "classification": "claude-haiku-4-5",
            "extraction": "claude-haiku-4-5",
            "monitor": "claude-sonnet-4-5",
            "analysis": "claude-sonnet-4-6",
            "review": "claude-sonnet-4-5",
            "code": "claude-sonnet-4-6",
            "test": "claude-sonnet-4-5",
            "refactor": "claude-opus-4-5",
            "architecture": "claude-opus-4-5",
            "complex_code": "claude-opus-4-5"
        }
    
    def route(self, task):
        """为任务选择最优模型"""
        task_type = task.get("type", "code")
        priority = task.get("priority", "normal")
        description = task.get("description", "")
        
        # 1. 分析任务复杂度
        complexity = self._analyze_complexity(description, task_type)
        
        # 2. 根据复杂度和优先级选择模型
        model = self._select_model(task_type, complexity, priority)
        
        # 3. 记录路由决策
        self._log_routing(task, model, complexity)
        
        return model
    
    def route_all_agents(self):
        """为所有 Agent 优化模型配置"""
        print("=" * 80)
        print("Model Router - 模型路由优化")
        print("=" * 80)
        
        if not self.agents_file.exists():
            print("\n✗ agents.json 不存在")
            return
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        print(f"\n🤖 分析 {len(agents)} 个 Agent 的模型配置...\n")
        
        changes = []
        for agent in agents:
            name = agent.get("name", "unknown")
            current_model = agent.get("model", "unknown")
            agent_type = agent.get("type", "")
            role = agent.get("role", "")
            
            # 推荐模型
            recommended = self._recommend_model_for_agent(agent)
            
            if recommended and recommended != current_model:
                print(f"📌 {name}")
                print(f"   当前: {current_model}")
                print(f"   推荐: {recommended}")
                print(f"   原因: {self._get_recommendation_reason(agent, recommended)}\n")
                
                changes.append({
                    "agent": name,
                    "from": current_model,
                    "to": recommended
                })
        
        if not changes:
            print("✓ 所有 Agent 的模型配置已是最优")
        else:
            print(f"\n💡 共有 {len(changes)} 个 Agent 可以优化")
            
            # 询问是否应用
            print("\n是否应用优化？(已自动应用)")
            self._apply_changes(agents, changes, data)
        
        print(f"\n{'=' * 80}")
    
    def _analyze_complexity(self, description, task_type):
        """分析任务复杂度"""
        complexity_score = 0
        
        # 长度
        if len(description) > 500:
            complexity_score += 3
        elif len(description) > 200:
            complexity_score += 2
        else:
            complexity_score += 1
        
        # 关键词
        complex_keywords = ["架构", "重构", "优化", "设计", "分析", "architecture", "refactor", "optimize", "design"]
        simple_keywords = ["检查", "查看", "列出", "check", "list", "show", "get"]
        
        for kw in complex_keywords:
            if kw in description.lower():
                complexity_score += 2
        
        for kw in simple_keywords:
            if kw in description.lower():
                complexity_score -= 1
        
        # 任务类型
        type_complexity = {
            "architecture": 5,
            "refactor": 4,
            "code": 3,
            "analysis": 3,
            "test": 2,
            "monitor": 1,
            "simple": 1
        }
        complexity_score += type_complexity.get(task_type, 2)
        
        # 分级
        if complexity_score >= 8:
            return "high"
        elif complexity_score >= 5:
            return "medium"
        else:
            return "low"
    
    def _select_model(self, task_type, complexity, priority):
        """选择模型"""
        # 高复杂度 → Opus
        if complexity == "high":
            return "claude-opus-4-5"
        
        # 紧急任务 → 快速模型
        if priority == "urgent":
            return "claude-sonnet-4-5"
        
        # 低复杂度 → Haiku（省钱）
        if complexity == "low" and priority == "low":
            return "claude-haiku-4-5"
        
        # 默认按任务类型路由
        return self.routing_rules.get(task_type, "claude-sonnet-4-5")
    
    def _recommend_model_for_agent(self, agent):
        """为 Agent 推荐最优模型"""
        agent_type = agent.get("type", "")
        role = agent.get("role", "").lower()
        schedule = agent.get("schedule", "")
        
        # 监控类 → Sonnet（平衡）
        if agent_type == "monitor" or "monitor" in role:
            return "claude-sonnet-4-5"
        
        # 学习类 → Sonnet（频繁调用，控制成本）
        if agent_type == "learning" or schedule in ["daily", "hourly"]:
            return "claude-sonnet-4-5"
        
        # 分析类 → Sonnet 4.6（更强）
        if agent_type == "analysis" or "analyst" in role:
            return "claude-sonnet-4-6"
        
        # 核心代码类 → Opus（最强）
        if "coder" in role or "developer" in role:
            return "claude-opus-4-5"
        
        return None
    
    def _get_recommendation_reason(self, agent, model):
        """获取推荐原因"""
        reasons = {
            "claude-haiku-4-5": "任务简单，使用 Haiku 可节省 80% 成本",
            "claude-sonnet-4-5": "平衡速度和质量，适合日常任务",
            "claude-sonnet-4-6": "更强的分析能力，适合复杂分析",
            "claude-opus-4-5": "最强模型，适合复杂代码和架构设计"
        }
        return reasons.get(model, "综合评估最优")
    
    def _apply_changes(self, agents, changes, data):
        """应用模型变更"""
        change_map = {c["agent"]: c["to"] for c in changes}
        
        for agent in agents:
            name = agent.get("name")
            if name in change_map:
                agent["model"] = change_map[name]
        
        # 保存
        if isinstance(data, list):
            with open(self.agents_file, "w", encoding="utf-8") as f:
                json.dump(agents, f, ensure_ascii=False, indent=2)
        else:
            data["agents"] = agents
            with open(self.agents_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已应用 {len(changes)} 个模型优化")
    
    def _log_routing(self, task, model, complexity):
        """记录路由决策"""
        log = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.get("id"),
            "task_type": task.get("type"),
            "complexity": complexity,
            "selected_model": model
        }
        
        self.routing_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.routing_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    router = ModelRouter()
    router.route_all_agents()
