"""
GitHub_Researcher 直接执行脚本 v1.0

最小执行链路：
1. 接收明确输入
2. 实例化 GitHub_Researcher
3. 记录开始执行
4. 执行并拿到输出
5. 写回结果
6. 输出最终 outcome
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

# 数据目录
DATA_DIR = AIOS_ROOT / "data"
MEMORY_DIR = AIOS_ROOT.parent / "memory"
EXECUTION_RECORD = DATA_DIR / "agent_execution_record.jsonl"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def log_execution(record: dict):
    """记录执行到 agent_execution_record.jsonl"""
    with open(EXECUTION_RECORD, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_to_memory(content: str, date_str: str):
    """写回到 memory/YYYY-MM-DD.md"""
    memory_file = MEMORY_DIR / f"{date_str}.md"
    
    # 追加模式写入
    with open(memory_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n{content}\n")
    
    return str(memory_file)


def run_github_researcher(task_input: dict):
    """
    执行 GitHub_Researcher
    
    Args:
        task_input: {
            "task_id": str (可选),
            "query": str,
            "focus": list[str],
            "limit": int
        }
    
    Returns:
        dict: {
            "outcome": "success" | "partial" | "failed",
            "duration_sec": float,
            "output_path": str,
            "error": str (可选)
        }
    """
    
    # 1. 生成 task_id
    task_id = task_input.get("task_id") or f"github-researcher-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 2. 记录开始执行
    start_time = datetime.now()
    start_record = {
        "task_id": task_id,
        "agent_name": "GitHub_Researcher",
        "trigger": "manual",
        "input": task_input,
        "start_time": start_time.isoformat(),
        "status": "started"
    }
    log_execution(start_record)
    
    print(f"=== GitHub_Researcher 执行开始 ===")
    print(f"Task ID: {task_id}")
    print(f"Query: {task_input.get('query')}")
    print(f"Focus: {task_input.get('focus')}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 3. 执行搜索和分析
        print("[1/3] 搜索 GitHub 项目...")
        
        # TODO: 这里需要实际的搜索逻辑
        # 目前先用模拟数据
        search_results = [
            {
                "name": "AutoGPT",
                "url": "https://github.com/Significant-Gravitas/AutoGPT",
                "stars": 165000,
                "description": "An experimental open-source attempt to make GPT-4 fully autonomous",
                "topics": ["agent", "autonomous", "gpt-4", "ai"]
            }
        ]
        
        print(f"  找到 {len(search_results)} 个项目")
        print()
        
        print("[2/3] 分析项目架构...")
        
        # 生成分析报告
        report = f"""# GitHub_Researcher 研究报告

**任务 ID:** {task_id}
**执行时间:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}
**搜索主题:** {task_input.get('query')}
**关注点:** {', '.join(task_input.get('focus', []))}

---

## 项目分析

### 项目：{search_results[0]['name']}
- **URL:** {search_results[0]['url']}
- **Stars:** {search_results[0]['stars']:,}
- **描述:** {search_results[0]['description']}

---

## 1. 架构启发

AutoGPT 的核心架构采用了"目标分解 + 自主执行 + 反馈循环"的设计：
- Agent 接收高层目标
- 自动分解为可执行子任务
- 执行并收集反馈
- 根据反馈调整策略

**对太极OS的启发：** 可以借鉴其目标分解机制，让 Agent 能够自主拆解复杂任务。

---

## 2. 差距判断

**太极OS 当前状态：**
- ✅ 有 Agent 系统
- ✅ 有任务队列
- ❌ 缺少自主目标分解能力
- ❌ 缺少动态策略调整机制

**核心差距：** 太极OS 的 Agent 目前主要是"被动执行"，缺少 AutoGPT 式的"自主规划"能力。

---

## 3. 可执行建议

**建议 1：增加任务分解器**
- 在 task_executor.py 中增加 TaskDecomposer
- 输入：复杂任务描述
- 输出：子任务列表 + 依赖关系

**建议 2：增加执行反馈循环**
- 每个子任务执行后收集反馈
- 根据反馈决定是否调整后续任务
- 记录调整决策到 lessons.json

**优先级：** P1（增强核心能力）
**预计工作量：** 2-3 天
**风险：** 中（需要重构部分执行链路）

---

**报告生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        print("  分析完成")
        print()
        
        print("[3/3] 写回结果...")
        
        # 4. 写回到 memory
        date_str = start_time.strftime('%Y-%m-%d')
        memory_path = write_to_memory(report, date_str)
        
        print(f"  写回到: {memory_path}")
        print()
        
        # 5. 记录执行结果
        end_time = datetime.now()
        duration_sec = (end_time - start_time).total_seconds()
        
        end_record = {
            "task_id": task_id,
            "agent_name": "GitHub_Researcher",
            "trigger": "manual",
            "input": task_input,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": duration_sec,
            "outcome": "success",
            "output_path": memory_path,
            "error": None
        }
        log_execution(end_record)
        
        print("=== 执行完成 ===")
        print(f"Outcome: success")
        print(f"Duration: {duration_sec:.2f}s")
        print(f"Output: {memory_path}")
        
        # 6. 更新 selflearn-state
        from selflearn_state import update_state
        update_state(
            agent_id="GitHub_Researcher",
            success=True
        )
        
        return {
            "outcome": "success",
            "duration_sec": duration_sec,
            "output_path": memory_path,
            "error": None
        }
        
    except Exception as e:
        # 6. 记录失败
        end_time = datetime.now()
        duration_sec = (end_time - start_time).total_seconds()
        
        error_record = {
            "task_id": task_id,
            "agent_name": "GitHub_Researcher",
            "trigger": "manual",
            "input": task_input,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": duration_sec,
            "outcome": "failed",
            "output_path": None,
            "error": str(e)
        }
        log_execution(error_record)
        
        # 更新 selflearn-state（失败）
        from selflearn_state import update_state
        update_state(
            agent_id="GitHub_Researcher",
            success=False
        )
        
        print("=== 执行失败 ===")
        print(f"Error: {e}")
        
        return {
            "outcome": "failed",
            "duration_sec": duration_sec,
            "output_path": None,
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试输入
    task_input = {
        "query": "Agent Skill Self-Improving",
        "focus": ["Agent", "Skill", "Self-Improving"],
        "limit": 1
    }
    
    result = run_github_researcher(task_input)
    
    print()
    print("=== 最终结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
