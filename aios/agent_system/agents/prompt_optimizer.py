"""Prompt Optimizer - 自动优化 Agent Prompt"""
import json
from pathlib import Path
from datetime import datetime

class PromptOptimizer:
    def __init__(self):
        self.agents_file = Path("agents.json")
        self.prompt_log = Path("data/prompts/optimization_log.jsonl")
        
        # 优化规则
        self.rules = [
            {"check": lambda p: len(p) < 50, "fix": "添加更多上下文和示例", "impact": "high"},
            {"check": lambda p: "step" not in p.lower() and "步骤" not in p, "fix": "添加分步骤指令", "impact": "medium"},
            {"check": lambda p: "output" not in p.lower() and "输出" not in p, "fix": "明确输出格式", "impact": "medium"},
            {"check": lambda p: "example" not in p.lower() and "示例" not in p, "fix": "添加示例", "impact": "low"}
        ]
    
    def optimize(self):
        print("=" * 80)
        print("Prompt Optimizer - Prompt 优化")
        print("=" * 80)
        
        if not self.agents_file.exists():
            print("\n✗ agents.json 不存在")
            return
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        print(f"\n🔍 分析 {len(agents)} 个 Agent 的 Prompt...\n")
        
        suggestions = []
        for agent in agents:
            name = agent.get("name", "unknown")
            goal = agent.get("goal", "")
            backstory = agent.get("backstory", "")
            prompt = goal + " " + backstory
            
            agent_suggestions = []
            for rule in self.rules:
                if rule["check"](prompt):
                    agent_suggestions.append(rule["fix"])
            
            if agent_suggestions:
                print(f"📌 {name}:")
                for s in agent_suggestions:
                    print(f"   • {s}")
                suggestions.append({"agent": name, "suggestions": agent_suggestions})
        
        if not suggestions:
            print("✓ 所有 Prompt 质量良好")
        else:
            print(f"\n💡 共 {len(suggestions)} 个 Agent 的 Prompt 可以优化")
        
        # 保存
        self.prompt_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.prompt_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": datetime.now().isoformat(), "suggestions": suggestions}, ensure_ascii=False) + "\n")
        
        print(f"\n{'=' * 80}")

if __name__ == "__main__":
    optimizer = PromptOptimizer()
    optimizer.optimize()
