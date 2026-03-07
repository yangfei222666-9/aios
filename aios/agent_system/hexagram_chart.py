#!/usr/bin/env python3
"""
卦象变化曲线图生成器
使用 matplotlib 生成卦象变化趋势图
"""
import json
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from pathlib import Path
from datetime import datetime

# ========== 【中文字体永久修复】Windows最稳方案 ==========
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 主字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块


def generate_hexagram_chart(output_path="hexagram_chart.png"):
    """生成卦象变化曲线图"""
    history_file = Path(__file__).parent / "data" / "pattern_history.jsonl"
    
    if not history_file.exists():
        print("[WARN] No pattern history found, skipping chart generation")
        return None
    
    # 读取历史数据
    records = []
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    
    if len(records) < 2:
        print("[WARN] Not enough data for chart (need at least 2 records)")
        return None
    
    # 取最近50条
    records = records[-50:]
    
    # 提取数据
    timestamps = [r.get("timestamp", "") for r in records]
    success_rates = [r.get("success_rate", 0) * 100 for r in records]
    confidences = [r.get("confidence", 0) * 100 for r in records]
    patterns = [r.get("pattern", "") for r in records]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 图1：成功率和置信度
    ax1.plot(range(len(success_rates)), success_rates, 'b-', label='成功率', linewidth=2)
    ax1.plot(range(len(confidences)), confidences, 'r--', label='置信度', linewidth=2)
    ax1.set_ylabel('百分比 (%)')
    ax1.set_title('AIOS 卦象分析 - 成功率与置信度')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 100)
    
    # 图2：卦象变化
    # 为每个卦象分配一个数字
    unique_patterns = list(set(patterns))
    pattern_to_num = {p: i for i, p in enumerate(unique_patterns)}
    pattern_nums = [pattern_to_num[p] for p in patterns]
    
    ax2.plot(range(len(pattern_nums)), pattern_nums, 'g-', marker='o', linewidth=2, markersize=4)
    ax2.set_ylabel('卦象')
    ax2.set_xlabel('时间')
    ax2.set_title('卦象变化趋势')
    ax2.set_yticks(range(len(unique_patterns)))
    ax2.set_yticklabels(unique_patterns)
    ax2.grid(True, alpha=0.3)
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] Chart saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_hexagram_chart()
