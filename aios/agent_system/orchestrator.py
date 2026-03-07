#!/usr/bin/env python3
"""
AIOS Orchestrator Agent v2.0 - 智能任务编排
支持多轮对话、任务拆解、上下文记忆
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from paths import TASK_QUEUE as _TASK_QUEUE

# 文件路径
TASK_QUEUE = _TASK_QUEUE
CONTEXT_FILE = Path(__file__).parent / "orchestrator_context.json"

# 任务类型关键词映射
TASK_TYPE_KEYWORDS = {
    "code": [
        "写代码", "编写", "开发", "实现", "重构", "优化", "修复", "debug",
        "写一个", "帮我写", "生成代码", "代码", "函数", "类", "模块",
        "bug", "错误", "修改", "改进", "代码审查", "爬虫", "API", "后端", "前端"
    ],
    "analysis": [
        "分析", "统计", "报告", "总结", "梳理", "整理", "归纳",
        "数据分析", "趋势", "模式", "根因", "原因", "为什么",
        "对比", "比较", "评估", "调研"
    ],
    "monitor": [
        "监控", "检查", "查看", "状态", "健康", "资源", "性能",
        "CPU", "内存", "磁盘", "网络", "告警", "巡检",
        "清理", "释放", "优化资源", "部署", "上线"
    ],
    "research": [
        "研究", "调研", "搜索", "查找", "了解", "学习", "探索",
        "资料", "文档", "论文", "技术", "方案", "最佳实践",
        "GitHub", "开源", "项目"
    ],
    "design": [
        "设计", "架构", "规划", "方案", "蓝图", "技术选型",
        "系统设计", "数据库设计", "API设计", "重构方案", "数据库结构"
    ]
}

# 优先级关键词
PRIORITY_KEYWORDS = {
    "high": ["紧急", "重要", "优先", "立即", "马上", "尽快", "高优先级"],
    "low": ["不急", "有空", "低优先级", "可以慢慢来", "不重要"]
}

# 复杂任务关键词（需要拆解）
COMPLEX_TASK_KEYWORDS = [
    "搭建", "构建", "开发一个", "做一个", "实现一个完整的",
    "系统", "平台", "应用", "项目", "网站", "博客"
]

class OrchestratorContext:
    """上下文管理器"""
    
    def __init__(self):
        self.context = self.load_context()
    
    def load_context(self) -> dict:
        """加载上下文"""
        if CONTEXT_FILE.exists():
            with open(CONTEXT_FILE, encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_task": None,
            "last_instruction": None,
            "conversation_history": []
        }
    
    def save_context(self):
        """保存上下文"""
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.context, f, indent=2, ensure_ascii=False)
    
    def update(self, instruction: str, task: dict):
        """更新上下文"""
        self.context["last_task"] = task
        self.context["last_instruction"] = instruction
        self.context["conversation_history"].append({
            "instruction": instruction,
            "task": task,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近10条对话
        if len(self.context["conversation_history"]) > 10:
            self.context["conversation_history"] = self.context["conversation_history"][-10:]
        
        self.save_context()
    
    def get_last_task(self) -> Optional[dict]:
        """获取上一个任务"""
        return self.context.get("last_task")
    
    def is_continuation(self, instruction: str) -> bool:
        """判断是否是延续上一个任务"""
        continuation_keywords = [
            "加上", "添加", "再", "还要", "另外", "同时", "并且",
            "修改", "改成", "换成", "优化", "完善"
        ]
        return any(kw in instruction for kw in continuation_keywords)

def detect_task_type(text: str) -> str:
    """检测任务类型"""
    text_lower = text.lower()
    
    scores = {}
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[task_type] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    return "code"

def detect_priority(text: str) -> str:
    """检测优先级"""
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in PRIORITY_KEYWORDS["high"]):
        return "high"
    
    if any(kw in text_lower for kw in PRIORITY_KEYWORDS["low"]):
        return "low"
    
    return "normal"

def is_complex_task(text: str) -> bool:
    """判断是否是复杂任务（需要拆解）"""
    return any(kw in text for kw in COMPLEX_TASK_KEYWORDS)

def decompose_task(instruction: str) -> List[dict]:
    """拆解复杂任务"""
    print(f"[SEARCH] 检测到复杂任务，正在拆解...")
    
    # 简单的拆解规则（可以用 LLM 做更智能的拆解）
    subtasks = []
    
    if "博客" in instruction or "网站" in instruction:
        subtasks = [
            {"type": "design", "description": "设计数据库结构（用户、文章、评论表）", "priority": "high"},
            {"type": "code", "description": "实现后端 API（用户认证、文章 CRUD、评论）", "priority": "high"},
            {"type": "code", "description": "实现前端界面（首页、文章详情、编辑器）", "priority": "normal"},
            {"type": "monitor", "description": "部署上线并配置监控", "priority": "normal"}
        ]
    elif "爬虫" in instruction:
        subtasks = [
            {"type": "design", "description": "设计爬虫架构（目标网站、数据结构、存储方案）", "priority": "high"},
            {"type": "code", "description": "实现爬虫核心逻辑（请求、解析、存储）", "priority": "high"},
            {"type": "code", "description": "添加错误处理和重试机制", "priority": "normal"},
            {"type": "monitor", "description": "添加监控和日志", "priority": "low"}
        ]
    else:
        # 默认拆解
        subtasks = [
            {"type": "design", "description": f"设计方案：{instruction}", "priority": "high"},
            {"type": "code", "description": f"实现核心功能：{instruction}", "priority": "high"},
            {"type": "monitor", "description": f"测试和部署：{instruction}", "priority": "normal"}
        ]
    
    # 添加时间戳和来源
    for task in subtasks:
        task["created_at"] = datetime.now().isoformat()
        task["source"] = "orchestrator_decompose"
    
    return subtasks

def create_task(instruction: str, context: OrchestratorContext) -> List[dict]:
    """根据自然语言指令创建任务（支持多轮对话和任务拆解）"""
    
    # 检查是否是延续上一个任务
    if context.is_continuation(instruction):
        last_task = context.get_last_task()
        if last_task:
            print(f"[IDEA] 检测到延续任务，基于上一个任务：{last_task['description']}")
            # 合并描述
            description = f"{last_task['description']} + {instruction}"
            task = {
                "type": last_task["type"],
                "description": description,
                "priority": detect_priority(instruction) or last_task["priority"],
                "created_at": datetime.now().isoformat(),
                "source": "orchestrator_continuation"
            }
            return [task]
    
    # 检查是否是复杂任务（需要拆解）
    if is_complex_task(instruction):
        return decompose_task(instruction)
    
    # 普通任务
    task_type = detect_task_type(instruction)
    priority = detect_priority(instruction)
    
    task = {
        "type": task_type,
        "description": instruction,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "source": "orchestrator"
    }
    
    return [task]

def append_task(task: dict):
    """追加任务到队列"""
    with open(TASK_QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")

def orchestrate(instruction: str) -> List[dict]:
    """编排任务（主函数）"""
    print(f"📥 收到指令: {instruction}")
    
    # 加载上下文
    context = OrchestratorContext()
    
    # 创建任务（可能返回多个子任务）
    tasks = create_task(instruction, context)
    
    if len(tasks) > 1:
        print(f"[PACKAGE] 拆解为 {len(tasks)} 个子任务：")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. [{task['type']}] {task['description']} (优先级: {task['priority']})")
    else:
        task = tasks[0]
        print(f"[TARGET] 任务类型: {task['type']}")
        print(f"[NOTE] 任务描述: {task['description']}")
        print(f"[ZAP] 优先级: {task['priority']}")
    
    # 写入队列
    for task in tasks:
        append_task(task)
    
    print(f"[OK] {len(tasks)} 个任务已加入队列")
    
    # 更新上下文
    context.update(instruction, tasks[0] if len(tasks) == 1 else {"type": "complex", "subtasks": tasks})
    
    return tasks

def main():
    """命令行接口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python orchestrator.py '你的指令'")
        print("\n示例:")
        print("  python orchestrator.py '帮我写一个爬虫'")
        print("  python orchestrator.py '加上错误重试机制'")
        print("  python orchestrator.py '帮我搭建一个博客系统'")
        sys.exit(1)
    
    instruction = " ".join(sys.argv[1:])
    orchestrate(instruction)

if __name__ == "__main__":
    main()
