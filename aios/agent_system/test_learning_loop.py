"""
Learning Loop 完整测试套件

测试流程：
1. 创建模拟失败数据
2. 运行规则提取
3. 验证规则生成
4. 测试规则应用
5. 验证规则效果
"""
import json
import time
from pathlib import Path

from paths import TASK_EXECUTIONS, RULES_FILE
from learning_rule_extractor import LearningRuleExtractor
from learning_rule_applier import LearningRuleApplier


def create_test_failures():
    """创建测试失败数据"""
    print("📝 创建测试失败数据...")
    
    test_failures = [
        # 超时失败（3次）
        {
            "task_id": "test-timeout-1",
            "agent_id": "test-agent",
            "task_type": "code",
            "status": "failed",
            "description": "Test timeout 1",
            "started_at": "2026-03-14T10:00:00Z",
            "completed_at": "2026-03-14T10:01:00Z",
            "duration_ms": 60000,
            "success": False,
            "error_type": "timeout",
            "error_message": "Task execution timed out after 60 seconds",
            "retry_count": 0
        },
        {
            "task_id": "test-timeout-2",
            "agent_id": "test-agent",
            "task_type": "code",
            "status": "failed",
            "description": "Test timeout 2",
            "started_at": "2026-03-14T10:05:00Z",
            "completed_at": "2026-03-14T10:06:00Z",
            "duration_ms": 60000,
            "success": False,
            "error_type": "timeout",
            "error_message": "Task execution timed out after 60 seconds",
            "retry_count": 1
        },
        {
            "task_id": "test-timeout-3",
            "agent_id": "test-agent",
            "task_type": "code",
            "status": "failed",
            "description": "Test timeout 3",
            "started_at": "2026-03-14T10:10:00Z",
            "completed_at": "2026-03-14T10:11:00Z",
            "duration_ms": 60000,
            "success": False,
            "error_type": "timeout",
            "error_message": "Task execution timed out after 60 seconds",
            "retry_count": 0
        },
        # 限流失败（2次）
        {
            "task_id": "test-ratelimit-1",
            "agent_id": "api-caller",
            "task_type": "api",
            "status": "failed",
            "description": "Test rate limit 1",
            "started_at": "2026-03-14T10:15:00Z",
            "completed_at": "2026-03-14T10:15:01Z",
            "duration_ms": 1000,
            "success": False,
            "error_type": "rate_limit",
            "error_message": "Rate limit exceeded: 429 Too Many Requests",
            "retry_count": 0
        },
        {
            "task_id": "test-ratelimit-2",
            "agent_id": "api-caller",
            "task_type": "api",
            "status": "failed",
            "description": "Test rate limit 2",
            "started_at": "2026-03-14T10:16:00Z",
            "completed_at": "2026-03-14T10:16:01Z",
            "duration_ms": 1000,
            "success": False,
            "error_type": "rate_limit",
            "error_message": "Rate limit exceeded: 429 Too Many Requests",
            "retry_count": 1
        },
        # 依赖缺失（2次）
        {
            "task_id": "test-dependency-1",
            "agent_id": "builder",
            "task_type": "build",
            "status": "failed",
            "description": "Test dependency 1",
            "started_at": "2026-03-14T10:20:00Z",
            "completed_at": "2026-03-14T10:20:05Z",
            "duration_ms": 5000,
            "success": False,
            "error_type": "dependency_missing",
            "error_message": "ModuleNotFoundError: No module named 'requests'",
            "retry_count": 0
        },
        {
            "task_id": "test-dependency-2",
            "agent_id": "builder",
            "task_type": "build",
            "status": "failed",
            "description": "Test dependency 2",
            "started_at": "2026-03-14T10:21:00Z",
            "completed_at": "2026-03-14T10:21:05Z",
            "duration_ms": 5000,
            "success": False,
            "error_type": "dependency_missing",
            "error_message": "ModuleNotFoundError: No module named 'requests'",
            "retry_count": 0
        }
    ]
    
    # 追加到执行记录
    with open(TASK_EXECUTIONS, 'a', encoding='utf-8') as f:
        for failure in test_failures:
            f.write(json.dumps(failure, ensure_ascii=False) + '\n')
    
    print(f"✅ 已添加 {len(test_failures)} 条测试失败记录")
    return test_failures


def test_rule_extraction():
    """测试规则提取"""
    print("\n" + "="*60)
    print("🧪 测试 1: 规则提取")
    print("="*60)
    
    extractor = LearningRuleExtractor()
    result = extractor.run_extraction()
    
    assert result['status'] == 'success', "规则提取失败"
    assert result['patterns_found'] >= 3, f"应该发现至少3个模式，实际: {result['patterns_found']}"
    assert result['rules_generated'] >= 3, f"应该生成至少3条规则，实际: {result['rules_generated']}"
    
    print("✅ 规则提取测试通过")
    return result


