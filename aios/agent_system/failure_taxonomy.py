"""
Failure Taxonomy - 两层错误分类系统

一级分类（System Layer）：
- model_error: LLM 相关错误
- tool_error: 工具调用错误
- planning_error: 规划/决策错误
- execution_error: 执行错误
- resource_error: 资源不足
- system_error: 系统级错误

二级分类（Root Cause）：详细原因
"""

import json
from datetime import datetime
from pathlib import Path

# 错误分类定义
TAXONOMY = {
    "model_error": {
        "timeout": "模型响应超时",
        "rate_limit": "API 速率限制",
        "hallucination": "模型幻觉/错误输出",
        "context_overflow": "上下文长度超限"
    },
    "tool_error": {
        "api_failure": "API 调用失败",
        "dependency_missing": "依赖缺失",
        "invalid_output": "工具输出格式错误",
        "permission_denied": "权限不足"
    },
    "planning_error": {
        "bad_plan": "规划不合理",
        "missing_step": "缺少关键步骤",
        "circular_dependency": "循环依赖",
        "invalid_decomposition": "任务拆解错误"
    },
    "execution_error": {
        "code_exception": "代码异常",
        "test_failure": "测试失败",
        "validation_error": "验证失败",
        "runtime_error": "运行时错误"
    },
    "resource_error": {
        "memory_exhausted": "内存耗尽",
        "disk_full": "磁盘空间不足",
        "cpu_overload": "CPU 过载",
        "network_unavailable": "网络不可用"
    },
    "system_error": {
        "queue_overflow": "队列溢出",
        "scheduler_failure": "调度器失败",
        "database_error": "数据库错误",
        "unknown": "未知系统错误"
    }
}

# 旧分类到新分类的映射
LEGACY_MAPPING = {
    "timeout": ("model_error", "timeout"),
    "dependency_error": ("tool_error", "dependency_missing"),
    "logic_error": ("execution_error", "code_exception"),
    "resource_exhausted": ("resource_error", "memory_exhausted")
}


class FailureTaxonomy:
    def __init__(self, data_dir="C:/Users/A/.openclaw/workspace/aios/agent_system"):
        self.data_dir = Path(data_dir)
        self.failures_file = self.data_dir / "failures_classified.jsonl"
        
    def classify_failure(self, task_id, agent, error_type, message, legacy=False):
        """
        分类失败记录
        
        Args:
            task_id: 任务ID
            agent: Agent名称
            error_type: 错误类型（旧格式或新格式）
            message: 错误消息
            legacy: 是否是旧格式（需要映射）
        
        Returns:
            dict: 分类后的失败记录
        """
        if legacy and error_type in LEGACY_MAPPING:
            layer, root_cause = LEGACY_MAPPING[error_type]
        else:
            # 新格式：error_type 应该是 "layer.root_cause"
            if "." in error_type:
                layer, root_cause = error_type.split(".", 1)
            else:
                # 默认归类为 system_error.unknown
                layer, root_cause = "system_error", "unknown"
        
        record = {
            "task_id": task_id,
            "agent": agent,
            "layer": layer,
            "type": root_cause,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # 写入 JSONL
        with open(self.failures_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        return record
    
    def migrate_legacy_lessons(self):
        """
        迁移旧的 lessons.json 到新的分类系统
        """
        lessons_file = self.data_dir / "lessons.json"
        if not lessons_file.exists():
            print("[WARN] lessons.json not found")
            return
        
        with open(lessons_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        migrated = 0
        for lesson in data.get("lessons", []):
            self.classify_failure(
                task_id=lesson.get("id", "unknown"),
                agent=lesson.get("agent", "unknown"),
                error_type=lesson.get("error_type", "unknown"),
                message=lesson.get("context", ""),
                legacy=True
            )
            migrated += 1
        
        print(f"[OK] Migrated {migrated} lessons to new taxonomy")
    
    def get_failure_distribution(self):
        """
        统计失败分布
        
        Returns:
            dict: 按 layer 和 type 统计的失败分布
        """
        if not self.failures_file.exists():
            return {"total": 0, "by_layer": {}, "by_type": {}}
        
        by_layer = {}
        by_type = {}
        total = 0
        
        with open(self.failures_file, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                layer = record.get("layer", "unknown")
                error_type = record.get("type", "unknown")
                
                by_layer[layer] = by_layer.get(layer, 0) + 1
                by_type[error_type] = by_type.get(error_type, 0) + 1
                total += 1
        
        # 计算百分比
        by_layer_pct = {k: f"{v/total*100:.1f}%" for k, v in by_layer.items()}
        by_type_pct = {k: f"{v/total*100:.1f}%" for k, v in by_type.items()}
        
        return {
            "total": total,
            "by_layer": by_layer_pct,
            "by_type": by_type_pct,
            "raw_counts": {
                "by_layer": by_layer,
                "by_type": by_type
            }
        }
    
    def print_distribution(self):
        """
        打印失败分布（人类可读）
        """
        dist = self.get_failure_distribution()
        
        print(f"\n=== Failure Distribution (Total: {dist['total']}) ===\n")
        
        print("By Layer:")
        for layer, pct in sorted(dist['by_layer'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {layer}: {pct}")
        
        print("\nBy Type:")
        for error_type, pct in sorted(dist['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {pct}")


if __name__ == "__main__":
    ft = FailureTaxonomy()
    
    # 迁移旧数据
    print("[MIGRATE] Converting legacy lessons.json...")
    ft.migrate_legacy_lessons()
    
    # 打印分布
    ft.print_distribution()
