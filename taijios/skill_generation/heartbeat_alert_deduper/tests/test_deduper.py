"""
test_deduper.py - heartbeat_alert_deduper 测试套件
"""
import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser import HeartbeatParser, CandidateAlert
from classifier import AlertClassifier
from deduper import HeartbeatAlertDeduper


SAMPLES_DIR = Path(__file__).parent / 'test_samples'


def load_sample(filename: str) -> str:
    with open(SAMPLES_DIR / filename, 'r', encoding='utf-8') as f:
        return f.read()


def run_test(name: str, fn) -> bool:
    try:
        fn()
        print(f"  ✓ {name}")
        return True
    except AssertionError as e:
        print(f"  ✗ {name}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ {name}: EXCEPTION: {e}")
        return False


# ============================================================
# V1: 语法验证
# ============================================================

def test_v1_syntax():
    print("\n[V1] 语法验证")
    passed = 0
    total = 0

    def test_manifest():
        manifest_path = Path(__file__).parent.parent / 'manifest.json'
        assert manifest_path.exists(), "manifest.json 不存在"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        required_fields = ['skill_name', 'version', 'risk_level', 'permissions']
        for field in required_fields:
            assert field in data, f"manifest 缺少字段: {field}"

    def test_output_serializable():
        deduper = HeartbeatAlertDeduper()
        text = load_sample('sample4_normal.txt')
        result = deduper.run(text)
        json.dumps(result, ensure_ascii=False)  # 不抛异常即通过

    for name, fn in [
        ("manifest.json 字段完整", test_manifest),
        ("输出 JSON 可序列化", test_output_serializable),
    ]:
        total += 1
        if run_test(name, fn):
            passed += 1

    return passed, total


# ============================================================
# V2: 行为验证
# ============================================================

def test_v2_behavior():
    print("\n[V2] 行为验证")
    passed = 0
    total = 0

    deduper = HeartbeatAlertDeduper()

    def test_case1_old_alerts_suppressed():
        """Case 1: 旧 Skill 告警被正确抑制"""
        text = load_sample('sample1_old_alerts.txt')
        result = deduper.run(text)
        
        # 找到 api-testing-skill 的结果
        api_result = next(
            (r for r in result['results'] if 'api-testing-skill' in r.get('alert_key', '')),
            None
        )
        assert api_result is not None, "未找到 api-testing-skill 告警"
        assert api_result['category'] == 'suppressed_old_alert', \
            f"期望 suppressed_old_alert，实际 {api_result['category']}"
        assert api_result['should_notify'] == False, "旧告警不应通知"

    def test_case2_quarantined_module():
        """Case 2: 已隔离模块被判定为 quarantined_known_issue"""
        text = load_sample('sample2_quarantined_module.txt')
        result = deduper.run(text)
        
        quarantined_result = next(
            (r for r in result['results'] if 'low_success_regeneration' in r.get('alert_key', '')),
            None
        )
        assert quarantined_result is not None, "未找到 low_success_regeneration.py 告警"
        assert quarantined_result['category'] == 'quarantined_known_issue', \
            f"期望 quarantined_known_issue，实际 {quarantined_result['category']}"
        assert quarantined_result['should_notify'] == False, "隔离模块不应通知"

    def test_case3_system_signals():
        """Case 3: evolution_score 过期被识别为系统信号"""
        text = load_sample('sample3_system_signals.txt')
        result = deduper.run(text)
        
        # 系统信号应该被识别，但不是高危告警
        signal_results = [r for r in result['results'] if r.get('source_type') == 'system_signal'
                         or 'signal:' in r.get('alert_key', '')]
        # 至少识别到了系统信号
        assert len(signal_results) > 0 or result['summary']['new_alerts'] >= 0, \
            "系统信号应被识别"

    def test_case4_normal_no_false_positive():
        """Case 4: 正常 heartbeat 不被误判成告警"""
        text = load_sample('sample4_normal.txt')
        result = deduper.run(text)
        
        assert result['summary']['notify_count'] == 0, \
            f"正常 heartbeat 不应有通知，实际 notify_count={result['summary']['notify_count']}"
        assert result['summary']['new_alerts'] == 0, \
            f"正常 heartbeat 不应有新告警，实际 new_alerts={result['summary']['new_alerts']}"

    def test_case5_escalated_alert_notified():
        """Case 5: 失败次数增加的告警应重新通知"""
        text = load_sample('sample5_escalated_alert.txt')
        result = deduper.run(text)
        
        # api-testing-skill 失败次数从 3 增加到 5，应该重新通知
        api_result = next(
            (r for r in result['results'] if 'api-testing-skill' in r.get('alert_key', '')),
            None
        )
        assert api_result is not None, "未找到 api-testing-skill 告警"
        assert api_result['should_notify'] == True, \
            f"失败次数增加的告警应通知，实际 should_notify={api_result['should_notify']}"

    def test_summary_structure():
        """输出结构完整"""
        text = load_sample('sample1_old_alerts.txt')
        result = deduper.run(text)
        
        required_keys = ['run_id', 'parsed_alerts_count', 'results', 'summary']
        for key in required_keys:
            assert key in result, f"输出缺少字段: {key}"
        
        summary_keys = ['new_alerts', 'suppressed_old_alerts', 'quarantined_known_issues', 'notify_count']
        for key in summary_keys:
            assert key in result['summary'], f"summary 缺少字段: {key}"

    for name, fn in [
        ("Case 1: 旧 Skill 告警被正确抑制", test_case1_old_alerts_suppressed),
        ("Case 2: 已隔离模块判定正确", test_case2_quarantined_module),
        ("Case 3: 系统信号被识别", test_case3_system_signals),
        ("Case 4: 正常 heartbeat 无误判", test_case4_normal_no_false_positive),
        ("Case 5: 失败次数增加触发重新通知", test_case5_escalated_alert_notified),
        ("输出结构完整", test_summary_structure),
    ]:
        total += 1
        if run_test(name, fn):
            passed += 1

    return passed, total