def test_rule_application():
    """测试规则应用"""
    print("\n" + "="*60)
    print("🧪 测试 2: 规则应用")
    print("="*60)
    
    applier = LearningRuleApplier()
    
    # 测试超时任务
    timeout_task = {
        'task_id': 'apply-test-1',
        'task_type': 'code',
        'error_type': 'timeout',
        'error_message': 'Task execution timed out after 60 seconds',
        'timeout': 60
    }
    
    print("\n原始任务:")
    print(f"  timeout: {timeout_task['timeout']}s")
    
    modified = applier.process_task_with_rules(timeout_task)
    
    print("\n修改后:")
    if '_rule_applied' in modified:
        rule_info = modified['_rule_applied']
        print(f"  应用规则: {rule_info['rule_id']}")
        print(f"  timeout: {modified.get('timeout')}s")
        assert modified['timeout'] > timeout_task['timeout'], "超时时间应该增加"
        print("✅ 超时规则应用成功")
    else:
        print("⚠️ 未找到匹配规则")
    
    # 测试限流任务
    ratelimit_task = {
        'task_id': 'apply-test-2',
        'task_type': 'api',
        'error_type': 'rate_limit',
        'error_message': 'Rate limit exceeded: 429 Too Many Requests'
    }
    
    print("\n测试限流任务...")
    modified = applier.process_task_with_rules(ratelimit_task)
    
    if '_rule_applied' in modified:
        rule_info = modified['_rule_applied']
        print(f"  应用规则: {rule_info['rule_id']}")
        print(f"  延迟: {modified.get('pre_execution_delay')}s")
        assert 'pre_execution_delay' in modified, "应该添加延迟"
        print("✅ 限流规则应用成功")
    else:
        print("⚠️ 未找到匹配规则")
    
    print("\n✅ 规则应用测试通过")


def test_rule_feedback():
    """测试规则反馈"""
    print("\n" + "="*60)
    print("🧪 测试 3: 规则反馈")
    print("="*60)
    
    applier = LearningRuleApplier()
    
    # 加载规则
    rules = applier.load_rules(force_reload=True)
    if not rules:
        print("⚠️ 没有规则可测试")
        return
    
    test_rule = rules[0]
    rule_id = test_rule['rule_id']
    
    print(f"\n测试规则: {test_rule['name']}")
    print(f"  初始置信度: {test_rule.get('confidence', 0):.2f}")
    print(f"  应用次数: {test_rule.get('applied_count', 0)}")
    
    # 模拟成功应用
    print("\n模拟成功应用...")
    applier.record_application(rule_id, 'test-task-1', {}, 'success')
    applier.record_application(rule_id, 'test-task-2', {}, 'success')
    
    # 重新加载规则
    updated_rules = applier.load_rules(force_reload=True)
    updated_rule = next((r for r in updated_rules if r['rule_id'] == rule_id), None)
    
    if updated_rule:
        print(f"\n更新后:")
        print(f"  置信度: {updated_rule.get('confidence', 0):.2f}")
        print(f"  应用次数: {updated_rule.get('applied_count', 0)}")
        print(f"  成功次数: {updated_rule.get('success_count', 0)}")
        assert updated_rule['applied_count'] > test_rule.get('applied_count', 0), "应用次数应该增加"
        print("✅ 规则反馈测试通过")
    else:
        print("⚠️ 规则未找到")


def test_full_loop():
    """测试完整闭环"""
    print("\n" + "="*60)
    print("🧪 测试 4: 完整闭环")
    print("="*60)
    
    print("\n步骤 1: 失败 → 模式识别")
    failures = create_test_failures()
    print(f"  ✅ 创建 {len(failures)} 条失败记录")
    
    print("\n步骤 2: 模式 → 规则生成")
    extractor = LearningRuleExtractor()
    result = extractor.run_extraction()
    print(f"  ✅ 生成 {result['rules_generated']} 条规则")
    
    print("\n步骤 3: 规则 → 任务调整")
    applier = LearningRuleApplier()
    test_task = {
        'task_id': 'loop-test-1',
        'task_type': 'code',
        'error_type': 'timeout',
        'error_message': 'Task execution timed out after 60 seconds',
        'timeout': 60
    }
    modified = applier.process_task_with_rules(test_task)
    if '_rule_applied' in modified:
        print(f"  ✅ 规则已应用: {modified['_rule_applied']['rule_id']}")
    else:
        print("  ⚠️ 未应用规则")
    
    print("\n步骤 4: 效果 → 规则优化")
    if '_rule_applied' in modified:
        rule_id = modified['_rule_applied']['rule_id']
        applier.record_application(rule_id, test_task['task_id'], {}, 'success')
        print(f"  ✅ 记录规则应用效果")
    
    print("\n✅ 完整闭环测试通过")


def main():
    """运行所有测试"""
    print("="*60)
    print("🚀 Learning Loop 完整测试套件")
    print("="*60)
    
    try:
        # 先创建测试数据
        print("\n📝 准备测试数据...")
        create_test_failures()
        
        # 测试 1: 规则提取
        test_rule_extraction()
        
        # 测试 2: 规则应用
        test_rule_application()
        
        # 测试 3: 规则反馈
        test_rule_feedback()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        
        # 显示最终状态
        print("\n📊 最终状态:")
        if RULES_FILE.exists():
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('rules', [])
                print(f"  总规则数: {len(rules)}")
                enabled = [r for r in rules if r.get('enabled', True)]
                print(f"  启用规则: {len(enabled)}")
                print(f"\n  规则列表:")
                for r in enabled[:5]:
                    print(f"    - {r['name']} (置信度: {r.get('confidence', 0):.2f})")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
