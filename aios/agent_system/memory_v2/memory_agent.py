"""
memory_agent.py - Memory Agent 骨架

Day 1 只做最小闭环：
- build_memory_record()
- queue_memory_write() 先同步落库（后续再异步化）
- recall_success_cases()
- recall_failure_fixes()
"""

from __future__ import annotations

from memory_v2.memory_store import upsert_memory, search_memories
from memory_v2.schemas import MemoryRecord


class MemoryAgent:
    def build_memory_record(self, task: dict, result: dict) -> MemoryRecord:
        """把 task/result 结构化成统一 MemoryRecord。"""
        task_desc = task.get("description", "")
        task_type = task.get("type", "")
        task_id = task.get("id", "")

        success = bool(result.get("success", False)) if isinstance(result, dict) else False
        output = result.get("output", "") if isinstance(result, dict) else str(result)
        error = result.get("error", "") if isinstance(result, dict) else ""

        if success:
            memory_type = "success_case"
            outcome = "success"
            text = f"{task_desc} | {output}"[:1200]
            summary = task_desc[:240]
            error_type = ""
        else:
            memory_type = "failure_pattern"
            outcome = "failed"
            text = f"{task_desc} | ERROR: {error or output}"[:1200]
            summary = f"FAILED: {task_desc}"[:240]
            error_type = self.classify_error({"message": error or output})

        return MemoryRecord(
            id=task_id or None,
            text=text,
            summary=summary,
            memory_type=memory_type,
            task_type=task_type,
            error_type=error_type,
            source="task_execution",
            source_task_id=task_id,
            outcome=outcome,
            confidence=0.6 if success else 0.5,
            tags=[],
        )

    def queue_memory_write(self, memory: MemoryRecord) -> str:
        """Day 1 先同步写，接口名保留为 queue，后续可无缝替换成异步队列。"""
        return upsert_memory(memory)

    def recall_success_cases(self, new_task: dict, top_k: int = 5) -> list[dict]:
        return search_memories(
            query=new_task.get("description", ""),
            memory_type="success_case",
            task_type=new_task.get("type", ""),
            top_k=top_k,
        )

    def recall_failure_fixes(self, task: dict, error: dict, top_k: int = 5) -> list[dict]:
        err_type = self.classify_error(error)
        return search_memories(
            query=error.get("message", ""),
            memory_type=["failure_pattern", "fix_solution"],
            task_type=task.get("type", ""),
            error_type=err_type,
            top_k=top_k,
        )

    @staticmethod
    def classify_error(error: dict) -> str:
        msg = (error.get("message", "") or "").lower()
        if "timeout" in msg or "timed out" in msg:
            return "timeout"
        if "502" in msg or "503" in msg or "gateway" in msg:
            return "upstream_api_error"
        if "import" in msg or "module" in msg or "dependency" in msg:
            return "dependency_error"
        if "json" in msg or "schema" in msg or "parse" in msg:
            return "data_validation_error"
        return "unknown"


memory_agent = MemoryAgent()
