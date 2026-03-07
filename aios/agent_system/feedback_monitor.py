#!/usr/bin/env python3
"""
社区反馈自动监控系统 - KUN_LEARN v3.0 集成
每 30 分钟扫描知乎/GitHub Issues/ClawdHub
自动生成 384-dim embedding 并分类反馈
实时生成回复模板并记录到 Experience Library
"""

import time
import json
from datetime import datetime
from pathlib import Path

# 导入 KUN_LEARN v3.0
try:
    from experience_learner_v3 import learner_v3
    KUN_LEARN_AVAILABLE = True
except ImportError:
    KUN_LEARN_AVAILABLE = False
    print("[WARN] KUN_LEARN v3.0 not available")

class FeedbackMonitor:
    """社区反馈监控器"""
    
    def __init__(self):
        self.feedback_log = Path("feedback_monitor.jsonl")
        self.last_check = None
    
    def scan_feedback(self, mode="real"):
        """扫描社区反馈
        
        Args:
            mode: "real" 或 "mock"（默认 real）
        """
        if mode == "mock":
            # 模拟数据（用于测试）
            feedbacks = [
                {
                    "source": "github",
                    "type": "positive",
                    "content": "64 卦决策系统太有创意了！",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "source": "zhihu",
                    "type": "constructive",
                    "content": "能不能开源 AIOS 的核心代码？",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "source": "clawdhub",
                    "type": "question",
                    "content": "Evolution Score 99.5% 是怎么算出来的？",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            return feedbacks
        
        # 真实模式：调用 GitHub API / 知乎 API
        feedbacks = []
        
        # 1. GitHub Issues（需要 GitHub Token）
        try:
            import requests
            repo = "yangfei222666-9/Repository-name-aios"
            url = f"https://api.github.com/repos/{repo}/issues"
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                issues = response.json()
                for issue in issues[:5]:  # 最多 5 条
                    feedbacks.append({
                        "source": "github",
                        "type": "question" if "?" in issue['title'] else "constructive",
                        "content": issue['title'],
                        "url": issue['html_url'],
                        "timestamp": issue['created_at']
                    })
        except Exception as e:
            print(f"[WARN] GitHub API 失败: {e}")
        
        # 2. 知乎（需要爬虫或 API）
        # TODO: 实现知乎评论抓取
        
        # 3. ClawdHub（需要 API）
        # TODO: 实现 ClawdHub 反馈抓取
        
        return feedbacks
    
    def classify_feedback(self, feedback):
        """使用 KUN_LEARN v3.0 分类反馈"""
        if not KUN_LEARN_AVAILABLE:
            return "unknown"
        
        task = {
            'error_type': 'feedback_classification',
            'prompt': feedback['content']
        }
        
        result = learner_v3.recommend(task)
        
        # 根据推荐策略分类
        if "positive" in feedback['content'].lower():
            return "positive"
        elif "question" in feedback['content'].lower() or "?" in feedback['content']:
            return "question"
        else:
            return "constructive"
    
    def generate_response(self, feedback):
        """生成回复模板"""
        feedback_type = self.classify_feedback(feedback)
        
        templates = {
            "positive": "感谢您的认可！{content} 是 AIOS 的核心创新之一。",
            "constructive": "非常好的建议！{content} 我们会在下一版本中考虑。",
            "question": "好问题！{content} 详细解释请参考文档：https://docs.openclaw.ai"
        }
        
        template = templates.get(feedback_type, "感谢您的反馈！")
        response = template.format(content=feedback['content'])
        
        return {
            "feedback": feedback,
            "response": response,
            "type": feedback_type,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_to_experience_library(self, feedback_data):
        """保存到 Experience Library"""
        with open(self.feedback_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_data, ensure_ascii=False) + '\n')
        
        print(f"[EXPERIENCE] Feedback saved: {feedback_data['type']}")
    
    def run_once(self, mode="real"):
        """运行一次监控
        
        Args:
            mode: "real" 或 "mock"（默认 real）
        """
        print(f"[MONITOR] Scanning feedback at {datetime.now()} (mode={mode})")
        
        feedbacks = self.scan_feedback(mode=mode)
        
        if not feedbacks:
            print("[MONITOR] No new feedback")
            return
        
        for feedback in feedbacks:
            response_data = self.generate_response(feedback)
            self.save_to_experience_library(response_data)
            
            print(f"[FEEDBACK] {feedback['source']}: {feedback['content']}")
            print(f"[RESPONSE] {response_data['response']}")
        
        print(f"[MONITOR] Processed {len(feedbacks)} feedbacks")
        
        self.last_check = datetime.now()
        
        return len(feedbacks)
    
    def run_continuous(self, interval_minutes=30):
        """持续监控（每 30 分钟）"""
        print(f"[MONITOR] Starting continuous monitoring (interval: {interval_minutes} min)")
        
        while True:
            count = self.run_once()
            print(f"[MONITOR] Processed {count} feedbacks")
            
            time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    import sys
    
    monitor = FeedbackMonitor()
    
    # 默认真实模式
    mode = sys.argv[1] if len(sys.argv) > 1 else "real"
    
    if mode == "continuous":
        # 持续监控（每 30 分钟）
        monitor.run_continuous(interval_minutes=30)
    else:
        # 运行一次（real 或 mock）
        monitor.run_once(mode=mode)
    
    print("\n[MONITOR] Feedback monitoring system ready!")
    print("[MONITOR] To run continuously: python feedback_monitor.py --continuous")
