"""
Agent 协作演示：代码审查流程

场景：
1. Coder Agent 写代码
2. Reviewer Agent 审查代码
3. Tester Agent 测试代码
4. 如果有问题，返回给 Coder 修复
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from auto_dispatcher import AutoDispatcher

class CollaborationDemo:
    """Agent 协作演示"""
    
    def __init__(self):
        workspace = Path(__file__).parent.parent.parent
        self.dispatcher = AutoDispatcher(workspace)
        self.workflow_log = []
    
    def log(self, step: str, agent: str, message: str):
        """记录工作流日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "agent": agent,
            "message": message
        }
        self.workflow_log.append(entry)
        print(f"[{step}] {agent}: {message}")
    
    def code_review_workflow(self, feature: str):
        """
        代码审查工作流
        
        Args:
            feature: 功能描述
        """
        print("\n" + "=" * 60)
        print(f"[START] 启动代码审查工作流: {feature}")
        print("=" * 60)
        
        # Step 1: Coder 写代码
        self.log("1-CODE", "coder", f"开始编写功能: {feature}")
        coder_task = {
            "type": "code",
            "message": f"实现功能: {feature}",
            "priority": "high"
        }
        self.dispatcher.enqueue_task(coder_task)
        
        # Step 2: Reviewer 审查代码
        self.log("2-REVIEW", "reviewer", "等待代码完成后审查")
        reviewer_task = {
            "type": "analysis",
            "message": f"审查代码: {feature}（检查代码质量、安全性、性能）",
            "priority": "high"
        }
        self.dispatcher.enqueue_task(reviewer_task)
        
        # Step 3: Tester 测试代码
        self.log("3-TEST", "tester", "等待审查通过后测试")
        tester_task = {
            "type": "monitor",
            "message": f"测试功能: {feature}（单元测试、集成测试）",
            "priority": "normal"
        }
        self.dispatcher.enqueue_task(tester_task)
        
        # Step 4: 处理任务队列
        print("\n" + "-" * 60)
        print("📋 处理任务队列...")
        print("-" * 60)
        results = self.dispatcher.process_queue(max_tasks=3)
        
        for i, r in enumerate(results, 1):
            task_type = r.get('type', 'unknown')
            message = r.get('message', r.get('task', {}).get('message', 'N/A'))[:50]
            status = r.get('result', {}).get('status', r.get('status', 'unknown'))
            print(f"  {i}. [{task_type}] {message}... → {status}")
        
        # Step 5: 生成报告
        print("\n" + "=" * 60)
        print("[REPORT] 工作流报告")
        print("=" * 60)
        print(f"总步骤: {len(self.workflow_log)}")
        print(f"处理任务: {len(results)}")
        print(f"完成时间: {datetime.now().isoformat()}")
        
        return {
            "workflow_log": self.workflow_log,
            "results": results
        }
    
    def parallel_workflow(self, tasks: list):
        """
        并行工作流（多个独立任务同时执行）
        
        Args:
            tasks: 任务列表 [{"type": "code", "message": "...", "priority": "high"}, ...]
        """
        print("\n" + "=" * 60)
        print(f"[ZAP] 启动并行工作流: {len(tasks)} 个任务")
        print("=" * 60)
        
        # 批量入队
        for i, task in enumerate(tasks, 1):
            self.dispatcher.enqueue_task(task)
            self.log(f"ENQUEUE-{i}", task['type'], task['message'][:50])
        
        # 批量处理
        print("\n" + "-" * 60)
        print("📋 并行处理任务...")
        print("-" * 60)
        results = self.dispatcher.process_queue(max_tasks=len(tasks))
        
        for i, r in enumerate(results, 1):
            task_type = r.get('type', 'unknown')
            message = r.get('message', r.get('task', {}).get('message', 'N/A'))[:50]
            status = r.get('result', {}).get('status', r.get('status', 'unknown'))
            print(f"  {i}. [{task_type}] {message}... → {status}")
        
        return results


def demo_code_review():
    """演示：代码审查流程"""
    demo = CollaborationDemo()
    result = demo.code_review_workflow("用户登录功能")
    
    # 保存日志
    log_file = Path(__file__).parent / "data" / "collaboration_demo.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] 日志已保存: {log_file}")


def demo_parallel():
    """演示：并行工作流"""
    demo = CollaborationDemo()
    
    tasks = [
        {"type": "code", "message": "实现用户注册 API", "priority": "high"},
        {"type": "code", "message": "实现密码重置功能", "priority": "high"},
        {"type": "analysis", "message": "分析系统性能瓶颈", "priority": "normal"},
        {"type": "monitor", "message": "监控数据库连接池", "priority": "low"},
    ]
    
    results = demo.parallel_workflow(tasks)
    print(f"\n[OK] 并行处理完成: {len(results)} 个任务")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "parallel":
        demo_parallel()
    else:
        demo_code_review()
