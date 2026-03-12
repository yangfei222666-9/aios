#!/usr/bin/env python3
"""
测试 Dispatch Lesson Extractor

验证从中枢决策模式提取 lesson 的能力
"""

import json
import pytest
from pathlib import Path
from dispatch_lesson_extractor import DispatchLessonExtractor, DispatchLessonType


@pytest.fixture
def test_data_dir(tmp_path):
    """创建测试数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_pattern_report(test_data_dir):
    """创建样本模式报告"""
    report = {
        "timestamp": "2026-03-11T08:52:00",
        "total_records": 6,
        "patterns": {
            "input_degradation": {
                "type": "decision_input_pattern",
                "top_5": [
                    {"pattern": "routine_monitor → degraded", "count": 1},
                    {"pattern": "routine_alert → degraded", "count": 1},
                    {"pattern": "critical_alert → degraded", "count": 1}
                ]
            },
            "handler_rejection": {
                "type": "handler_rejection_pattern",
                "top_5": [
                    {
                        "handler": "pattern-detector",
                        "count": 3,
                        "sample_reasons": [
                            {"chosen_instead": "aios-health-monitor", "situation": "routine_monitor"},
                            {"chosen_instead": "aios-health-monitor", "situation": "routine_alert"},
                            {"chosen_instead": "aios-health-monitor", "situation": "critical_alert"}
                        ]
                    }
                ]
            },
            "policy_trigger": {
                "type": "policy_pattern",
                "top_5": [
                    {"pattern": "degrade: system degraded", "count": 3}
                ]
            },
            "fallback_route": {
                "type": "fallback_pattern",
                "top_5": [
                    {"pattern": "retry_later (→ degraded)", "count": 3}
                ]
            }
        }
    }
    
    report_file = test_data_dir / "dispatch_pattern_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_file


@pytest.fixture
def sample_dispatch_log(test_data_dir):
    """创建样本决策日志"""
    log_file = test_data_dir / "dispatch_log.jsonl"
    
    records = [
        {
            "decision_record": {
                "chosen_handler": "aios-health-monitor",
                "final_status": "degraded"
            },
            "timestamp": "2026-03-11T08:00:00"
        },
        {
            "decision_record": {
                "chosen_handler": "aios-health-monitor",
                "final_status": "degraded"
            },
            "timestamp": "2026-03-11T08:05:00"
        },
        {
            "decision_record": {
                "chosen_handler": "aios-health-monitor",
                "final_status": "degraded"
            },
            "timestamp": "2026-03-11T08:10:00"
        }
    ]
    
    with open(log_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return log_file


def test_extract_policy_over_conservative(test_data_dir, sample_pattern_report):
    """测试提取"策略过于保守"lesson"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    # 应该提取到 policy_over_conservative lesson
    policy_lessons = [l for l in lessons if l['lesson_type'] == DispatchLessonType.POLICY_OVER_CONSERVATIVE.value]
    assert len(policy_lessons) == 1
    
    lesson = policy_lessons[0]
    assert 'degrade policy used in 100%' in lesson['trigger_pattern']
    assert lesson['confidence'] >= 0.9


def test_extract_fallback_single_path(test_data_dir, sample_pattern_report):
    """测试提取"fallback 路径单一"lesson"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    # 应该提取到 fallback_single_path lesson
    fallback_lessons = [l for l in lessons if l['lesson_type'] == DispatchLessonType.FALLBACK_SINGLE_PATH.value]
    assert len(fallback_lessons) == 1
    
    lesson = fallback_lessons[0]
    assert 'retry_later' in lesson['trigger_pattern']
    assert '100%' in lesson['trigger_pattern']
    assert lesson['confidence'] == 0.9


def test_extract_handler_distribution_too_narrow(test_data_dir, sample_pattern_report, sample_dispatch_log):
    """测试提取"handler 分布过窄"lesson"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    # 应该提取到 handler_distribution_too_narrow lesson
    handler_lessons = [l for l in lessons if l['lesson_type'] == DispatchLessonType.HANDLER_DISTRIBUTION_TOO_NARROW.value]
    assert len(handler_lessons) == 1
    
    lesson = handler_lessons[0]
    assert 'aios-health-monitor' in lesson['trigger_pattern']
    assert '100%' in lesson['trigger_pattern']


