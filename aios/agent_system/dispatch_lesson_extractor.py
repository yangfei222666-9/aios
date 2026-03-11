#!/usr/bin/env python3
"""
Dispatch Lesson Extractor - 从中枢决策模式提取经验

从 dispatch patterns + health diagnosis 中提取结构化 lesson，
把"中枢怎么反复降级和 fallback"沉淀成可复用的系统经验。

Version: 1.0.0
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class DispatchLessonType(Enum):
    """中枢决策 Lesson 类型"""
    POLICY_OVER_CONSERVATIVE = "policy_over_conservative"
    FALLBACK_SINGLE_PATH = "fallback_single_path"
    HANDLER_DISTRIBUTION_TOO_NARROW = "handler_distribution_too_narrow"
    HANDLER_REJECTION_BIAS = "handler_rejection_bias"


class DispatchLessonExtractor:
    """中枢决策经验提取器"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "data"
        
        # 输入文件
        self.dispatch_log = self.data_dir / "dispatch_log.jsonl"
        self.pattern_report = self.data_dir / "dispatch_pattern_report.json"
        self.health_diagnosis = self.data_dir / "health_diagnosis.json"
        self.existing_lessons = self.data_dir / "lessons.json"
        
        # 输出文件
        self.new_lessons_file = self.data_dir / "new_dispatch_lessons.json"
        self.summary_file = self.data_dir / "dispatch_lessons_summary.md"
        
        # 已有 lesson（用于去重）
        self.existing_lesson_ids = set()
        self.existing_lesson_patterns = set()
    
    def load_existing_lessons(self):
        """加载已有 lesson（避免重复）"""
        if not self.existing_lessons.exists():
            return
        
        try:
            with open(self.existing_lessons, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 支持两种格式：列表或字典
                if isinstance(data, list):
                    lessons = data
                elif isinstance(data, dict):
                    lessons = data.get('lessons', [])
                else:
                    lessons = []
                
                for lesson in lessons:
                    if isinstance(lesson, dict):
                        self.existing_lesson_ids.add(lesson.get('lesson_id', ''))
                        self.existing_lesson_patterns.add(lesson.get('trigger_pattern', ''))
        except Exception as e:
            print(f"⚠️  加载已有 lesson 失败: {e}")
    
    def load_pattern_report(self) -> Optional[Dict[str, Any]]:
        """加载模式分析报告"""
        if not self.pattern_report.exists():
            return None
        
        with open(self.pattern_report, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_lessons(self) -> List[Dict[str, Any]]:
        """提取所有 lesson"""
        self.load_existing_lessons()
        pattern_report = self.load_pattern_report()
        
        if not pattern_report:
            return []
        
        lessons = []
        
        # 1. 检测 policy_over_conservative
        lesson = self._extract_policy_over_conservative(pattern_report)
        if lesson:
            lessons.append(lesson)
        
        # 2. 检测 fallback_single_path
        lesson = self._extract_fallback_single_path(pattern_report)
        if lesson:
            lessons.append(lesson)
        
        # 3. 检测 handler_distribution_too_narrow
        lesson = self._extract_handler_distribution_too_narrow(pattern_report)
        if lesson:
            lessons.append(lesson)
        
        # 4. 检测 handler_rejection_bias
        lesson = self._extract_handler_rejection_bias(pattern_report)
        if lesson:
            lessons.append(lesson)
        
        return lessons
    
    def _extract_policy_over_conservative(self, report: Dict) -> Optional[Dict]:
        """提取"策略过于保守"lesson"""
        policy_triggers = report['patterns']['policy_trigger']['top_5']
        
        if not policy_triggers:
            return None
        
        # 检查是否所有 policy 都是 degrade
        degrade_count = sum(
            p['count'] for p in policy_triggers 
            if 'degrade:' in p['pattern']
        )
        total_count = sum(p['count'] for p in policy_triggers)
        
        if total_count == 0:
            return None
        
        degrade_ratio = degrade_count / total_count
        
        # 如果 degrade 占比 > 80%，认为过于保守
        if degrade_ratio > 0.8:
            trigger_pattern = f"degrade policy used in {degrade_ratio:.0%} of decisions"
            
            # 去重检查
            if trigger_pattern in self.existing_lesson_patterns:
                return None
            
            evidence = [p['pattern'] for p in policy_triggers[:3]]
            
            return {
                "lesson_id": self._generate_lesson_id("policy_conservative"),
                "lesson_type": DispatchLessonType.POLICY_OVER_CONSERVATIVE.value,
                "trigger_pattern": trigger_pattern,
                "false_assumption": "all tasks should be degraded by default for safety",
                "correct_model": "differentiate safe tasks from risky tasks, apply degrade selectively",
                "evidence": evidence,
                "recommended_rule": "add policy rules to allow safe tasks without degradation",
                "consumer_modules": ["policy-decision", "unified-router"],
                "confidence": min(0.9, degrade_ratio),
                "extracted_at": datetime.now().isoformat()
            }
        
        return None
    
    def _extract_fallback_single_path(self, report: Dict) -> Optional[Dict]:
        """提取"fallback 路径单一"lesson"""
        fallback_routes = report['patterns']['fallback_route']['top_5']
        
        if not fallback_routes:
            return None
        
        # 检查是否只有一种 fallback
        if len(fallback_routes) == 1:
            top_fallback = fallback_routes[0]
            trigger_pattern = f"{top_fallback['pattern']} used in 100% of fallback cases"
            
            # 去重检查
            if trigger_pattern in self.existing_lesson_patterns:
                return None
            
            return {
                "lesson_id": self._generate_lesson_id("fallback_single"),
                "lesson_type": DispatchLessonType.FALLBACK_SINGLE_PATH.value,
                "trigger_pattern": trigger_pattern,
                "false_assumption": "single fallback path is sufficient for all degraded states",
                "correct_model": "different degraded situations need differentiated fallback paths",
                "evidence": [top_fallback['pattern']],
                "recommended_rule": "add fallback types: escalate (for critical), notify (for alerts), skip (for low-priority)",
                "consumer_modules": ["policy-decision", "health-monitor"],
                "confidence": 0.9,
                "extracted_at": datetime.now().isoformat()
            }
        
        # 检查是否某个 fallback 占比过高
        total_count = sum(f['count'] for f in fallback_routes)
        top_fallback = fallback_routes[0]
        top_ratio = top_fallback['count'] / total_count
        
        if top_ratio > 0.8:
            trigger_pattern = f"{top_fallback['pattern']} used in {top_ratio:.0%} of fallback cases"
            
            if trigger_pattern in self.existing_lesson_patterns:
                return None
            
            return {
                "lesson_id": self._generate_lesson_id("fallback_dominant"),
                "lesson_type": DispatchLessonType.FALLBACK_SINGLE_PATH.value,
                "trigger_pattern": trigger_pattern,
                "false_assumption": "one fallback path can handle most cases",
                "correct_model": "fallback diversity improves system resilience",
                "evidence": [f['pattern'] for f in fallback_routes[:3]],
                "recommended_rule": "balance fallback distribution, avoid over-reliance on single path",
                "consumer_modules": ["policy-decision"],
                "confidence": min(0.9, top_ratio),
                "extracted_at": datetime.now().isoformat()
            }
        
        return None
    
    def _extract_handler_distribution_too_narrow(self, report: Dict) -> Optional[Dict]:
        """提取"handler 分布过窄"lesson"""
        # 从 dispatch_log 读取 chosen_handler 分布
        if not self.dispatch_log.exists():
            return None
        
        handler_counts = {}
        total_count = 0
        
        with open(self.dispatch_log, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if 'decision_record' in entry:
                        handler = entry['decision_record'].get('chosen_handler', 'unknown')
                        handler_counts[handler] = handler_counts.get(handler, 0) + 1
                        total_count += 1
                except:
                    continue
        
        if total_count == 0:
            return None
        
        # 检查是否某个 handler 占比过高
        if handler_counts:
            top_handler = max(handler_counts.items(), key=lambda x: x[1])
            top_ratio = top_handler[1] / total_count
            
            if top_ratio > 0.8:
                trigger_pattern = f"{top_handler[0]} chosen in {top_ratio:.0%} of decisions"
                
                if trigger_pattern in self.existing_lesson_patterns:
                    return None
                
                return {
                    "lesson_id": self._generate_lesson_id("handler_narrow"),
                    "lesson_type": DispatchLessonType.HANDLER_DISTRIBUTION_TOO_NARROW.value,
                    "trigger_pattern": trigger_pattern,
                    "false_assumption": "one handler can handle most tasks effectively",
                    "correct_model": "diverse handler distribution indicates healthy routing",
                    "evidence": [f"{h}: {c} times" for h, c in sorted(handler_counts.items(), key=lambda x: -x[1])[:3]],
                    "recommended_rule": "add more handler routing samples, verify router is not biased",
                    "consumer_modules": ["unified-router", "health-monitor"],
                    "confidence": min(0.9, top_ratio),
                    "extracted_at": datetime.now().isoformat()
                }
        
        return None
    
    def _extract_handler_rejection_bias(self, report: Dict) -> Optional[Dict]:
        """提取"handler 淘汰偏见"lesson"""
        rejected_handlers = report['patterns']['handler_rejection']['top_5']
        
        if not rejected_handlers:
            return None
        
        # 检查是否某个 handler 总被淘汰
        top_rejected = rejected_handlers[0]
        
        if top_rejected['count'] >= 3:
            # 分析淘汰原因
            reasons = top_rejected.get('sample_reasons', [])
            chosen_handlers = [r['chosen_instead'] for r in reasons]
            
            # 如果总被同一个 handler 替代
            if chosen_handlers and len(set(chosen_handlers)) == 1:
                dominant_handler = chosen_handlers[0]
                trigger_pattern = f"{top_rejected['handler']} always rejected in favor of {dominant_handler}"
                
                if trigger_pattern in self.existing_lesson_patterns:
                    return None
                
                return {
                    "lesson_id": self._generate_lesson_id("handler_bias"),
                    "lesson_type": DispatchLessonType.HANDLER_REJECTION_BIAS.value,
                    "trigger_pattern": trigger_pattern,
                    "false_assumption": f"{dominant_handler} is always better than {top_rejected['handler']}",
                    "correct_model": "different handlers excel in different contexts",
                    "evidence": [f"Rejected {top_rejected['count']} times, always chosen: {dominant_handler}"],
                    "recommended_rule": f"review routing logic: is {top_rejected['handler']} truly unsuitable, or is {dominant_handler} over-prioritized?",
                    "consumer_modules": ["unified-router"],
                    "confidence": 0.8,
                    "extracted_at": datetime.now().isoformat()
                }
        
        return None
    
    def _generate_lesson_id(self, prefix: str) -> str:
        """生成唯一的 lesson ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lesson_id = f"dispatch_{prefix}_{timestamp}"
        
        # 确保唯一
        counter = 1
        while lesson_id in self.existing_lesson_ids:
            lesson_id = f"dispatch_{prefix}_{timestamp}_{counter}"
            counter += 1
        
        return lesson_id
    
    def save_lessons(self, lessons: List[Dict[str, Any]]):
        """保存新 lesson"""
        if not lessons:
            print("⚠️  没有新的 lesson 需要保存")
            return
        
        # 保存到 new_dispatch_lessons.json
        with open(self.new_lessons_file, 'w', encoding='utf-8') as f:
            json.dump({
                "extracted_at": datetime.now().isoformat(),
                "total_lessons": len(lessons),
                "lessons": lessons
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已保存 {len(lessons)} 条新 lesson: {self.new_lessons_file}")
        
        # 写回 lessons.json
        self._append_to_lessons_json(lessons)
    
    def _append_to_lessons_json(self, new_lessons: List[Dict[str, Any]]):
        """追加到 lessons.json"""
        if self.existing_lessons.exists():
            with open(self.existing_lessons, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 支持两种格式：列表或字典
                if isinstance(data, list):
                    lessons = data
                elif isinstance(data, dict):
                    lessons = data.get('lessons', [])
                else:
                    lessons = []
        else:
            lessons = []
        
        lessons.extend(new_lessons)
        
        # 保存为字典格式（标准格式）
        output = {
            "lessons": lessons,
            "last_updated": datetime.now().isoformat(),
            "total_lessons": len(lessons)
        }
        
        with open(self.existing_lessons, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已写回 lessons.json（新增 {len(new_lessons)} 条）")
    
    def generate_summary(self, lessons: List[Dict[str, Any]]):
        """生成可读总结"""
        if not lessons:
            summary = "# Dispatch Lessons Summary\n\n无新 lesson 提取。\n"
        else:
            summary = f"# Dispatch Lessons Summary\n\n"
            summary += f"**生成时间：** {datetime.now().isoformat()}\n"
            summary += f"**新 lesson 数量：** {len(lessons)}\n\n"
            summary += "---\n\n"
            
            for i, lesson in enumerate(lessons, 1):
                summary += f"## Lesson {i}: {lesson['lesson_type']}\n\n"
                summary += f"**Lesson ID:** {lesson['lesson_id']}\n\n"
                summary += f"**触发模式：** {lesson['trigger_pattern']}\n\n"
                summary += f"**错误假设：** {lesson['false_assumption']}\n\n"
                summary += f"**正确模型：** {lesson['correct_model']}\n\n"
                summary += f"**证据：**\n"
                for evidence in lesson['evidence']:
                    summary += f"- {evidence}\n"
                summary += f"\n**推荐规则：** {lesson['recommended_rule']}\n\n"
                summary += f"**消费模块：** {', '.join(lesson['consumer_modules'])}\n\n"
                summary += f"**置信度：** {lesson['confidence']:.2f}\n\n"
                summary += "---\n\n"
            
            # 固定结论句式
            summary += "## 总结\n\n"
            
            if lessons:
                top_lesson = max(lessons, key=lambda l: l['confidence'])
                summary += f"**当前最值得沉淀的中枢经验：** {top_lesson['trigger_pattern']}\n\n"
                summary += f"**当前最明显的错误假设：** {top_lesson['false_assumption']}\n\n"
                summary += f"**当前最应该写回系统规则的改进：** {top_lesson['recommended_rule']}\n\n"
                summary += f"**这条经验下一步应被哪个模块消费：** {', '.join(top_lesson['consumer_modules'])}\n"
        
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"✅ 已生成总结: {self.summary_file}")
    
    def run(self):
        """执行完整流程"""
        print("🔍 开始提取中枢决策经验...")
        
        lessons = self.extract_lessons()
        
        if not lessons:
            print("⚠️  未发现新的可提取 lesson")
            self.generate_summary([])
            return
        
        print(f"✅ 提取到 {len(lessons)} 条新 lesson")
        
        self.save_lessons(lessons)
        self.generate_summary(lessons)
        
        print("\n" + "="*60)
        print("中枢决策经验提取完成")
        print("="*60)


def main():
    """主函数"""
    extractor = DispatchLessonExtractor()
    extractor.run()


if __name__ == '__main__':
    main()
