"""
工作流进度追踪器
Agent 通过这个模块报告工作流执行进度
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class WorkflowProgressTracker:
    """工作流进度追踪器"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.progress_file = self.workspace / "aios" / "agent_system" / "workflow_progress.jsonl"
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
    
    def report_stage_start(self, execution_id: str, stage_id: str, agent_id: str):
        """报告阶段开始"""
        self._append_progress({
            "execution_id": execution_id,
            "stage_id": stage_id,
            "agent_id": agent_id,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
    
    def report_stage_progress(self, execution_id: str, stage_id: str, 
                             progress: float, message: str):
        """报告阶段进度（0.0-1.0）"""
        self._append_progress({
            "execution_id": execution_id,
            "stage_id": stage_id,
            "status": "in_progress",
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def report_stage_complete(self, execution_id: str, stage_id: str, 
                             output: Any, metrics: Optional[Dict] = None):
        """报告阶段完成"""
        self._append_progress({
            "execution_id": execution_id,
            "stage_id": stage_id,
            "status": "completed",
            "output": output,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def report_stage_failed(self, execution_id: str, stage_id: str, 
                           error: str, retry_count: int = 0):
        """报告阶段失败"""
        self._append_progress({
            "execution_id": execution_id,
            "stage_id": stage_id,
            "status": "failed",
            "error": error,
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_execution_progress(self, execution_id: str) -> Dict:
        """获取执行进度"""
        if not self.progress_file.exists():
            return {"execution_id": execution_id, "stages": []}
        
        stages = []
        with open(self.progress_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record.get("execution_id") == execution_id:
                        stages.append(record)
        
        return {
            "execution_id": execution_id,
            "stages": stages,
            "total_stages": len(set(s["stage_id"] for s in stages)),
            "completed_stages": len([s for s in stages if s["status"] == "completed"]),
            "failed_stages": len([s for s in stages if s["status"] == "failed"])
        }
    
    def _append_progress(self, record: Dict):
        """追加进度记录"""
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# 便捷函数（供 Agent 使用）
_tracker = None

def init_tracker(workspace: Path):
    """初始化追踪器"""
    global _tracker
    _tracker = WorkflowProgressTracker(workspace)

def report_start(execution_id: str, stage_id: str, agent_id: str):
    """报告开始"""
    if _tracker:
        _tracker.report_stage_start(execution_id, stage_id, agent_id)

def report_progress(execution_id: str, stage_id: str, progress: float, message: str):
    """报告进度"""
    if _tracker:
        _tracker.report_stage_progress(execution_id, stage_id, progress, message)

def report_complete(execution_id: str, stage_id: str, output: Any, metrics: Optional[Dict] = None):
    """报告完成"""
    if _tracker:
        _tracker.report_stage_complete(execution_id, stage_id, output, metrics)

def report_failed(execution_id: str, stage_id: str, error: str, retry_count: int = 0):
    """报告失败"""
    if _tracker:
        _tracker.report_stage_failed(execution_id, stage_id, error, retry_count)


if __name__ == "__main__":
    # 测试
    from pathlib import Path
    
    workspace = Path("C:/Users/A/.openclaw/workspace")
    tracker = WorkflowProgressTracker(workspace)
    
    # 模拟工作流执行
    execution_id = "test-exec-001"
    
    tracker.report_stage_start(execution_id, "1_understand", "coder-dispatcher")
    tracker.report_stage_progress(execution_id, "1_understand", 0.5, "正在分析需求...")
    tracker.report_stage_complete(execution_id, "1_understand", {
        "requirements": ["支持TTL", "支持LRU", "线程安全"]
    }, metrics={"duration_sec": 5.2})
    
    tracker.report_stage_start(execution_id, "2_design", "coder-dispatcher")
    tracker.report_stage_failed(execution_id, "2_design", "设计方案不完整", retry_count=1)
    
    # 查看进度
    progress = tracker.get_execution_progress(execution_id)
    print(json.dumps(progress, indent=2, ensure_ascii=False))
