"""Documentation Generator Agent - 自动生成文档"""
import json
from pathlib import Path
from datetime import datetime

class DocumentationGenerator:
    def __init__(self):
        self.docs_dir = Path("docs")
        
    def generate_agent_docs(self):
        """为所有 Agent 生成文档"""
        print("=" * 80)
        print("Documentation Generator - 文档生成")
        print("=" * 80)
        
        agents_file = Path("agents.json")
        if not agents_file.exists():
            print("\n✗ agents.json 不存在")
            return
        
        with open(agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        print(f"\n📝 为 {len(agents)} 个 Agent 生成文档...\n")
        
        # 生成 README
        readme = self._generate_readme(agents)
        
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        readme_file = self.docs_dir / "AGENTS_README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme)
        
        print(f"✓ 已生成: {readme_file}")
        
        # 生成 API 文档
        api_doc = self._generate_api_doc(agents)
        api_file = self.docs_dir / "AGENTS_API.md"
        with open(api_file, "w", encoding="utf-8") as f:
            f.write(api_doc)
        
        print(f"✓ 已生成: {api_file}")
        print(f"\n{'=' * 80}")
    
    def _generate_readme(self, agents):
        lines = ["# AIOS Agent 文档\n", f"*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"]
        lines.append(f"## 概览\n\n共 {len(agents)} 个 Agent\n\n")
        
        # 按类型分组
        by_type = {}
        for agent in agents:
            t = agent.get("type", "other")
            by_type.setdefault(t, []).append(agent)
        
        for agent_type, type_agents in sorted(by_type.items()):
            lines.append(f"## {agent_type.upper()} ({len(type_agents)} 个)\n\n")
            for agent in type_agents:
                lines.append(f"### {agent.get('name')}\n")
                lines.append(f"- **角色:** {agent.get('role', '未定义')}\n")
                lines.append(f"- **目标:** {agent.get('goal', '未定义')}\n")
                lines.append(f"- **模型:** {agent.get('model', '未定义')}\n")
                lines.append(f"- **调度:** {agent.get('schedule', '未定义')}\n\n")
        
        return "".join(lines)
    
    def _generate_api_doc(self, agents):
        lines = ["# AIOS Agent API 文档\n\n"]
        for agent in agents:
            script = agent.get("script_path", "")
            if script:
                lines.append(f"## {agent.get('name')}\n")
                lines.append(f"```bash\n& \"C:\\Program Files\\Python312\\python.exe\" -X utf8 {script}\n```\n\n")
        return "".join(lines)

if __name__ == "__main__":
    generator = DocumentationGenerator()
    generator.generate_agent_docs()