def test_extract_handler_rejection_bias(test_data_dir, sample_pattern_report):
    """测试提取"handler 淘汰偏见"lesson"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    # 应该提取到 handler_rejection_bias lesson
    bias_lessons = [l for l in lessons if l['lesson_type'] == DispatchLessonType.HANDLER_REJECTION_BIAS.value]
    assert len(bias_lessons) == 1
    
    lesson = bias_lessons[0]
    assert 'pattern-detector' in lesson['trigger_pattern']
    assert 'aios-health-monitor' in lesson['trigger_pattern']


def test_lesson_structure(test_data_dir, sample_pattern_report):
    """测试 lesson 结构完整性"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    assert len(lessons) > 0
    
    for lesson in lessons:
        # 必需字段
        assert 'lesson_id' in lesson
        assert 'lesson_type' in lesson
        assert 'trigger_pattern' in lesson
        assert 'false_assumption' in lesson
        assert 'correct_model' in lesson
        assert 'evidence' in lesson
        assert 'recommended_rule' in lesson
        assert 'consumer_modules' in lesson
        assert 'confidence' in lesson
        assert 'extracted_at' in lesson
        
        # 证据不为空
        assert len(lesson['evidence']) > 0
        
        # 消费模块不为空
        assert len(lesson['consumer_modules']) > 0
        
        # 置信度在合理范围
        assert 0 <= lesson['confidence'] <= 1


def test_avoid_duplicate_lessons(test_data_dir, sample_pattern_report):
    """测试避免重复 lesson"""
    # 创建已有 lessons.json
    existing_lessons = {
        "lessons": [
            {
                "lesson_id": "existing_001",
                "trigger_pattern": "retry_later (→ degraded) used in 100% of fallback cases"
            }
        ]
    }
    
    lessons_file = test_data_dir / "lessons.json"
    with open(lessons_file, 'w', encoding='utf-8') as f:
        json.dump(existing_lessons, f)
    
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    # 不应该提取重复的 fallback_single_path lesson
    fallback_lessons = [l for l in lessons if l['lesson_type'] == DispatchLessonType.FALLBACK_SINGLE_PATH.value]
    assert len(fallback_lessons) == 0


def test_save_and_append_lessons(test_data_dir, sample_pattern_report):
    """测试保存和追加 lesson"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    extractor.save_lessons(lessons)
    
    # 检查 new_dispatch_lessons.json
    new_lessons_file = test_data_dir / "new_dispatch_lessons.json"
    assert new_lessons_file.exists()
    
    with open(new_lessons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data['total_lessons'] == len(lessons)
        assert len(data['lessons']) == len(lessons)
    
    # 检查 lessons.json
    lessons_file = test_data_dir / "lessons.json"
    assert lessons_file.exists()
    
    with open(lessons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data['total_lessons'] == len(lessons)
        assert len(data['lessons']) == len(lessons)


def test_generate_summary(test_data_dir, sample_pattern_report):
    """测试生成总结"""
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    extractor.generate_summary(lessons)
    
    summary_file = test_data_dir / "dispatch_lessons_summary.md"
    assert summary_file.exists()
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查固定句式
        assert '当前最值得沉淀的中枢经验：' in content
        assert '当前最明显的错误假设：' in content
        assert '当前最应该写回系统规则的改进：' in content
        assert '这条经验下一步应被哪个模块消费：' in content


def test_empty_pattern_report(test_data_dir):
    """测试空模式报告"""
    # 创建空报告
    report = {
        "patterns": {
            "input_degradation": {"top_5": []},
            "handler_rejection": {"top_5": []},
            "policy_trigger": {"top_5": []},
            "fallback_route": {"top_5": []}
        }
    }
    
    report_file = test_data_dir / "dispatch_pattern_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f)
    
    extractor = DispatchLessonExtractor(data_dir=test_data_dir)
    lessons = extractor.extract_lessons()
    
    assert len(lessons) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
