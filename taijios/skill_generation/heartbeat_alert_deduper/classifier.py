"""
classifier.py - 告警分类逻辑
"""
from typing import List, Dict
from dataclasses import dataclass, asdict
from parser import CandidateAlert
from rules import DedupRules, QuarantinedModules, KnownAlerts, AlertKeyGenerator


@dataclass
class ClassifiedAlert:
    """分类后的告警"""
    alert_key: str
    category: str  # new_alert | recurring_old_alert | suppressed_old_alert | quarantined_known_issue | non_alert_signal | unknown_needs_review
    should_notify: bool
    reason: str
    evidence: Dict
    raw_text: str

    def to_dict(self):
        return asdict(self)


class AlertClassifier:
    """告警分类器"""

    def __init__(self):
        self.dedup_rules = DedupRules()
        self.quarantined = QuarantinedModules()
        self.known_alerts = KnownAlerts()
        self.key_generator = AlertKeyGenerator()

    def classify(self, candidates: List[CandidateAlert]) -> List[ClassifiedAlert]:
        """
        对候选告警进行分类
        
        Args:
            candidates: 候选告警列表
            
        Returns:
            分类后的告警列表
        """
        results = []

        for candidate in candidates:
            classified = self._classify_single(candidate)
            results.append(classified)

        return results

    def _classify_single(self, candidate: CandidateAlert) -> ClassifiedAlert:
        """对单个候选告警分类"""
        
        # 生成 alert_key
        alert_key = self.key_generator.generate(candidate)

        # 提取证据
        evidence = self._extract_evidence(candidate)

        # 规则 1：已隔离模块优先
        if candidate.source_type == 'module_error' and candidate.module_name:
            if self.quarantined.is_quarantined(candidate.module_name):
                return ClassifiedAlert(
                    alert_key=alert_key,
                    category='quarantined_known_issue',
                    should_notify=self.dedup_rules.should_notify_quarantined(),
                    reason='quarantined_module_known_issue',
                    evidence=evidence,
                    raw_text=candidate.raw_text
                )

        # 规则 5：明显不是告警
        if candidate.source_type == 'non_alert_signal':
            return ClassifiedAlert(
                alert_key=alert_key,
                category='non_alert_signal',
                should_notify=False,
                reason='normal_system_signal',
                evidence=evidence,
                raw_text=candidate.raw_text
            )

        # 规则 2 & 3：历史告警检查
        if self.dedup_rules.should_dedup():
            has_changed, change_reason = self.known_alerts.has_changed(alert_key, evidence)
            
            if not has_changed:
                # 规则 2：历史已报告且无变化
                return ClassifiedAlert(
                    alert_key=alert_key,
                    category='suppressed_old_alert',
                    should_notify=False,
                    reason='previously_reported_no_change',
                    evidence=evidence,
                    raw_text=candidate.raw_text
                )
            
            elif change_reason != 'first_seen_alert':
                # 规则 3：历史已报告但发生变化
                return ClassifiedAlert(
                    alert_key=alert_key,
                    category='new_alert',
                    should_notify=True,
                    reason=f'dedup_break_condition_triggered:{change_reason}',
                    evidence=evidence,
                    raw_text=candidate.raw_text
                )

        # 规则 4：首次出现
        if not self.known_alerts.find_alert(alert_key):
            return ClassifiedAlert(
                alert_key=alert_key,
                category='new_alert',
                should_notify=True,
                reason='first_seen_alert',
                evidence=evidence,
                raw_text=candidate.raw_text
            )

        # 规则 6：无法可靠判断
        return ClassifiedAlert(
            alert_key=alert_key,
            category='unknown_needs_review',
            should_notify=True,
            reason='insufficient_information_for_classification',
            evidence=evidence,
            raw_text=candidate.raw_text
        )

    def _extract_evidence(self, candidate: CandidateAlert) -> Dict:
        """从候选告警中提取证据"""
        evidence = {}

        if candidate.severity:
            evidence['severity'] = candidate.severity
        if candidate.error_type:
            evidence['error_type'] = candidate.error_type
        if candidate.failure_count:
            evidence['failure_count'] = candidate.failure_count
        if candidate.skill_name:
            evidence['skill_name'] = candidate.skill_name
        if candidate.module_name:
            evidence['module_name'] = candidate.module_name
        if candidate.signal_name:
            evidence['signal_name'] = candidate.signal_name
        if candidate.status:
            evidence['status'] = candidate.status
        if candidate.line_no:
            evidence['line_no'] = candidate.line_no

        return evidence


if __name__ == '__main__':
    # 简单测试
    from parser import HeartbeatParser
    
    parser = HeartbeatParser()
    classifier = AlertClassifier()
    
    test_text = """
    api-testing-skill — 连续失败 3 次，原因：network_error
    low_success_regeneration.py 第209行 SyntaxError
    HEARTBEAT_OK
    """
    
    candidates = parser.parse(test_text)
    classified = classifier.classify(candidates)
    
    print(f"Classified {len(classified)} alerts:")
    for alert in classified:
        print(f"  - {alert.category}: {alert.alert_key} (notify: {alert.should_notify})")
