"""User Intent Classifier - 用户意图识别和任务路由"""
import json
import re
from datetime import datetime
from pathlib import Path

class UserIntentClassifier:
    def __init__(self):
        self.patterns = {
            "code": [
                r"写.*代码", r"实现.*功能", r"创建.*脚本", r"生成.*程序",
                r"write.*code", r"implement", r"create.*script", r"generate.*program",
                r"重构", r"refactor", r"优化.*代码", r"optimize.*code",
                r"修复.*bug", r"fix.*bug", r"调试", r"debug"
            ],
            "analysis": [
                r"分析", r"analyze", r"统计", r"statistics",
                r"报告", r"report", r"总结", r"summary",
                r"评估", r"evaluate", r"审查", r"review",
                r"对比", r"compare", r"检查", r"check"
            ],
            "monitor": [
                r"监控", r"monitor", r"检测", r"detect",
                r"观察", r"observe", r"追踪", r"track",
                r"健康", r"health", r"状态", r"status",
                r"性能", r"performance", r"资源", r"resource"
            ],
            "test": [
                r"测试", r"test", r"验证", r"verify",
                r"单元测试", r"unit.*test", r"集成测试", r"integration.*test",
                r"压力测试", r"stress.*test", r"性能测试", r"performance.*test"
            ],
            "document": [
                r"文档", r"document", r"说明", r"instruction",
                r"教程", r"tutorial", r"指南", r"guide",
                r"注释", r"comment", r"README"
            ],
            "deploy": [
                r"部署", r"deploy", r"发布", r"release",
                r"上线", r"launch", r"打包", r"package",
                r"构建", r"build", r"编译", r"compile"
            ]
        }
        
        self.priority_keywords = {
            "urgent": [r"紧急", r"urgent", r"立即", r"immediately", r"马上", r"asap"],
            "high": [r"重要", r"important", r"优先", r"priority", r"尽快", r"soon"],
            "low": [r"不急", r"not.*urgent", r"有空", r"when.*free", r"慢慢", r"slowly"]
        }
    
    def classify(self, text):
        """分类用户意图"""
        print("=" * 80)
        print("User Intent Classifier - 意图识别")
        print("=" * 80)
        
        print(f"\n📝 输入文本: {text}\n")
        
        # 1. 识别任务类型
        task_type = self._classify_task_type(text)
        print(f"🎯 任务类型: {task_type}")
        
        # 2. 识别优先级
        priority = self._classify_priority(text)
        print(f"⚡ 优先级: {priority}")
        
        # 3. 提取关键信息
        keywords = self._extract_keywords(text)
        print(f"🔑 关键词: {', '.join(keywords)}")
        
        # 4. 路由到 Agent
        agent = self._route_to_agent(task_type)
        print(f"🤖 路由到: {agent}")
        
        # 5. 生成任务描述
        task = {
            "id": f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": task_type,
            "priority": priority,
            "description": text,
            "keywords": keywords,
            "agent": agent,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # 6. 保存到队列
        self._save_to_queue(task)
        
        print(f"\n✓ 任务已创建: {task['id']}")
        print(f"\n{'=' * 80}")
        
        return task
    
    def _classify_task_type(self, text):
        """分类任务类型"""
        text_lower = text.lower()
        scores = {}
        
        for task_type, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            scores[task_type] = score
        
        # 返回得分最高的类型
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # 默认为 code
        return "code"
    
    def _classify_priority(self, text):
        """分类优先级"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if re.search(keyword, text_lower):
                    return priority
        
        # 默认为 normal
        return "normal"
    
    def _extract_keywords(self, text):
        """提取关键词"""
        # 简单实现：提取长度 > 2 的中文词和英文单词
        chinese = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        english = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        keywords = list(set(chinese + english))
        return keywords[:10]  # 最多 10 个
    
    def _route_to_agent(self, task_type):
        """路由到对应 Agent"""
        routing = {
            "code": "coder-dispatcher",
            "analysis": "analyst-dispatcher",
            "monitor": "monitor-dispatcher",
            "test": "coder-dispatcher",
            "document": "analyst-dispatcher",
            "deploy": "coder-dispatcher"
        }
        return routing.get(task_type, "coder-dispatcher")
    
    def _save_to_queue(self, task):
        """保存到任务队列"""
        queue_file = Path("task_queue.jsonl")
        
        with open(queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    import sys
    
    classifier = UserIntentClassifier()
    
    if len(sys.argv) > 1:
        # 从命令行参数读取
        text = " ".join(sys.argv[1:])
    else:
        # 交互式输入
        text = input("请输入任务描述: ")
    
    classifier.classify(text)
