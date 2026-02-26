import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 读取错误分类配置
config_file = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\error_classification.json")
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    print("错误分类配置不存在")
    sys.exit(1)

# 读取最近的进化报告
reports_dir = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system\data\evolution\reports")
if reports_dir.exists():
    reports = sorted(reports_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if reports:
        with open(reports[0], 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # 分析失败任务
        traces = report.get('phases', {}).get('observe', {}).get('traces', [])
        failures = [t for t in traces if not t.get('success', True)]
        
        print(f"总任务数: {len(traces)}")
        print(f"失败任务数: {len(failures)}")
        print(f"成功率: {(len(traces) - len(failures)) / len(traces) * 100:.1f}%")
        print()
        
        # 错误分类统计
        error_categories = Counter()
        for failure in failures:
            error_msg = failure.get('error', '').lower()
            categorized = False
            
            for category, cat_config in config['error_categories'].items():
                for pattern in cat_config['patterns']:
                    if pattern.lower() in error_msg:
                        error_categories[category] += 1
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                error_categories['unknown'] += 1
        
        print("错误分类统计:")
        for category, count in error_categories.most_common():
            severity = config['error_categories'].get(category, {}).get('severity', 'unknown')
            threshold = config['monitoring']['alert_thresholds'].get(category, 999)
            status = "⚠️ 超阈值" if count >= threshold else "✅"
            print(f"  {status} {category}: {count}次 (阈值: {threshold}, 严重度: {severity})")
    else:
        print("没有找到进化报告")
else:
    print("报告目录不存在")
