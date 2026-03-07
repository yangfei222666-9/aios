"""Workflow Designer Agent - 工作流设计和执行"""
import json
from pathlib import Path
from datetime import datetime

class WorkflowDesigner:
    def __init__(self):
        self.workflows_dir = Path("data/workflows")
        
    def create_workflow(self, name, steps):
        """创建工作流"""
        workflow = {
            "id": f"wf-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "status": "ready"
        }
        
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        wf_file = self.workflows_dir / f"{workflow['id']}.json"
        with open(wf_file, "w", encoding="utf-8") as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 工作流已创建: {workflow['id']}")
        return workflow
    
    def list_workflows(self):
        print("=" * 80)
        print("Workflow Designer - 工作流列表")
        print("=" * 80)
        
        if not self.workflows_dir.exists():
            print("\n✓ 暂无工作流")
            return []
        
        workflows = []
        for f in self.workflows_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as fp:
                wf = json.load(fp)
                workflows.append(wf)
                print(f"\n📋 {wf['name']} ({wf['id']})")
                print(f"   步骤数: {len(wf.get('steps', []))}")
                print(f"   状态: {wf.get('status')}")
        
        if not workflows:
            print("\n✓ 暂无工作流")
        
        print(f"\n{'=' * 80}")
        return workflows
    
    def run_workflow(self, workflow_id):
        """执行工作流"""
        wf_file = self.workflows_dir / f"{workflow_id}.json"
        if not wf_file.exists():
            print(f"✗ 工作流不存在: {workflow_id}")
            return
        
        with open(wf_file, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        
        print(f"\n🚀 执行工作流: {workflow['name']}")
        
        for i, step in enumerate(workflow.get("steps", []), 1):
            print(f"\n  步骤 {i}: {step.get('name')}")
            print(f"  Agent: {step.get('agent')}")
            print(f"  任务: {step.get('task')}")
            
            # 创建 spawn 请求
            spawn = {
                "timestamp": datetime.now().isoformat(),
                "agent": step.get("agent"),
                "task": step.get("task"),
                "workflow_id": workflow_id,
                "step": i,
                "status": "spawned"
            }
            
            with open("spawn_requests.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(spawn, ensure_ascii=False) + "\n")
            
            print(f"  ✓ 已提交")

if __name__ == "__main__":
    designer = WorkflowDesigner()
    
    # 创建示例工作流
    workflow = designer.create_workflow(
        "代码开发工作流",
        [
            {"name": "编写代码", "agent": "coder-dispatcher", "task": "实现功能"},
            {"name": "代码审查", "agent": "Code_Reviewer", "task": "审查代码质量"},
            {"name": "运行测试", "agent": "coder-dispatcher", "task": "运行单元测试"}
        ]
    )
    
    designer.list_workflows()
