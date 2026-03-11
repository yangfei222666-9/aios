"""
GitHub_Researcher 日常运行脚本 v1.0

受控日常运行配置：
- 固定频率：每日一次
- 固定输出格式：三段 markdown（架构启发 + 差距判断 + 可执行建议）
- 固定写回位置：memory/YYYY-MM-DD.md + agent_execution_record.jsonl
- 5 项观察指标：执行时间、输出质量、写回完整性、错误率、资源消耗

观察期：3 天
验收标准：
- ✅ 连续 3 天稳定执行
- ✅ 输出质量不漂
- ✅ 写回不断
- ✅ 耗时无异常漂移
- ✅ 5 项观察指标正常
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from run_github_researcher import run_github_researcher

# 数据目录
DATA_DIR = AIOS_ROOT / "data"
DAILY_LOG = DATA_DIR / "github_researcher_daily.jsonl"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)


def log_daily_run(record: dict):
    """记录每日运行到 github_researcher_daily.jsonl"""
    with open(DAILY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_daily_task_input():
    """
    生成每日任务输入
    
    每日关注主题轮换：
    - 周一：Agent System
    - 周二：Self-Improving
    - 周三：Multi-Agent
    - 周四：Skill / Tool Use
    - 周五：Memory / Scheduler
    - 周六：Observability / Runtime
    - 周日：综合回顾
    """
    
    weekday = datetime.now().weekday()
    
    topics = {
        0: {  # 周一
            "query": "Agent System Architecture",
            "focus": ["Agent", "System", "Architecture", "Orchestration"]
        },
        1: {  # 周二
            "query": "Self-Improving AI Systems",
            "focus": ["Self-Improving", "Learning", "Evolution", "Adaptation"]
        },
        2: {  # 周三
            "query": "Multi-Agent Collaboration",
            "focus": ["Multi-Agent", "Collaboration", "Coordination", "Communication"]
        },
        3: {  # 周四
            "query": "Agent Skill Tool Use",
            "focus": ["Skill", "Tool", "Plugin", "Extension"]
        },
        4: {  # 周五
            "query": "Agent Memory Scheduler",
            "focus": ["Memory", "Scheduler", "State", "Context"]
        },
        5: {  # 周六
            "query": "Agent Observability Runtime",
            "focus": ["Observability", "Runtime", "Monitoring", "Debugging"]
        },
        6: {  # 周日
            "query": "AIOS Personal AI Operating System",
            "focus": ["AIOS", "Personal", "Operating System", "Integration"]
        }
    }
    
    return topics.get(weekday, topics[0])


def run_daily():
    """执行每日运行"""
    
    print("=" * 60)
    print("GitHub_Researcher 日常运行")
    print("=" * 60)
    print()
    
    # 1. 生成任务输入
    task_input = get_daily_task_input()
    task_input["limit"] = 3  # 每日分析 3 个项目
    
    print(f"今日主题: {task_input['query']}")
    print(f"关注点: {', '.join(task_input['focus'])}")
    print()
    
    # 2. 记录开始时间
    start_time = datetime.now()
    
    # 3. 执行
    result = run_github_researcher(task_input)
    
    # 4. 记录结束时间
    end_time = datetime.now()
    
    # 5. 计算观察指标
    metrics = {
        "date": start_time.strftime('%Y-%m-%d'),
        "weekday": start_time.strftime('%A'),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_sec": result["duration_sec"],
        "outcome": result["outcome"],
        "output_path": result.get("output_path"),
        "error": result.get("error"),
        
        # 5 项观察指标
        "metrics": {
            "execution_time": result["duration_sec"],
            "output_quality": "pending_review",  # 需要人工评估
            "writeback_complete": result["output_path"] is not None,
            "error_occurred": result["outcome"] == "failed",
            "resource_usage": "normal"  # 简化版，后续可增加实际监控
        }
    }
    
    # 6. 记录到日志
    log_daily_run(metrics)
    
    # 7. 输出总结
    print()
    print("=" * 60)
    print("日常运行完成")
    print("=" * 60)
    print()
    print(f"日期: {metrics['date']} ({metrics['weekday']})")
    print(f"结果: {metrics['outcome']}")
    print(f"耗时: {metrics['duration_sec']:.2f}s")
    print()
    print("观察指标:")
    print(f"  执行时间: {metrics['metrics']['execution_time']:.2f}s")
    print(f"  输出质量: {metrics['metrics']['output_quality']}")
    print(f"  写回完整: {metrics['metrics']['writeback_complete']}")
    print(f"  发生错误: {metrics['metrics']['error_occurred']}")
    print(f"  资源消耗: {metrics['metrics']['resource_usage']}")
    print()
    
    if result["outcome"] == "success":
        print(f"✅ 输出已写回: {result['output_path']}")
    else:
        print(f"❌ 执行失败: {result['error']}")
    
    print()
    
    return metrics


if __name__ == "__main__":
    metrics = run_daily()
    
    # 输出 JSON 格式（便于自动化处理）
    print()
    print("=== JSON 输出 ===")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
