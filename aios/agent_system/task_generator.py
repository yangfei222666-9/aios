"""
Task Generator Agent - 自动生成任务

每天自动生成 100 个任务，覆盖：
- Code Tasks (40%)
- Analysis Tasks (30%)
- Tool Tasks (20%)
- Stress Tasks (10%)
"""

import json
import random
from datetime import datetime
from pathlib import Path

class TaskGenerator:
    def __init__(self, data_dir="C:/Users/A/.openclaw/workspace/aios/agent_system"):
        self.data_dir = Path(data_dir)
        self.queue_file = self.data_dir / "task_queue.jsonl"
        
        # 任务模板
        self.templates = {
            "code": [
                "Write a Python function to {action}",
                "Fix the bug in {component}",
                "Refactor {module} to improve readability",
                "Add unit tests for {function}",
                "Optimize {algorithm} for better performance",
                "Implement {feature} with error handling",
                "Create a CLI tool for {task}",
                "Add type hints to {module}",
            ],
            "analysis": [
                "Analyze the dataset in {file}",
                "Summarize the article: {topic}",
                "Compare {algo1} vs {algo2}",
                "Generate a report on {metric}",
                "Find patterns in {data}",
                "Evaluate the performance of {system}",
                "Review the code quality of {repo}",
            ],
            "tool": [
                "Fetch data from {api}",
                "Parse JSON from {source}",
                "Generate a {format} report",
                "Convert {input} to {output}",
                "Validate {data} against {schema}",
                "Export {data} to {destination}",
            ],
            "stress": [
                "Multi-agent collaboration: {scenario}",
                "Long chain reasoning: {problem}",
                "Tool chaining: {workflow}",
                "Complex planning: {goal}",
            ]
        }
        
        # 填充词
        self.fillers = {
            "action": ["calculate fibonacci", "sort a list", "parse CSV", "validate email"],
            "component": ["scheduler", "router", "executor", "validator"],
            "module": ["utils.py", "core.py", "helpers.py", "config.py"],
            "function": ["process_data", "validate_input", "format_output", "handle_error"],
            "algorithm": ["sorting", "searching", "caching", "batching"],
            "feature": ["retry logic", "rate limiting", "logging", "monitoring"],
            "task": ["file backup", "log rotation", "data sync", "health check"],
            "file": ["sales.csv", "logs.json", "metrics.db", "events.jsonl"],
            "topic": ["AI trends", "system design", "performance tuning", "security best practices"],
            "algo1": ["quicksort", "mergesort", "heapsort", "bubblesort"],
            "algo2": ["quicksort", "mergesort", "heapsort", "bubblesort"],
            "metric": ["latency", "throughput", "error rate", "success rate"],
            "data": ["user behavior", "system logs", "API calls", "task executions"],
            "system": ["AIOS", "dispatcher", "scheduler", "monitor"],
            "repo": ["aios/core", "aios/agents", "aios/utils", "aios/tests"],
            "api": ["GitHub API", "Weather API", "News API", "Stock API"],
            "source": ["API response", "config file", "database", "log file"],
            "format": ["PDF", "CSV", "JSON", "HTML"],
            "input": ["CSV", "JSON", "XML", "YAML"],
            "output": ["JSON", "CSV", "Markdown", "HTML"],
            "schema": ["JSON Schema", "OpenAPI", "Protobuf", "Avro"],
            "destination": ["database", "S3", "local file", "API endpoint"],
            "scenario": ["code review + testing", "planning + execution", "monitoring + alerting"],
            "problem": ["optimize database queries", "design distributed system", "debug memory leak"],
            "workflow": ["fetch → parse → validate → store", "read → transform → analyze → report"],
            "goal": ["migrate 1000 users", "process 10GB data", "handle 1M requests"],
        }
    
    def generate_task(self, task_type):
        """
        生成单个任务
        
        Args:
            task_type: code/analysis/tool/stress
        
        Returns:
            dict: 任务描述
        """
        template = random.choice(self.templates[task_type])
        
        # 填充模板
        desc = template
        for key, values in self.fillers.items():
            if f"{{{key}}}" in desc:
                desc = desc.replace(f"{{{key}}}", random.choice(values))
        
        # 映射到 dispatcher
        dispatcher_map = {
            "code": "coder-dispatcher",
            "analysis": "analyst-dispatcher",
            "tool": "coder-dispatcher",
            "stress": "analyst-dispatcher"
        }
        
        priority_map = {
            "code": "normal",
            "analysis": "normal",
            "tool": "low",
            "stress": "high"
        }
        
        task_id = f"gen-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        return {
            "id": task_id,
            "type": task_type,
            "description": desc,
            "dispatcher": dispatcher_map[task_type],
            "priority": priority_map[task_type],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
    
    def generate_batch(self, total=100):
        """
        批量生成任务
        
        Args:
            total: 总任务数（默认 100）
        
        Returns:
            list: 生成的任务列表
        """
        # 按比例分配
        distribution = {
            "code": int(total * 0.4),      # 40%
            "analysis": int(total * 0.3),  # 30%
            "tool": int(total * 0.2),      # 20%
            "stress": int(total * 0.1)     # 10%
        }
        
        tasks = []
        for task_type, count in distribution.items():
            for _ in range(count):
                tasks.append(self.generate_task(task_type))
        
        return tasks
    
    def enqueue_tasks(self, tasks):
        """
        将任务写入队列
        
        Args:
            tasks: 任务列表
        """
        with open(self.queue_file, "a", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
        
        print(f"[OK] Enqueued {len(tasks)} tasks to {self.queue_file}")
    
    def run_daily_generation(self, count=100):
        """
        每日任务生成（主入口）
        
        Args:
            count: 生成任务数（默认 100）
        """
        print(f"[GENERATE] Generating {count} tasks...")
        tasks = self.generate_batch(count)
        
        # 统计
        by_type = {}
        for task in tasks:
            t = task["type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        print(f"[STATS] Task distribution:")
        for t, c in by_type.items():
            print(f"  {t}: {c}")
        
        # 入队
        self.enqueue_tasks(tasks)
        
        return tasks


if __name__ == "__main__":
    gen = TaskGenerator()
    
    # 生成 100 个任务
    gen.run_daily_generation(count=100)
