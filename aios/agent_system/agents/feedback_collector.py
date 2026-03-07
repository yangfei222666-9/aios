"""Feedback Collector Agent - 用户反馈收集"""
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

class FeedbackCollector:
    def __init__(self):
        self.feedback_file = Path("data/feedback/user_feedback.jsonl")
        
    def collect(self, feedback_text, rating=None, category=None):
        """收集单条反馈"""
        feedback = {
            "id": f"fb-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "text": feedback_text,
            "rating": rating,
            "category": category or self._classify(feedback_text),
            "sentiment": self._analyze_sentiment(feedback_text)
        }
        
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback, ensure_ascii=False) + "\n")
        
        print(f"✓ 反馈已收集: {feedback['id']}")
        return feedback
    
    def analyze(self):
        """分析所有反馈"""
        print("=" * 80)
        print("Feedback Collector - 反馈分析")
        print("=" * 80)
        
        if not self.feedback_file.exists():
            print("\n✓ 暂无反馈数据")
            return
        
        feedbacks = []
        with open(self.feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    feedbacks.append(json.loads(line))
        
        print(f"\n📊 总反馈数: {len(feedbacks)}")
        
        # 情感分析
        sentiments = Counter(fb.get("sentiment") for fb in feedbacks)
        print(f"\n😊 情感分布:")
        for sentiment, count in sentiments.most_common():
            print(f"  {sentiment}: {count}")
        
        # 分类统计
        categories = Counter(fb.get("category") for fb in feedbacks)
        print(f"\n📋 分类统计:")
        for cat, count in categories.most_common():
            print(f"  {cat}: {count}")
        
        # 平均评分
        ratings = [fb.get("rating") for fb in feedbacks if fb.get("rating")]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            print(f"\n⭐ 平均评分: {avg_rating:.1f}/5")
        
        print(f"\n{'=' * 80}")
    
    def _classify(self, text):
        keywords = {
            "bug": ["bug", "错误", "问题", "失败", "crash"],
            "feature": ["功能", "需要", "希望", "建议", "feature"],
            "performance": ["慢", "快", "性能", "速度", "slow"],
            "ux": ["界面", "使用", "体验", "ui", "ux"]
        }
        text_lower = text.lower()
        for cat, kws in keywords.items():
            if any(kw in text_lower for kw in kws):
                return cat
        return "general"
    
    def _analyze_sentiment(self, text):
        positive = ["好", "棒", "赞", "喜欢", "great", "good", "nice", "love"]
        negative = ["差", "烂", "坏", "讨厌", "bad", "poor", "hate", "terrible"]
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        if pos > neg:
            return "positive"
        elif neg > pos:
            return "negative"
        return "neutral"

if __name__ == "__main__":
    collector = FeedbackCollector()
    collector.collect("AIOS 运行很稳定，功能很强大！", rating=5)
    collector.collect("任务执行有点慢，希望能优化速度", rating=3)
    collector.analyze()
