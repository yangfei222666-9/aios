"""
Agent Learning Loop: 闭环学习机制
Agent 执行 → 记录结果 → 反馈到 AIOS → 更新知识库 → 下次执行时应用
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "agent_system" / "data" / "learning"
LEARNING_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_BASE = LEARNING_DIR / "knowledge_base.jsonl"
FEEDBACK_LOG = LEARNING_DIR / "feedback_log.jsonl"


class AgentLearningLoop:
    """Agent 闭环学习"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def record_execution(
        self, task: str, result: Dict, success: bool, error: str = None
    ):
        """
        记录 Agent 执行结果
        """
        execution_record = {
            "ts": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "task": task,
            "success": success,
            "error": error,
            "result": result,
            "duration_sec": result.get("duration_sec", 0),
        }

        # 写入反馈日志
        with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(execution_record, ensure_ascii=False) + "\n")

        # 如果失败，提取教训
        if not success and error:
            self._extract_lesson(task, error)

    def _extract_lesson(self, task: str, error: str):
        """从失败中提取教训"""
        lesson = {
            "ts": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "task_type": self._classify_task(task),
            "error_type": self._classify_error(error),
            "error": error,
            "lesson": self._generate_lesson(error),
            "confidence": 0.7,  # 初始置信度
        }

        # 写入知识库
        with open(KNOWLEDGE_BASE, "a", encoding="utf-8") as f:
            f.write(json.dumps(lesson, ensure_ascii=False) + "\n")

    def _classify_task(self, task: str) -> str:
        """分类任务类型"""
        task_lower = task.lower()
        if "code" in task_lower or "代码" in task:
            return "coding"
        elif "test" in task_lower or "测试" in task:
            return "testing"
        elif "analyze" in task_lower or "分析" in task:
            return "analysis"
        elif "research" in task_lower or "研究" in task:
            return "research"
        else:
            return "general"

    def _classify_error(self, error: str) -> str:
        """分类错误类型"""
        error_lower = error.lower()
        if "502" in error or "network" in error_lower:
            return "network"
        elif "429" in error or "rate limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower:
            return "timeout"
        elif "syntax" in error_lower or "语法" in error:
            return "syntax"
        else:
            return "unknown"

    def _generate_lesson(self, error: str) -> str:
        """生成教训"""
        error_type = self._classify_error(error)

        lessons = {
            "network": "网络请求失败时应该增加重试机制（至少3次），并使用指数退避策略",
            "rate_limit": "遇到限流时应该降低请求频率，在请求之间增加延迟（至少1秒）",
            "timeout": "超时错误说明任务执行时间过长，应该优化逻辑或增加超时时间",
            "syntax": "语法错误说明代码生成有问题，应该更仔细地检查语法规则",
            "unknown": "未知错误，需要更详细的错误信息才能分析",
        }

        return lessons.get(error_type, lessons["unknown"])

    def get_relevant_lessons(self, task: str) -> List[Dict]:
        """
        获取与当前任务相关的历史教训
        """
        if not KNOWLEDGE_BASE.exists():
            return []

        task_type = self._classify_task(task)
        lessons = []

        with open(KNOWLEDGE_BASE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    lesson = json.loads(line)
                    # 匹配任务类型或通用教训
                    if (
                        lesson.get("task_type") == task_type
                        or lesson.get("task_type") == "general"
                    ):
                        if (
                            lesson.get("confidence", 0) >= 0.5
                        ):  # 只返回置信度 >= 0.5 的教训
                            lessons.append(lesson)
                except:
                    continue

        # 按时间倒序，返回最近的 5 条
        lessons.sort(key=lambda x: x.get("ts", ""), reverse=True)
        return lessons[:5]

    def inject_lessons_to_prompt(self, base_prompt: str, task: str) -> str:
        """将历史教训注入到 Agent 的 system prompt"""
        lessons = self.get_relevant_lessons(task)

        if not lessons:
            return base_prompt

        lesson_section = "\n\n## [DOCS] 历史教训（避免重复错误）\n\n"
        for i, lesson in enumerate(lessons, 1):
            lesson_section += f"{i}. **{lesson['error_type']}**: {lesson['lesson']}\n"

        lesson_section += "\n请在执行任务时参考以上教训，避免重复犯错。\n"

        return base_prompt + lesson_section

    def update_lesson_confidence(self, lesson_id: str, success: bool):
        """
        根据执行结果更新教训的置信度
        成功 → 置信度 +0.1，失败 → 置信度 -0.1
        """
        # TODO: 实现置信度更新逻辑
        pass


# ── CLI ──

if __name__ == "__main__":
    print("=" * 50)
    print("Agent Learning Loop 演示")
    print("=" * 50)

    loop = AgentLearningLoop("test-agent")

    # 模拟失败执行
    print("\n[TEST] 模拟失败执行...")
    loop.record_execution(
        task="编写一个 Python 脚本",
        result={"duration_sec": 10},
        success=False,
        error="Network error: 502 Bad Gateway",
    )

    loop.record_execution(
        task="测试代码功能",
        result={"duration_sec": 5},
        success=False,
        error="API rate limit exceeded: 429",
    )

    print("[OK] 失败记录已保存")

    # 获取相关教训
    print("\n[DOCS] 获取相关教训...")
    lessons = loop.get_relevant_lessons("编写一个新的 Python 脚本")

    if lessons:
        print(f"找到 {len(lessons)} 条相关教训：")
        for i, lesson in enumerate(lessons, 1):
            print(f"\n{i}. 错误类型: {lesson['error_type']}")
            print(f"   教训: {lesson['lesson']}")
            print(f"   置信度: {lesson['confidence']}")
    else:
        print("暂无相关教训")

    # 演示注入到 prompt
    print("\n[NOTE] 注入到 prompt 演示...")
    base_prompt = "你是一个代码开发专员，负责编写高质量的代码。"
    enhanced_prompt = loop.inject_lessons_to_prompt(base_prompt, "编写 Python 脚本")
    print(enhanced_prompt)
