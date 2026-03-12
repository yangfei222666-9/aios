#!/usr/bin/env python3
"""
测试 Dispatch Pattern Detector

验证 4 类决策模式识别能力
"""

import json
import pytest
from pathlib import Path
from dispatch_pattern_detector import DispatchPatternDetector, DecisionPatternType


@pytest.fixture
def test_data_dir(tmp_path):
    """创建测试数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_dispatch_log(test_data_dir):
    """创建样本决策日志"""
    log_file = test_data_dir / "dispatch_log.jsonl"
    
    records = [
        # 1. routine_monitor 被降级
        {
            "timestamp": "2026-03-11T08:00:00",
            "current_situation": "routine_monitor",
            "rejected_handlers": ["skill-executor", "agent-dispatcher"],
            "chosen_handler": "aios-health-monitor",
            "policy_result": "degrade",
            "policy_reason": "low_priority_task",
            "fallback_action": "retry_later",
            "final_status": "degraded"
        },
        # 2. routine_alert 被降级
        {
            "timestamp": "2026-03-11T08:05:00",
            "current_situation": "routine_alert",
            "rejected_handlers": ["skill-executor"],
            "chosen_handler": "aios-health-monitor",
            "policy_result": "degrade",
            "policy_reason": "rate_limit",
            "fallback_action": "retry_later",
            "final_status": "degraded"
        },
        # 3. critical_alert 被降级
        {
            "timestamp": "2026-03-11T08:10:00",
            "current_situation": "critical_alert",
            "rejected_handlers": ["agent-dispatcher"],
            "chosen_handler": "aios-health-monitor",
            "policy_result": "degrade",
            "policy_reason": "resource_exhausted",
            "fallback_action": "retry_later",
            "final_status": "degraded"
        },
        # 4. routine_monitor 再次被降级
        {
            "timestamp": "2026-03-11T08:15:00",
            "current_situation": "routine_monitor",
            "rejected_handlers": ["skill-executor"],
            "chosen_handler": "aios-health-monitor",
            "policy_result": "degrade",
            "policy_reason": "low_priority_task",
            "fallback_action": "retry_later",
            "final_status": "degraded"
        },
        # 5. 正常执行（不应被计入降级模式）
        {
            "timestamp": "2026-03-11T08:20:00",
            "current_situation": "user_request",
            "rejected_handlers": [],
            "chosen_handler": "skill-executor",
            "policy_result": "allow",
            "policy_reason": "normal_execution",
            "fallback_action": "none",
            "final_status": "completed"
        }
    ]
    
    with open(log_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return log_file


def test_load_dispatch_log(test_data_dir, sample_dispatch_log):
    """测试加载决策日志"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    records = detector.load_dispatch_log()
    
    assert len(records) == 5
    assert records[0]['current_situation'] == 'routine_monitor'


def test_detect_input_degradation_patterns(test_data_dir, sample_dispatch_log):
    """测试输入降级模式检测"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    detector.load_dispatch_log()
    detector.detect_input_degradation_patterns()
    
    # routine_monitor 出现 2 次降级
    assert detector.degraded_situations['routine_monitor → degraded'] == 2
    # routine_alert 出现 1 次降级
    assert detector.degraded_situations['routine_alert → degraded'] == 1
    # critical_alert 出现 1 次降级
    assert detector.degraded_situations['critical_alert → degraded'] == 1
    # user_request 不应被计入（状态是 completed）
    assert 'user_request → completed' not in detector.degraded_situations


def test_detect_handler_rejection_patterns(test_data_dir, sample_dispatch_log):
    """测试 handler 淘汰模式检测"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    detector.load_dispatch_log()
    detector.detect_handler_rejection_patterns()
    
    # skill-executor 被淘汰 3 次
    assert detector.rejected_handlers['skill-executor'] == 3
    # agent-dispatcher 被淘汰 2 次
    assert detector.rejected_handlers['agent-dispatcher'] == 2
    
    # 检查淘汰原因记录
    assert len(detector.rejection_reasons['skill-executor']) == 3
    assert detector.rejection_reasons['skill-executor'][0]['chosen_instead'] == 'aios-health-monitor'


def test_detect_policy_trigger_patterns(test_data_dir, sample_dispatch_log):
    """测试 policy 触发模式检测"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    detector.load_dispatch_log()
    detector.detect_policy_trigger_patterns()
    
    # degrade: low_priority_task 出现 2 次
    assert detector.policy_triggers['degrade: low_priority_task'] == 2
    # degrade: rate_limit 出现 1 次
    assert detector.policy_triggers['degrade: rate_limit'] == 1
    # degrade: resource_exhausted 出现 1 次
    assert detector.policy_triggers['degrade: resource_exhausted'] == 1
    # allow 不应被计入
    assert 'allow: normal_execution' not in detector.policy_triggers


def test_detect_fallback_route_patterns(test_data_dir, sample_dispatch_log):
    """测试 fallback 路径模式检测"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    detector.load_dispatch_log()
    detector.detect_fallback_route_patterns()
    
    # retry_later 出现 4 次
    assert detector.fallback_routes['retry_later (→ degraded)'] == 4
    # none 不应被计入
    assert 'none (→ completed)' not in detector.fallback_routes


def test_full_analysis(test_data_dir, sample_dispatch_log):
    """测试完整分析流程"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    report = detector.analyze()
    
    # 基本信息
    assert report['total_records'] == 5
    assert 'patterns' in report
    assert 'summary' in report
    assert 'optimization_target' in report
    
    # 检查 4 类模式
    patterns = report['patterns']
    assert 'input_degradation' in patterns
    assert 'handler_rejection' in patterns
    assert 'policy_trigger' in patterns
    assert 'fallback_route' in patterns
    
    # 检查 Top 5
    assert len(patterns['input_degradation']['top_5']) > 0
    assert len(patterns['handler_rejection']['top_5']) > 0
    assert len(patterns['policy_trigger']['top_5']) > 0
    assert len(patterns['fallback_route']['top_5']) > 0


def test_summary_format(test_data_dir, sample_dispatch_log):
    """测试总结格式"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    report = detector.analyze()
    summary = report['summary']
    
    # 检查固定句式
    assert "当前最常被降级的输入类型：" in summary
    assert "当前最常被淘汰的 handler：" in summary
    assert "当前最常触发的 policy 原因：" in summary
    assert "当前最常走的 fallback 路径：" in summary


def test_optimization_target(test_data_dir, sample_dispatch_log):
    """测试优化目标识别"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    report = detector.analyze()
    
    # 应该识别出 fallback 路径过于单一（retry_later 出现 4 次）
    assert "fallback 路径过于单一" in report['optimization_target']
    assert "retry_later" in report['optimization_target']


def test_empty_log(test_data_dir):
    """测试空日志处理"""
    detector = DispatchPatternDetector(data_dir=test_data_dir)
    report = detector.analyze()
    
    assert report['status'] == 'no_data'
    assert 'message' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