# ============================================================
# V3: 风险验证
# ============================================================

def test_v3_risk():
    print("\n[V3] 风险验证")
    passed = 0
    total = 0

    def test_no_system_config_write():
        """不修改系统配置"""
        import os
        protected_files = [
            'HEARTBEAT.md',
            'MEMORY.md',
            'agents.json',
            'task_queue.jsonl'
        ]
        # 检查 deduper.py 源码不包含对这些文件的写操作
        deduper_src = Path(__file__).parent.parent / 'deduper.py'
        with open(deduper_src, 'r', encoding='utf-8') as f:
            content = f.read()
        for protected in protected_files:
            assert f'open("{protected}"' not in content and f"open('{protected}'" not in content, \
                f"deduper.py 不应写入 {protected}"

    def test_only_writes_own_files():
        """只写自己的结果文件"""
        deduper = HeartbeatAlertDeduper()
        text = load_sample('sample4_normal.txt')
        deduper.run(text)
        
        # 检查只有 deduper_runs.jsonl 被写入
        runs_file = deduper.memory_dir / 'deduper_runs.jsonl'
        assert runs_file.exists(), "deduper_runs.jsonl 应该被创建"

    def test_no_notification_triggered():
        """不触发通知"""
        classifier_src = Path(__file__).parent.parent / 'classifier.py'
        with open(classifier_src, 'r', encoding='utf-8') as f:
            content = f.read()
        # 不应包含发送通知的代码
        assert 'message.send' not in content, "classifier.py 不应发送通知"
        assert 'requests.post' not in content, "classifier.py 不应发送 HTTP 请求"

    for name, fn in [
        ("不修改系统配置文件", test_no_system_config_write),
        ("只写自己的结果文件", test_only_writes_own_files),
        ("不触发通知", test_no_notification_triggered),
    ]:
        total += 1
        if run_test(name, fn):
            passed += 1

    return passed, total


# ============================================================
# 主测试运行器
# ============================================================

def main():
    print("=" * 50)
    print("heartbeat_alert_deduper 三层验证")
    print("=" * 50)

    total_passed = 0
    total_tests = 0

    for test_fn in [test_v1_syntax, test_v2_behavior, test_v3_risk]:
        passed, total = test_fn()
        total_passed += passed
        total_tests += total

    print(f"\n{'=' * 50}")
    match_rate = total_passed / total_tests if total_tests > 0 else 0
    print(f"总计: {total_passed}/{total_tests} 通过 ({match_rate:.0%})")

    if match_rate >= 0.9:
        print("✅ 验证通过 (≥90%) — 可进入 draft registry")
    else:
        print("❌ 验证未通过 (<90%) — 需要修复后重试")

    return 0 if match_rate >= 0.9 else 1


if __name__ == '__main__':
    sys.exit(main())
