"""
parser.py - 从 heartbeat 文本中抽取候选告警
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class CandidateAlert:
    """候选告警数据结构"""
    source_type: str  # skill_failure | module_error | system_signal
    raw_text: str
    skill_name: Optional[str] = None
    module_name: Optional[str] = None
    error_type: Optional[str] = None
    severity: Optional[str] = None
    failure_count: Optional[int] = None
    signal_name: Optional[str] = None
    status: Optional[str] = None
    line_no: Optional[int] = None

    def to_dict(self):
        return asdict(self)


class HeartbeatParser:
    """Heartbeat 文本解析器"""

    # Skill failure 模式
    # 例如：api-testing-skill — 连续失败 3 次，原因：network_error
    SKILL_FAILURE_PATTERN = re.compile(
        r'([a-z0-9\-]+)\s*—\s*连续失败\s*(\d+)\s*次[，,]\s*原因[：:]\s*(\w+)',
        re.IGNORECASE
    )

    # 模块错误模式
    # 例如：low_success_regeneration.py 第209行 SyntaxError
    MODULE_ERROR_PATTERN = re.compile(
        r'([a-z0-9_\.]+\.py)\s*(?:第\s*(\d+)\s*行)?\s*(\w+Error)',
        re.IGNORECASE
    )

    # 导入失败模式
    # 例如：spawn_lock_monitor 导入失败
    IMPORT_ERROR_PATTERN = re.compile(
        r'([a-z0-9_]+)\s*导入失败',
        re.IGNORECASE
    )

    # 系统信号模式
    # 例如：evolution_score.json 已过期
    SYSTEM_SIGNAL_PATTERN = re.compile(
        r'(evolution_score\.json|memory\s+build\s+latency)\s*(已过期|degraded|stale)',
        re.IGNORECASE
    )

    # 正常信号模式（用于排除）
    NORMAL_SIGNAL_PATTERNS = [
        re.compile(r'HEARTBEAT_OK', re.IGNORECASE),
        re.compile(r'Health\s+score:\s*100', re.IGNORECASE),
        re.compile(r'spawn_pending\.jsonl\s+doesn\'t\s+exist', re.IGNORECASE),
        re.compile(r'no\s+pending\s+spawn\s+requests', re.IGNORECASE),
        re.compile(r'所有\s*Agent\s*都运行过', re.IGNORECASE),
    ]

    def parse(self, heartbeat_text: str) -> List[CandidateAlert]:
        """
        从 heartbeat 文本中抽取候选告警
        
        Args:
            heartbeat_text: 完整 heartbeat 输出文本
            
        Returns:
            候选告警列表
        """
        candidates = []
        lines = heartbeat_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是正常信号（排除）
            if self._is_normal_signal(line):
                candidates.append(CandidateAlert(
                    source_type='non_alert_signal',
                    raw_text=line
                ))
                continue

            # 尝试匹配 Skill failure
            skill_match = self.SKILL_FAILURE_PATTERN.search(line)
            if skill_match:
                failure_count = int(skill_match.group(2))
                candidates.append(CandidateAlert(
                    source_type='skill_failure',
                    raw_text=line,
                    skill_name=skill_match.group(1),
                    failure_count=failure_count,
                    error_type=skill_match.group(3),
                    severity=self._infer_severity(line, failure_count)
                ))
                continue

            # 尝试匹配模块错误
            module_match = self.MODULE_ERROR_PATTERN.search(line)
            if module_match:
                candidates.append(CandidateAlert(
                    source_type='module_error',
                    raw_text=line,
                    module_name=module_match.group(1),
                    line_no=int(module_match.group(2)) if module_match.group(2) else None,
                    error_type=module_match.group(3)
                ))
                continue

            # 尝试匹配导入失败
            import_match = self.IMPORT_ERROR_PATTERN.search(line)
            if import_match:
                candidates.append(CandidateAlert(
                    source_type='module_error',
                    raw_text=line,
                    module_name=import_match.group(1),
                    error_type='ImportError'
                ))
                continue

            # 尝试匹配系统信号
            signal_match = self.SYSTEM_SIGNAL_PATTERN.search(line)
            if signal_match:
                candidates.append(CandidateAlert(
                    source_type='system_signal',
                    raw_text=line,
                    signal_name=signal_match.group(1),
                    status=signal_match.group(2)
                ))
                continue

        return candidates

    def _is_normal_signal(self, line: str) -> bool:
        """检查是否是正常信号"""
        for pattern in self.NORMAL_SIGNAL_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def _infer_severity(self, line: str, failure_count: int = None) -> str:
        """
        从文本推断严重程度
        
        优先级：
        1. 文本中的明确关键词
        2. 失败次数（Skill failure 专用）
        3. 默认 INFO
        """
        line_lower = line.lower()
        
        # 优先检查文本关键词
        if 'crit' in line_lower or 'critical' in line_lower:
            return 'CRIT'
        elif 'warn' in line_lower or 'warning' in line_lower:
            return 'WARN'
        elif 'error' in line_lower:
            return 'ERROR'
        
        # 如果有失败次数，根据次数推断
        if failure_count is not None:
            if failure_count >= 3:
                return 'ERROR'
            elif failure_count == 2:
                return 'WARN'
            else:
                return 'INFO'
        
        # 默认
        return 'INFO'


if __name__ == '__main__':
    # 简单测试
    parser = HeartbeatParser()
    
    test_text = """
    AIOS Heartbeat v5.0 Started
    
    api-testing-skill — 连续失败 3 次，原因：network_error
    docker-skill — 连续失败 3 次，原因：resource_exhausted
    low_success_regeneration.py 第209行 SyntaxError
    spawn_lock_monitor 导入失败
    evolution_score.json 已过期
    
    Health score: 100/100
    HEARTBEAT_OK
    """
    
    candidates = parser.parse(test_text)
    print(f"Found {len(candidates)} candidates:")
    for c in candidates:
        print(f"  - {c.source_type}: {c.raw_text[:50]}")
