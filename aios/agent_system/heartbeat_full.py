#!/usr/bin/env python3
"""
AIOS 心跳运行器 v3.5
自动处理任务队列、激活休眠Agent、修复失败Agent
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
WORKSPACE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(WORKSPACE / "aios" / "agent_system"))

from learning_agents import LEARNING_AGENTS

# 文件路径
TASK_QUEUE = Path(__file__).parent / "task_queue.jsonl"
SPAWN_REQUESTS = Path(__file__).parent / "spawn_requests.jsonl"
SPAWN_RESULTS = Path(__file__).parent / "spawn_results.jsonl"
AGENTS_FILE = Path(__file__).parent / "data" / "agents.json"
AGENTS_DATA_FILE = Path(__file__).parent / "agents_data.json"
STATE_FILE = WORKSPACE / "memory" / "selflearn-state.json"
HEARTBEAT_LOG = Path(__file__).parent / "heartbeat.log"
HEARTBEAT_STATS = Path(__file__).parent / "heartbeat_stats.json"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # 写入日志文件
    with open(HEARTBEAT_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

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

def load_jsonl(file_path):
    """加载JSONL文件"""
    if not file_path.exists():
        return []
    with open(file_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def append_jsonl(file_path, data):
    """追加到JSONL文件"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def process_task_queue():
    """处理任务队列（核心函数）"""
    log("📋 处理任务队列...")
    
    # 读取队列
    tasks = load_jsonl(TASK_QUEUE)
    if not tasks:
        log("  队列为空")
        return "QUEUE_OK"
    
    log(f"  队列中有 {len(tasks)} 个任务")
    
    # 最多处理5个
    to_process = tasks[:5]
    remaining = tasks[5:]
    
    # 路由映射（直接映射到 agents.json 里的 Agent）
    route_map = {
        "code": "skill_creator",  # 代码相关 → skill_creator
        "analysis": "document_agent",  # 分析相关 → document_agent
        "monitor": "aios_health_check",  # 监控相关 → aios_health_check
        "research": "document_agent"  # 研究相关 → document_agent
    }
    
    processed = 0
    failed = 0
    stats = {}
    
    for task in to_process:
        task_id = task.get("id", "unknown")
        task_type = task.get("task_type", task.get("type", "unknown"))  # 兼容两种格式
        agent_id = route_map.get(task_type, "document_agent")  # 默认用 document_agent
        
        log(f"  处理任务 {task_id} ({task_type}) -> {agent_id}")
        
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
        
        try:
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
            log(f"    ✓ 已创建spawn请求")
            
        except Exception as e:
            failed += 1
            log(f"    ✗ 失败: {e}")
    
    # 更新队列（移除已处理的任务）
    if remaining:
        with open(TASK_QUEUE, "w", encoding="utf-8") as f:
            for task in remaining:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
    else:
        # 清空队列
        TASK_QUEUE.unlink(missing_ok=True)
    
    # 返回结果
    if processed > 0:
        stats_str = ", ".join(f"{k}:{v}" for k, v in stats.items())
        return f"QUEUE_PROCESSED:{processed} ({stats_str})"
    elif failed > 0:
        return f"QUEUE_FAILED:{failed}"
    else:
        return "QUEUE_OK"

def activate_sleeping_learning_agents():
    """激活休眠的学习Agent"""
    log("😴 检查休眠的学习Agent...")
    
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
        log("  所有学习Agent都已运行过")
        return "LEARNING_AGENTS_OK"
    
    log(f"  发现 {len(never_run)} 个从未运行的Agent")
    
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
        log(f"    ✓ {agent['name']}")
    
    # 保存状态
    save_json(STATE_FILE, state)
    
    return f"LEARNING_AGENTS_ACTIVATED:{len(activated)}"

