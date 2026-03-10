"""
自然观察期监控脚本
每日检查 lessons.json，统计真实失败样本数量
达到阈值（每类 ≥3 个）后自动通知
"""
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent
LESSONS_FILE = BASE_DIR / "lessons.json"
STATE_FILE = BASE_DIR / "observation_state.json"

# 目标阈值
THRESHOLD_PER_TYPE = 3

# 目标错误类型
TARGET_ERROR_TYPES = [
    "api_error",
    "network_error",
    "resource_exhausted",
    "timeout",
    "dependency_error",
]

def load_lessons():
    """加载 lessons.json"""
    if not LESSONS_FILE.exists():
        return []
    with open(LESSONS_FILE, encoding='utf-8') as f:
        return json.load(f)

def classify_samples(lessons):
    """分类样本：simulated vs real production"""
    simulated = []
    real = []
    
    for l in lessons:
        source = l.get('source', 'unknown')
        if source == 'simulation' or l.get('simulation', False):
            simulated.append(l)
        elif source == 'real':
            real.append(l)
        else:
            # 默认视为真实样本（向后兼容）
            real.append(l)
    
    return simulated, real

def count_by_error_type(lessons):
    """统计每类错误的样本数"""
    error_types = [l.get('error_type', 'unknown') for l in lessons]
    return Counter(error_types)

def check_threshold(real_counts):
    """检查是否达到阈值"""
    ready_types = []
    pending_types = []
    
    for error_type in TARGET_ERROR_TYPES:
        count = real_counts.get(error_type, 0)
        if count >= THRESHOLD_PER_TYPE:
            ready_types.append((error_type, count))
        else:
            pending_types.append((error_type, count, THRESHOLD_PER_TYPE - count))
    
    return ready_types, pending_types

def generate_report():
    """生成观察期报告"""
    print("=" * 60)
    print("📊 自然观察期监控报告")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    lessons = load_lessons()
    simulated, real = classify_samples(lessons)
    
    print(f"\n总样本数: {len(lessons)}")
    print(f"  模拟样本: {len(simulated)}")
    print(f"  真实样本: {len(real)}")
    
    # 统计真实样本
    real_counts = count_by_error_type(real)
    ready_types, pending_types = check_threshold(real_counts)
    
    print(f"\n真实样本分布:")
    for error_type, count in real_counts.most_common():
        status = "✅" if count >= THRESHOLD_PER_TYPE else "⏳"
        print(f"  {status} {error_type}: {count} 个")
    
    # 达标类型
    if ready_types:
        print(f"\n✅ 已达标类型 (≥{THRESHOLD_PER_TYPE} 个):")
        for error_type, count in ready_types:
            print(f"  • {error_type}: {count} 个")
    
    # 待积累类型
    if pending_types:
        print(f"\n⏳ 待积累类型:")
        for error_type, count, needed in pending_types:
            print(f"  • {error_type}: {count}/{THRESHOLD_PER_TYPE} (还需 {needed} 个)")
    
    # 判断是否可以进入正式验证
    if len(ready_types) >= 3:
        print(f"\n🎉 观察期完成！")
        print(f"   已有 {len(ready_types)} 类错误达标，可以执行正式闭环验证。")
        action = "READY_FOR_VALIDATION"
    else:
        print(f"\n⏳ 继续观察...")
        print(f"   目标: 至少 3 类错误达标 (当前 {len(ready_types)}/3)")
        action = "CONTINUE_OBSERVATION"
    
    print("=" * 60)
    
    # 保存状态
    state = {
        "timestamp": datetime.now().isoformat(),
        "total_samples": len(lessons),
        "simulated_samples": len(simulated),
        "real_samples": len(real),
        "real_counts": dict(real_counts),
        "ready_types": [t for t, _ in ready_types],
        "pending_types": [t for t, _, _ in pending_types],
        "action": action,
    }
    
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    print(f"\n状态已保存: {STATE_FILE}")
    
    return state

def generate_markdown_report():
    """生成 Markdown 报告"""
    lessons = load_lessons()
    simulated, real = classify_samples(lessons)
    real_counts = count_by_error_type(real)
    ready_types, pending_types = check_threshold(real_counts)
    
    lines = [
        "# 自然观察期监控报告",
        "",
        f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**阈值：** 每类 ≥{THRESHOLD_PER_TYPE} 个真实样本",
        "",
        "## 样本统计",
        "",
        f"- **总样本数：** {len(lessons)}",
        f"- **模拟样本：** {len(simulated)} (不计入生产验证)",
        f"- **真实样本：** {len(real)}",
        "",
        "## 真实样本分布",
        "",
        "| 错误类型 | 样本数 | 状态 | 进度 |",
        "|---------|--------|------|------|",
    ]
    
    for error_type in TARGET_ERROR_TYPES:
        count = real_counts.get(error_type, 0)
        status = "✅ 达标" if count >= THRESHOLD_PER_TYPE else "⏳ 待积累"
        progress = f"{count}/{THRESHOLD_PER_TYPE}"
        lines.append(f"| {error_type} | {count} | {status} | {progress} |")
    
    lines.extend([
        "",
        "## 观察期状态",
        "",
    ])
    
    if len(ready_types) >= 3:
        lines.extend([
            "🎉 **观察期完成！**",
            "",
            f"已有 {len(ready_types)} 类错误达标，可以执行正式闭环验证：",
            "",
        ])
        for error_type, count in ready_types:
            lines.append(f"- ✅ {error_type}: {count} 个")
        lines.extend([
            "",
            "**下一步：** 执行正式闭环验证脚本",
        ])
    else:
        lines.extend([
            "⏳ **继续观察中...**",
            "",
            f"目标: 至少 3 类错误达标 (当前 {len(ready_types)}/3)",
            "",
            "待积累类型：",
            "",
        ])
        for error_type, count, needed in pending_types:
            lines.append(f"- {error_type}: {count}/{THRESHOLD_PER_TYPE} (还需 {needed} 个)")
    
    lines.extend([
        "",
        "---",
        "",
        "**说明：**",
        "- 模拟样本用于逻辑验证，不计入生产统计",
        "- 真实样本来自生产环境真实失败",
        "- 每类错误需要至少 3 个真实样本才能验证闭环效果",
    ])
    
    report_path = BASE_DIR / "observation_period_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Markdown 报告: {report_path}")
    return report_path

if __name__ == '__main__':
    state = generate_report()
    generate_markdown_report()
    
    # 如果达标，输出通知标记
    if state['action'] == 'READY_FOR_VALIDATION':
        print("\n🔔 ALERT: 观察期完成，可以执行正式验证")
