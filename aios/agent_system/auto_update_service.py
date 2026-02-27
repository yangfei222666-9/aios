"""
自动回写脚本 - 监听 OpenClaw sessions 完成事件
从 sessions 历史中提取执行结果，自动更新 agents.json
"""
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess

AGENTS_FILE = Path(__file__).parent / "agents.json"
SPAWN_RESULTS = Path(__file__).parent / "spawn_results.jsonl"
PROCESSED_SESSIONS = Path(__file__).parent / "processed_sessions.json"

def load_processed_sessions():
    """加载已处理的 session 列表"""
    if not PROCESSED_SESSIONS.exists():
        return set()
    
    with open(PROCESSED_SESSIONS, encoding="utf-8") as f:
        data = json.load(f)
        return set(data.get("sessions", []))

def save_processed_session(session_key: str):
    """保存已处理的 session"""
    processed = load_processed_sessions()
    processed.add(session_key)
    
    with open(PROCESSED_SESSIONS, "w", encoding="utf-8") as f:
        json.dump({"sessions": list(processed)}, f, indent=2)

def check_pending_spawns():
    """
    检查待处理的 spawn 请求
    从 spawn_results.jsonl 中找出 status=spawned 的任务
    """
    if not SPAWN_RESULTS.exists():
        return []
    
    pending = []
    with open(SPAWN_RESULTS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            
            result = json.loads(line)
            if result.get("status") == "spawned":
                pending.append(result)
    
    return pending

def update_agent_stats(agent_name: str, success: bool, duration_seconds: float):
    """更新 Agent 统计（调用 update_agent_stats.py）"""
    cmd = [
        "C:\\Program Files\\Python312\\python.exe",
        "-X", "utf8",
        str(Path(__file__).parent / "update_agent_stats.py"),
        "--task-id", "auto",
        "--agent-id", agent_name,
        "--duration", str(duration_seconds)
    ]
    
    if success:
        cmd.append("--success")
    else:
        cmd.append("--failed")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 更新失败：{e}")
        return False

def main():
    """主循环"""
    print("=" * 60)
    print("AIOS 自动回写服务")
    print("=" * 60)
    print("监听 spawn 请求完成事件，自动更新 Agent 统计")
    print("按 Ctrl+C 停止")
    print()
    
    processed = load_processed_sessions()
    
    while True:
        try:
            # 检查待处理的 spawn
            pending = check_pending_spawns()
            
            if pending:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现 {len(pending)} 个待处理任务")
                
                for spawn in pending:
                    task_id = spawn.get("task_id")
                    agent_id = spawn.get("agent_id")
                    
                    # 这里需要从 OpenClaw 获取 session 状态
                    # 由于无法直接调用 OpenClaw API，这里只是示例
                    print(f"  - {task_id} ({agent_id}): 等待完成...")
            
            # 每 30 秒检查一次
            time.sleep(30)
        
        except KeyboardInterrupt:
            print("\n\n✅ 服务已停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
