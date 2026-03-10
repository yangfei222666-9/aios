"""
deduper.py - heartbeat_alert_deduper 主入口
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from parser import HeartbeatParser
from classifier import AlertClassifier


class HeartbeatAlertDeduper:
    """Heartbeat 告警去重器"""

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or Path(__file__).parent / 'memory'
        self.memory_dir.mkdir(exist_ok=True)
        
        self.parser = HeartbeatParser()
        self.classifier = AlertClassifier()
        
        self.runs_file = self.memory_dir / 'deduper_runs.jsonl'

    def run(self, heartbeat_text: str, context_meta: Optional[Dict] = None) -> Dict:
        """
        运行去重分析
        
        Args:
            heartbeat_text: 完整 heartbeat 输出文本
            context_meta: 可选的上下文元数据
            
        Returns:
            结构化分析结果
        """
        # 生成 run_id
        run_id = f"deduper-{datetime.now().isoformat()}"

        # 1. 解析候选告警
        candidates = self.parser.parse(heartbeat_text)

        # 2. 分类
        classified = self.classifier.classify(candidates)

        # 3. 生成摘要
        summary = self._generate_summary(classified)

        # 4. 构建结果
        result = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "parsed_alerts_count": len(candidates),
            "results": [alert.to_dict() for alert in classified],
            "summary": summary,
            "context_meta": context_meta or {}
        }

        # 5. 记录运行结果
        self._save_run(result)

        return result

    def _generate_summary(self, classified) -> Dict:
        """生成摘要统计"""
        summary = {
            "new_alerts": 0,
            "recurring_old_alerts": 0,
            "suppressed_old_alerts": 0,
            "quarantined_known_issues": 0,
            "non_alert_signals": 0,
            "unknown_needs_review": 0,
            "notify_count": 0
        }

        for alert in classified:
            category = alert.category
            
            if category == 'new_alert':
                summary['new_alerts'] += 1
            elif category == 'recurring_old_alert':
                summary['recurring_old_alerts'] += 1
            elif category == 'suppressed_old_alert':
                summary['suppressed_old_alerts'] += 1
            elif category == 'quarantined_known_issue':
                summary['quarantined_known_issues'] += 1
            elif category == 'non_alert_signal':
                summary['non_alert_signals'] += 1
            elif category == 'unknown_needs_review':
                summary['unknown_needs_review'] += 1

            if alert.should_notify:
                summary['notify_count'] += 1

        return summary

    def _save_run(self, result: Dict):
        """保存运行记录"""
        with open(self.runs_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python deduper.py <heartbeat_text_file>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    # 读取输入
    with open(input_file, 'r', encoding='utf-8') as f:
        heartbeat_text = f.read()
    
    # 运行去重
    deduper = HeartbeatAlertDeduper()
    result = deduper.run(heartbeat_text)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 输出摘要
    summary = result['summary']
    print("\n=== Summary ===")
    print(f"New alerts: {summary['new_alerts']}")
    print(f"Suppressed old alerts: {summary['suppressed_old_alerts']}")
    print(f"Quarantined known issues: {summary['quarantined_known_issues']}")
    print(f"Non-alert signals: {summary['non_alert_signals']}")
    print(f"Unknown needs review: {summary['unknown_needs_review']}")
    print(f"Total notify count: {summary['notify_count']}")


if __name__ == '__main__':
    main()
