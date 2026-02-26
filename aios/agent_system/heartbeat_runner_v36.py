#!/usr/bin/env python3
"""
AIOS 心跳运行器 v3.6 - 集成版
集成 Orchestrator、ProcessManager、结构化日志
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加路径
WORKSPACE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(WORKSPACE / "aios" / "agent_system"))

from learning_agents import LEARNING_AGENTS

# 文件路径
TASK_QUEUE = Path(__file__).parent / "task_queue.jsonl"
SPAWN_REQUESTS = Path(__file__).parent / "spawn_requests.jsonl"
SPAWN_RESULTS = Path(__file__).parent / "spawn_results.jsonl"
AGENTS_FILE = Path(__file__).parent / "data" / "agents.json"
STATE_FILE = WORKSPACE / "memory" / "selflearn-state.json"
HEARTBEAT_LOG = Path(__file__).parent / "heartbeat.log"

def structured_log(level, **kwargs):
    """结构化日志"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        **kwargs
    }
    
    # 打印到控制台
    message = kwargs.get("message", "")
    print(f"[{level.upper()}] {message}")
    
    # 写入日志文件
    with open(HEARTBEAT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def load_json(file_path):
    """加载JSON文件"""
    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    """保存JSON文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def append_jsonl(file_path, data):
    """追加到JSONL文件"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def process_task_queue():
    """处理任务队列 - 每次最多5个"""
    structured_log("info", message="📋 处理任务队列...")
    
    if not TASK_QUEUE.exists():
        structured_log("info", message="  队列为空")
        return "QUEUE_OK"
    
    with open(TASK_QUEUE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not lines:
        structured_log("info", message="  队列为空")
        return "QUEUE_OK"
    
    structured_log("info", message=f"  队列中有 {len(lines)} 个任务")
    
    processed = 0
    failed = 0
    remaining = []
    stats = {}
    
    # 路由映射
    route_map = {
        "code": "coder-dispatcher",
        "analysis": "analyst-dispatcher",
        "monitor": "monitor-dispatcher",
        "research": "researcher-dispatcher"
    }
    
    for line in lines:
        if processed >= 5:
            remaining.append(line)
            continue
        
        try:
            task = json.loads(line.strip())
            task_id = task.get("id", "unknown")
            task_type = task.get("type", "unknown")
            agent_id = route_map.get(task_type, "coder-dispatcher")
            
            structured_log("info", 
                message=f"  处理任务 {task_id}",
                type=task_type,
                agent=agent_id,
                description=task.get("description", "")[:50]
            )
            
            # 创建spawn请求
            spawn_request = {
                "task_id": task_id,
                "task_type": task_type,
                "agent_id": agent_id,
                "description": task.get("description", ""),
                "priority": task.get("priority", "normal"),
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            # 写入spawn请求
            append_jsonl(SPAWN_REQUESTS, spawn_request)
            
            # 记录结果
            result = {
                "task_id": task_id,
                "agent_id": agent_id,
                "status": "spawned",
                "spawned_at": datetime.now().isoformat()
            }
            append_jsonl(SPAWN_RESULTS, result)
            
            processed += 1
            stats[task_type] = stats.get(task_type, 0) + 1
            structured_log("info", message=f"    ✓ 已创建spawn请求")
            
        except Exception as e:
            structured_log("error", 
                message=f"  任务处理失败",
                error=str(e),
                line=line[:100]
            )
            failed += 1
            remaining.append(line)
    
    # 写回剩余任务
    if remaining:
        with open(TASK_QUEUE, "w", encoding="utf-8") as f:
            f.writelines(remaining)
    else:
        TASK_QUEUE.unlink(missing_ok=True)
    
    structured_log("info", message=f"  任务队列处理完成，本次处理 {processed} 个")
    
    # 返回结果
    if processed > 0:
        stats_str = ", ".join(f"{k}:{v}" for k, v in stats.items())
        return f"QUEUE_PROCESSED:{processed} ({stats_str})"
    elif failed > 0:
        return f"QUEUE_FAILED:{failed}"
    else:
        return "QUEUE_OK"

def activate_sleeping_learning_agents():
    """激活从未运行过的学习Agent"""
    structured_log("info", message="😴 检查休眠的学习Agent...")
    
    # 读取状态
    state = load_json(STATE_FILE)
    
    # 找出从未运行的Agent
    never_run = []
    for agent in LEARNING_AGENTS:
        name = agent["name"]
        last_run_key = f"last_{name.lower()}"
        if not state.get(last_run_key):
            never_run.append(agent)
    
    if not never_run:
        structured_log("info", message="  所有学习Agent都已运行过")
        return "LEARNING_AGENTS_OK"
    
    structured_log("info", message=f"  发现 {len(never_run)} 个从未运行的Agent")
    
    # 为每个Agent创建spawn请求
    activated = []
    for agent in never_run:
        task = f"""你是 {agent['role']}。

**目标：** {agent['goal']}

**背景：** {agent.get('backstory', '')}

**任务：**
{chr(10).join('- ' + t for t in agent.get('tasks', []))}

**要求：**
1. 记录学习内容到 memory/{datetime.now().strftime('%Y-%m-%d')}.md
2. 提取核心思路（不要只是罗列项目）
3. 对比我们的 AIOS（优势、缺口、可借鉴）
4. 给出具体的改进建议（可执行的）
"""

        request = {
            "agent_name": agent["name"],
            "task": task,
            "model": agent.get("model", "claude-sonnet-4-6"),
            "thinking": agent.get("thinking", "off"),
            "priority": agent.get("priority", "normal"),
            "created_at": datetime.now().isoformat()
        }

        append_jsonl(SPAWN_REQUESTS, request)
        
        # 更新状态
        state[f"last_{agent['name'].lower()}"] = datetime.now().isoformat()
        activated.append(agent["name"])
        structured_log("info", message=f"    ✓ {agent['name']}")
    
    # 保存状态
    save_json(STATE_FILE, state)
    
    structured_log("info", message=f"  已激活 {len(activated)} 个学习Agent")
    return f"LEARNING_AGENTS_ACTIVATED:{len(activated)}"

def handle_coder_failure():
    """Coder 连续失败处理"""
    structured_log("info", message="🔧 检查Coder状态...")
    
    # 读取agents.json
    agents_data = load_json(AGENTS_FILE)
    agents = agents_data.get("agents", [])
    
    # 找到coder-dispatcher
    coder = None
    for agent in agents:
        if agent.get("id") == "coder-dispatcher":
            coder = agent
            break
    
    if not coder:
        structured_log("warn", message="  未找到coder-dispatcher")
        return "CODER_NOT_FOUND"
    
    # 检查失败次数
    stats = coder.get("stats", {})
    failed = stats.get("tasks_failed", 0)
    completed = stats.get("tasks_completed", 0)
    
    structured_log("info", 
        message=f"  Coder统计",
        completed=completed,
        failed=failed
    )
    
    if failed < 3:
        structured_log("info", message="  Coder正常")
        return "CODER_OK"
    
    # 失败≥3次，需要修复
    structured_log("warn", message=f"  ⚠️ Coder连续失败{failed}次，应用修复...")
    
    # 修复策略
    fixes_applied = []
    
    # 1. 增加超时
    if coder.get("timeout", 60) < 120:
        coder["timeout"] = 120
        fixes_applied.append("timeout:60→120")
        structured_log("info", message="    ✓ 超时增加到120秒")
    
    # 2. 降低thinking level
    if coder.get("thinking") == "high":
        coder["thinking"] = "medium"
        fixes_applied.append("thinking:high→medium")
        structured_log("info", message="    ✓ thinking降低到medium")
    
    # 3. 增加重试次数
    if coder.get("max_retries", 3) < 5:
        coder["max_retries"] = 5
        fixes_applied.append("retries:3→5")
        structured_log("info", message="    ✓ 重试次数增加到5")
    
    # 保存修改
    if fixes_applied:
        save_json(AGENTS_FILE, agents_data)
        structured_log("info", message=f"  ✓ 已应用 {len(fixes_applied)} 个修复")
        return f"CODER_FIXED ({', '.join(fixes_applied)})"
    else:
        structured_log("warn", message="  ⚠️ 无法自动修复，需要人工介入")
        return "CODER_NEEDS_ATTENTION"

def check_self_improving_loop():
    """Self-Improving Loop 检查"""
    structured_log("info", message="🔄 检查Self-Improving Loop...")
    
    # 读取loop状态
    loop_state_file = Path(__file__).parent / "data" / "loop_state.json"
    if not loop_state_file.exists():
        structured_log("info", message="  Loop状态文件不存在")
        return "LOOP_NOT_INITIALIZED"
    
    loop_state = load_json(loop_state_file)
    improvements = loop_state.get("total_improvements", 0)
    
    structured_log("info", message=f"  总改进次数: {improvements}")
    
    if improvements > 0:
        return f"SELF_IMPROVING:+{improvements}"
    else:
        return "SELF_IMPROVING_OK"

def clean_temp_files():
    """清理临时文件"""
    structured_log("info", message="🧹 清理临时文件...")
    
    # 清理.bak文件
    bak_files = list(Path(__file__).parent.rglob("*.bak"))
    for f in bak_files:
        try:
            f.unlink()
        except:
            pass
    
    if bak_files:
        structured_log("info", message=f"  ✓ 清理了 {len(bak_files)} 个.bak文件")
    
    return "CLEANUP_OK"

def heartbeat():
    """心跳主函数"""
    start = datetime.now()
    
    print("=" * 80)
    structured_log("info", message="🚀 AIOS Heartbeat Started")
    print("=" * 80)
    
    results = []
    
    try:
        # 1. 处理任务队列（最优先）
        result = process_task_queue()
        results.append(result)
        
        # 2. 检查并启动从未运行的学习Agent
        result = activate_sleeping_learning_agents()
        results.append(result)
        
        # 3. 处理 Coder 连续失败问题
        result = handle_coder_failure()
        results.append(result)
        
        # 4. Self-Improving Loop 检查
        result = check_self_improving_loop()
        results.append(result)
        
        # 5. 清理 & 记录
        result = clean_temp_files()
        results.append(result)
        
        duration = (datetime.now() - start).total_seconds()
        
        print("=" * 80)
        structured_log("info", 
            message="✅ Heartbeat Completed",
            duration=f"{duration:.2f}s"
        )
        print("=" * 80)
        
        # 输出摘要
        summary = []
        for r in results:
            if not r.endswith("_OK"):
                summary.append(r)
        
        if summary:
            print("\n" + ", ".join(summary))
        else:
            print("\nHEARTBEAT_OK")
        
    except Exception as e:
        structured_log("error", 
            message="❌ Heartbeat失败",
            error=str(e)
        )
        import traceback
        structured_log("error", 
            message="堆栈跟踪",
            traceback=traceback.format_exc()
        )
        print(f"\nHEARTBEAT_ERROR: {e}")

if __name__ == "__main__":
    # 单次运行模式
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        heartbeat()
    else:
        # 循环模式（每30秒）
        print("AIOS 心跳运行器 v3.6 - 循环模式")
        print("按 Ctrl+C 停止")
        print()
        
        try:
            while True:
                heartbeat()
                print()
                print("等待30秒...")
                print()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n心跳已停止")
