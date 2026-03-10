"""
rules.py - 封装去重规则、隔离模块规则、变化检测逻辑
"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class DedupRules:
    """去重规则管理"""

    def __init__(self, rules_path: Optional[Path] = None):
        self.rules_path = rules_path or Path(__file__).parent / 'memory' / 'dedup_rules.json'
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """加载去重规则"""
        if not self.rules_path.exists():
            # 默认规则
            return {
                "alert_dedup_enabled": True,
                "notify_again_conditions": [
                    "severity_upgraded",
                    "error_type_changed",
                    "failure_count_increased",
                    "fixed_then_recurred"
                ],
                "quarantined_modules_notify": False
            }
        
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def should_dedup(self) -> bool:
        """是否启用去重"""
        return self.rules.get('alert_dedup_enabled', True)

    def should_notify_quarantined(self) -> bool:
        """隔离模块是否通知"""
        return self.rules.get('quarantined_modules_notify', False)

    def get_notify_again_conditions(self) -> List[str]:
        """获取重新通知条件"""
        return self.rules.get('notify_again_conditions', [])


class QuarantinedModules:
    """隔离模块管理"""

    def __init__(self, modules_path: Optional[Path] = None):
        self.modules_path = modules_path or Path(__file__).parent / 'memory' / 'quarantined_modules.json'
        self.modules = self._load_modules()

    def _load_modules(self) -> List[Dict]:
        """加载隔离模块列表"""
        if not self.modules_path.exists():
            return []
        
        with open(self.modules_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_quarantined(self, module_name: str) -> bool:
        """检查模块是否已隔离"""
        for module in self.modules:
            if module.get('module_name') == module_name:
                return module.get('status') == 'quarantined'
        return False

    def get_quarantine_info(self, module_name: str) -> Optional[Dict]:
        """获取隔离信息"""
        for module in self.modules:
            if module.get('module_name') == module_name:
                return module
        return None


class KnownAlerts:
    """已知告警历史管理"""

    def __init__(self, alerts_path: Optional[Path] = None):
        self.alerts_path = alerts_path or Path(__file__).parent / 'memory' / 'known_alerts.json'
        self.alerts = self._load_alerts()

    def _load_alerts(self) -> List[Dict]:
        """加载已知告警"""
        if not self.alerts_path.exists():
            return []
        
        with open(self.alerts_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def find_alert(self, alert_key: str) -> Optional[Dict]:
        """查找历史告警"""
        for alert in self.alerts:
            if alert.get('alert_key') == alert_key:
                return alert
        return None

    def has_changed(self, alert_key: str, current_evidence: Dict) -> tuple[bool, str]:
        """
        检查告警是否发生变化
        
        Returns:
            (has_changed, reason)
        """
        historical = self.find_alert(alert_key)
        if not historical:
            return True, "first_seen_alert"

        # 检查严重程度是否升级
        hist_severity = historical.get('severity', '')
        curr_severity = current_evidence.get('severity', '')
        if self._is_severity_upgraded(hist_severity, curr_severity):
            return True, "severity_upgraded"

        # 检查错误类型是否变化
        hist_error = historical.get('error_type', '')
        curr_error = current_evidence.get('error_type', '')
        if hist_error and curr_error and hist_error != curr_error:
            return True, "error_type_changed"

        # 检查失败次数是否增加
        hist_count = historical.get('failure_count', 0)
        curr_count = current_evidence.get('failure_count', 0)
        if curr_count > hist_count:
            return True, "failure_count_increased"

        # 检查是否修复后复发
        if historical.get('status') == 'fixed' and current_evidence.get('status') == 'failed':
            return True, "fixed_then_recurred"

        return False, "no_change"

    def _is_severity_upgraded(self, old: str, new: str) -> bool:
        """判断严重程度是否升级"""
        severity_levels = {'INFO': 0, 'WARN': 1, 'ERROR': 2, 'CRIT': 3}
        old_level = severity_levels.get(old.upper(), 0)
        new_level = severity_levels.get(new.upper(), 0)
        return new_level > old_level


class AlertKeyGenerator:
    """告警主键生成器 - 统一的 key 生成规则"""

    @staticmethod
    def generate(candidate) -> str:
        """
        生成 alert_key（从 CandidateAlert 对象）
        
        规则：
        - Skill failure: skill:{skill_name}:{error_type}:{severity}
        - Module error: module:{module_name}:{error_type}
        - System signal: signal:{signal_name}:{status}
        """
        if candidate.source_type == 'skill_failure':
            return AlertKeyGenerator.build_skill_key(
                candidate.skill_name,
                candidate.error_type,
                candidate.severity
            )
        
        elif candidate.source_type == 'module_error':
            return AlertKeyGenerator.build_module_key(
                candidate.module_name,
                candidate.error_type
            )
        
        elif candidate.source_type == 'system_signal':
            return AlertKeyGenerator.build_signal_key(
                candidate.signal_name,
                candidate.status
            )
        
        else:
            return f"unknown:{candidate.source_type}"

    @staticmethod
    def build_skill_key(skill_name: str, error_type: str, severity: str) -> str:
        """构建 Skill failure 的 alert_key"""
        return f"skill:{skill_name}:{error_type}:{severity}"

    @staticmethod
    def build_module_key(module_name: str, error_type: str) -> str:
        """构建 Module error 的 alert_key"""
        return f"module:{module_name}:{error_type}"

    @staticmethod
    def build_signal_key(signal_name: str, status: str) -> str:
        """构建 System signal 的 alert_key"""
        return f"signal:{signal_name}:{status}"


if __name__ == '__main__':
    # 简单测试
    rules = DedupRules()
    print(f"Dedup enabled: {rules.should_dedup()}")
    print(f"Notify conditions: {rules.get_notify_again_conditions()}")
    
    quarantined = QuarantinedModules()
    print(f"Is low_success_regeneration.py quarantined: {quarantined.is_quarantined('low_success_regeneration.py')}")
