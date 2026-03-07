"""
默认 Agent 脚本（用于测试）
"""
import time
import sys
from datetime import datetime

def main():
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "default-agent"
    
    print(f"[{datetime.now()}] Agent {agent_name} 启动")
    
    try:
        while True:
            print(f"[{datetime.now()}] Agent {agent_name} 心跳")
            time.sleep(10)
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Agent {agent_name} 收到停止信号，正在清理...")
        time.sleep(1)
        print(f"[{datetime.now()}] Agent {agent_name} 已停止")

if __name__ == "__main__":
    main()