def handle_coder_failure():
    """处理Coder连续失败"""
    log("🔧 检查Coder状态...")
    
    # 读取agents_data.json（新的动态数据）
    agents_data = load_json(AGENTS_DATA_FILE)
    agents = agents_data.get("agents", [])
    
    # 找到活跃的coder-dispatcher
    coder = None
    for agent in agents:
        if agent.get("id") == "coder-dispatcher" and agent.get("status") == "active":
            coder = agent
            break
    
    if not coder:
        log("  未找到活跃的coder-dispatcher（可能已归档）")
        return "CODER_OK"  # 没有活跃的Coder，不需要检查
    
    # 检查失败次数
    stats = coder.get("stats", {})
    failed = stats.get("tasks_failed", 0)
    completed = stats.get("tasks_completed", 0)
    
    log(f"  Coder统计: 完成{completed}, 失败{failed}")
    
    if failed < 3:
        log("  Coder正常")
        return "CODER_OK"
    
    # 失败≥3次，需要修复
    log(f"  ⚠️ Coder连续失败{failed}次，应用修复...")
    
    # 修复策略
    fixes_applied = []
    
    # 1. 增加超时
    if coder.get("timeout", 60) < 120:
        coder["timeout"] = 120
        fixes_applied.append("timeout:60→120")
        log("    ✓ 超时增加到120秒")
    
    # 2. 降低thinking level
    if coder.get("thinking") == "high":
        coder["thinking"] = "medium"
        fixes_applied.append("thinking:high→medium")
        log("    ✓ thinking降低到medium")
    
    # 3. 增加重试次数
    if coder.get("max_retries", 3) < 5:
        coder["max_retries"] = 5
        fixes_applied.append("retries:3→5")
        log("    ✓ 重试次数增加到5")
    
    # 保存修改
    if fixes_applied:
        save_json(AGENTS_FILE, agents_data)
        log(f"  ✓ 已应用 {len(fixes_applied)} 个修复")
        return f"CODER_FIXED ({', '.join(fixes_applied)})"
    else:
        log("  ⚠️ 无法自动修复，需要人工介入")
        return "CODER_NEEDS_ATTENTION"

def check_self_improving_loop():
    """检查Self-Improving Loop"""
    log("🔄 检查Self-Improving Loop...")
    
    # 读取loop状态
    loop_state_file = Path(__file__).parent / "data" / "loop_state.json"
    if not loop_state_file.exists():
        log("  Loop状态文件不存在")
        return "LOOP_NOT_INITIALIZED"
    
    loop_state = load_json(loop_state_file)
    improvements = loop_state.get("total_improvements", 0)
    
    log(f"  总改进次数: {improvements}")
    
    if improvements > 0:
        return f"SELF_IMPROVING:+{improvements}"
    else:
        return "SELF_IMPROVING_OK"

def clean_temp_files():
    """清理临时文件"""
    log("🧹 清理临时文件...")
    
    # 清理.bak文件
    bak_files = list(Path(__file__).parent.rglob("*.bak"))
    for f in bak_files:
        f.unlink()
    
    if bak_files:
        log(f"  ✓ 清理了 {len(bak_files)} 个.bak文件")
    
    return "CLEANUP_OK"

def update_stats(results):
    """更新心跳统计"""
    stats = load_json(HEARTBEAT_STATS)
    
    # 初始化
    if "total_heartbeats" not in stats:
        stats["total_heartbeats"] = 0
        stats["tasks_processed"] = 0
        stats["agents_activated"] = 0
        stats["coder_fixes"] = 0
    
    # 更新
    stats["total_heartbeats"] += 1
    stats["last_heartbeat"] = datetime.now().isoformat()
    
    # 解析结果
    for result in results:
        if result.startswith("QUEUE_PROCESSED:"):
            count = int(result.split(":")[1].split()[0])
            stats["tasks_processed"] += count
        elif result.startswith("LEARNING_AGENTS_ACTIVATED:"):
            count = int(result.split(":")[1])
            stats["agents_activated"] += count
        elif result.startswith("CODER_FIXED"):
            stats["coder_fixes"] += 1
    
    save_json(HEARTBEAT_STATS, stats)

def heartbeat():
    """心跳主函数"""
    log("=" * 80)
    log("🚀 AIOS Heartbeat Started @ " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log("=" * 80)
    
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
        
        # 更新统计
        update_stats(results)
        
        log("=" * 80)
        log("✅ Heartbeat Completed")
        log("=" * 80)
        
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
        log(f"❌ Heartbeat失败: {e}")
        import traceback
        log(traceback.format_exc())
        print(f"\nHEARTBEAT_ERROR: {e}")

if __name__ == "__main__":
    heartbeat()
