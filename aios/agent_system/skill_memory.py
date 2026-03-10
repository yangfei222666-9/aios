"""
Skill Memory - 让技能成为有记忆、可演化的知识单元

核心功能：
1. 自动记录每次 Skill 执行
2. 聚合统计（成功率、使用频率、平均耗时）
3. 成功模式识别
4. 失败教训积累
5. 技能演化追踪

灵感来源：MemOS Skill Memory for cross-task skill reuse and evolution
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

# 路径配置
from paths import DATA_DIR

SKILL_MEMORY_FILE = DATA_DIR / "skill_memory.jsonl"
SKILL_EXECUTIONS_FILE = DATA_DIR / "skill_executions.jsonl"


class SkillMemory:
    """技能记忆管理器"""
    
    def __init__(self):
        self.memory_file = SKILL_MEMORY_FILE
        self.executions_file = SKILL_EXECUTIONS_FILE
        self._ensure_files()
    
    @staticmethod
    def normalize_skill_id(raw_name: str) -> str:
        """
        Skill 名称规范化（硬规则）
        
        规则：
        1. 全部小写
        2. 空格/下划线 → 连字符
        3. 去掉多余连字符
        4. 去掉前后连字符
        
        示例：
          "PDF Skill"   → "pdf-skill"
          "pdf_skill"   → "pdf-skill"
          "PDF-Skill"   → "pdf-skill"
          "pdf"         → "pdf"
          " Git  Skill" → "git-skill"
        """
        s = raw_name.strip().lower()
        s = re.sub(r'[\s_]+', '-', s)   # 空格/下划线 → 连字符
        s = re.sub(r'-+', '-', s)        # 多个连字符 → 一个
        s = s.strip('-')                 # 去掉首尾连字符
        return s
    
    def _ensure_files(self):
        """确保数据文件存在"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_file.exists():
            self.memory_file.write_text("", encoding="utf-8")
        if not self.executions_file.exists():
            self.executions_file.write_text("", encoding="utf-8")
    
    def track_execution(
        self,
        skill_id: str,
        skill_name: str,
        task_id: str,
        command: str,
        status: str,
        duration_ms: int,
        skill_version: str = "1.0.0",
        input_params: Optional[Dict] = None,
        output_summary: Optional[str] = None,
        error: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        记录一次 Skill 执行
        
        Args:
            skill_id: 技能 ID（自动规范化，如 "PDF Skill" → "pdf-skill"）
            skill_name: 技能显示名称
            task_id: 任务 ID
            command: 执行的命令
            status: 执行状态（success/failed）
            duration_ms: 执行耗时（毫秒）
            skill_version: 技能版本号（默认 "1.0.0"）
            input_params: 输入参数
            output_summary: 输出摘要
            error: 错误信息（如果失败）
            context: 上下文信息（agent、user_intent 等）
        
        Returns:
            execution_id: 执行记录 ID
        """
        # 硬规则：强制规范化 skill_id
        skill_id = self.normalize_skill_id(skill_id)
        
        now = datetime.now()
        execution_id = f"exec-{now.strftime('%Y%m%d-%H%M%S')}-{task_id[-3:]}"
        
        execution_record = {
            "execution_id": execution_id,
            "skill_id": skill_id,
            "skill_name": skill_name,
            "skill_version": skill_version,
            "task_id": task_id,
            "command": command,
            "started_at": now.isoformat(),
            "duration_ms": duration_ms,
            "status": status,
            "input_params": input_params or {},
            "output_summary": output_summary or "",
            "error": error,
            "context": context or {}
        }
        
        # 追加到执行记录文件
        with open(self.executions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(execution_record, ensure_ascii=False) + "\n")
        
        return execution_id
    
    def update_skill_stats(self, skill_id: str) -> Dict:
        """
        更新指定 Skill 的统计信息
        
        Args:
            skill_id: 技能 ID（自动规范化）
        
        Returns:
            更新后的技能记忆条目
        """
        # 硬规则：强制规范化
        skill_id = self.normalize_skill_id(skill_id)
        
        # 读取所有执行记录
        executions = self._load_executions(skill_id)
        
        if not executions:
            return {}
        
        # 计算统计
        total = len(executions)
        success = sum(1 for e in executions if e["status"] == "success")
        failed = total - success
        success_rate = success / total if total > 0 else 0.0
        
        avg_duration = sum(e["duration_ms"] for e in executions) / total
        
        last_execution = max(executions, key=lambda e: e["started_at"])
        
        # 版本追踪：取最新执行记录的版本，收集所有历史版本
        latest_version = last_execution.get("skill_version", "1.0.0")
        seen_versions = sorted(set(
            e.get("skill_version", "1.0.0") for e in executions
        ))
        
        # 识别常见模式（基于 command）
        command_stats = defaultdict(lambda: {"count": 0, "success": 0})
        for e in executions:
            cmd = e["command"].split()[0] if e["command"] else "unknown"
            command_stats[cmd]["count"] += 1
            if e["status"] == "success":
                command_stats[cmd]["success"] += 1
        
        common_patterns = [
            {
                "pattern": cmd,
                "usage_count": stats["count"],
                "success_rate": stats["success"] / stats["count"] if stats["count"] > 0 else 0.0
            }
            for cmd, stats in sorted(command_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        ]
        
        # 提取失败教训
        failure_lessons = self._extract_failure_lessons(executions)
        
        # 计算演化分数（基于成功率、使用频率）
        evolution_score = self._calculate_evolution_score(success_rate, total)
        
        # 构建技能记忆条目
        skill_memory_entry = {
            "skill_id": skill_id,
            "skill_name": last_execution.get("skill_name", skill_id),
            "skill_version": latest_version,
            "version_history": seen_versions,
            "last_used": last_execution["started_at"],
            "usage_count": total,
            "success_count": success,
            "failure_count": failed,
            "success_rate": round(success_rate, 3),
            "avg_execution_time_ms": round(avg_duration, 1),
            "evolution_score": round(evolution_score, 1),
            "common_patterns": common_patterns,
            "failure_lessons": failure_lessons,
            "updated_at": datetime.now().isoformat()
        }
        
        # 更新到 skill_memory.jsonl
        self._update_memory_file(skill_id, skill_memory_entry)
        
        return skill_memory_entry
    
    def _load_executions(self, skill_id: str) -> List[Dict]:
        """加载指定 Skill 的所有执行记录（skill_id 已规范化）"""
        if not self.executions_file.exists():
            return []
        
        executions = []
        with open(self.executions_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    # 对比时也规范化存储的 skill_id（兼容旧数据）
                    if self.normalize_skill_id(record.get("skill_id", "")) == skill_id:
                        executions.append(record)
        
        return executions
    
    def _extract_failure_lessons(self, executions: List[Dict]) -> List[Dict]:
        """从执行记录中提取失败教训"""
        error_stats = defaultdict(lambda: {"count": 0, "last_seen": None})
        
        for e in executions:
            if e["status"] == "failed" and e.get("error"):
                error_type = self._classify_error(e["error"])
                error_stats[error_type]["count"] += 1
                error_stats[error_type]["last_seen"] = e["started_at"]
        
        lessons = [
            {
                "error_type": error_type,
                "count": stats["count"],
                "last_seen": stats["last_seen"],
                "recovery_strategy": self._suggest_recovery(error_type)
            }
            for error_type, stats in sorted(error_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        ]
        
        return lessons
    
    def _classify_error(self, error_msg: str) -> str:
        """分类错误类型"""
        error_lower = error_msg.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "encoding" in error_lower or "decode" in error_lower:
            return "encoding_error"
        elif "not found" in error_lower or "no such file" in error_lower:
            return "file_not_found"
        elif "permission" in error_lower:
            return "permission_denied"
        elif any(kw in error_lower for kw in [
            "memory", "out of memory", "oom",
            "resource", "resources exhausted", "insufficient resources",
            "quota exceeded", "disk space", "cpu"
        ]):
            return "resource_exhausted"
        elif any(kw in error_lower for kw in [
            "network", "connection", "dns", "unreachable",
            "502", "503", "504", "gateway"
        ]):
            return "network_error"
        elif any(kw in error_lower for kw in [
            "dependency", "module not found", "import error",
            "package", "version conflict"
        ]):
            return "dependency_error"
        else:
            return "unknown"
    
    def _suggest_recovery(self, error_type: str) -> str:
        """根据错误类型建议恢复策略"""
        strategies = {
            "timeout": "increase_timeout_and_retry",
            "encoding_error": "try_multiple_encodings",
            "file_not_found": "check_file_path_and_retry",
            "permission_denied": "check_permissions_and_retry",
            "resource_exhausted": "reduce_batch_size_and_retry",
            "network_error": "switch_to_backup_endpoint",
            "dependency_error": "check_dependencies_and_reinstall",
            "unknown": "default_recovery"
        }
        return strategies.get(error_type, "default_recovery")
    
    def _calculate_evolution_score(self, success_rate: float, usage_count: int) -> float:
        """
        计算技能演化分数（0-100）
        
        公式：evolution_score = success_rate * 70 + min(usage_count / 10, 1.0) * 30
        
        - 成功率占 70%
        - 使用频率占 30%（使用 100 次以上视为成熟）
        """
        success_component = success_rate * 70
        usage_component = min(usage_count / 100, 1.0) * 30
        return success_component + usage_component
    
    def _update_memory_file(self, skill_id: str, new_memory: Dict):
        """更新 skill_memory.jsonl 中的指定条目"""
        # 读取所有现有记录
        existing_memories = []
        if self.memory_file.exists():
            with open(self.memory_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        memory = json.loads(line)
                        if memory.get("skill_id") != skill_id:
                            existing_memories.append(memory)
        
        # 追加新记录
        existing_memories.append(new_memory)
        
        # 重写文件
        with open(self.memory_file, "w", encoding="utf-8") as f:
            for memory in existing_memories:
                f.write(json.dumps(memory, ensure_ascii=False) + "\n")
    
    def get_skill_memory(self, skill_id: str) -> Optional[Dict]:
        """获取指定 Skill 的记忆条目"""
        skill_id = self.normalize_skill_id(skill_id)
        if not self.memory_file.exists():
            return None
        
        with open(self.memory_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    memory = json.loads(line)
                    if self.normalize_skill_id(memory.get("skill_id", "")) == skill_id:
                        return memory
        
        return None
    
    def get_all_skills(self) -> List[Dict]:
        """获取所有技能的记忆条目"""
        if not self.memory_file.exists():
            return []
        
        skills = []
        with open(self.memory_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    skills.append(json.loads(line))
        
        return skills


# 全局实例
skill_memory = SkillMemory()


if __name__ == "__main__":
    # 测试
    print("Skill Memory 测试")
    print("=" * 60)
    
    # 模拟记录一次执行
    exec_id = skill_memory.track_execution(
        skill_id="pdf-skill",
        skill_name="PDF 处理工具",
        task_id="task-20260307-001",
        command="python pdf_cli.py extract input.pdf",
        status="success",
        duration_ms=1200,
        input_params={"file": "input.pdf", "action": "extract"},
        output_summary="Extracted 15 pages, 8500 words",
        context={"agent": "document-agent", "user_intent": "提取 PDF 文本"}
    )
    print(f"✓ 记录执行: {exec_id}")
    
    # 更新统计
    memory = skill_memory.update_skill_stats("pdf-skill")
    print(f"✓ 更新统计: {memory['skill_id']}")
    print(f"  使用次数: {memory['usage_count']}")
    print(f"  成功率: {memory['success_rate']:.1%}")
    print(f"  演化分数: {memory['evolution_score']:.1f}/100")
    
    # 获取记忆
    retrieved = skill_memory.get_skill_memory("pdf-skill")
    print(f"✓ 获取记忆: {retrieved['skill_id']}")
    
    print("\n测试完成！")
