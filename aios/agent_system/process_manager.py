"""
AIOS Agent Process Manager
真实的 Agent 进程管理（启动/停止/健康检查）
"""
import subprocess
import psutil
import json
import time
import os
from datetime import datetime
from pathlib import Path

AIOS_ROOT = Path(__file__).parent.parent
PID_FILE = AIOS_ROOT / "data" / "agent_pids.json"

class AgentProcessManager:
    def __init__(self):
        self.processes = self._load_pids()
    
    def _load_pids(self):
        """加载 PID 记录"""
        if PID_FILE.exists():
            with open(PID_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_pids(self):
        """保存 PID 记录"""
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, "w", encoding='utf-8') as f:
            json.dump(self.processes, f, indent=2, ensure_ascii=False)
    
    def start_agent(self, name: str, entry_script: str = None):
        """真实启动 Agent 进程"""
        # 确定入口脚本
        if entry_script is None:
            # 优先查找 agent_system/agents/{name}/main.py
            script_path = AIOS_ROOT / "agent_system" / "agents" / name / "main.py"
            if not script_path.exists():
                # 兜底：使用默认 Agent 脚本
                script_path = AIOS_ROOT / "agent_system" / "agents" / "default_agent.py"
            if not script_path.exists():
                return {"success": False, "error": f"找不到 Agent 入口脚本: {name}"}
        else:
            script_path = Path(entry_script.format(name=name))
        
        # 日志文件
        log_dir = AIOS_ROOT / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}.log"
        
        try:
            # 启动进程
            proc = subprocess.Popen(
                [r"C:\Program Files\Python312\python.exe", "-u", str(script_path)],
                stdout=open(log_file, "a", encoding='utf-8'),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # Windows 独立进程组
            )
            
            # 记录 PID
            self.processes[name] = {
                "pid": proc.pid,
                "start_time": datetime.now().isoformat(),
                "status": "running",
                "script": str(script_path)
            }
            self._save_pids()
            
            print(f"Agent {name} 已启动，PID: {proc.pid}")
            return {"success": True, "pid": proc.pid}
        
        except Exception as e:
            print(f"启动 Agent {name} 失败: {e}")
            return {"success": False, "error": str(e)}
    
    def is_alive(self, name: str) -> bool:
        """检查进程是否存活"""
        if name not in self.processes:
            return False
        
        pid = self.processes[name].get("pid")
        try:
            return psutil.Process(pid).is_running()
        except psutil.NoSuchProcess:
            self.processes[name]["status"] = "stopped"
            self._save_pids()
            return False
    
    def stop_agent(self, name: str, timeout: int = 8):
        """优雅停止：SIGTERM → 等待清理 → 超时 SIGKILL"""
        if name not in self.processes:
            return {"success": False, "error": "Agent not found"}
        
        pid = self.processes[name]["pid"]
        
        try:
            p = psutil.Process(pid)
            print(f"发送 SIGTERM 到 {name} (PID {pid})")
            p.terminate()  # SIGTERM
            
            # 等待优雅退出
            for _ in range(timeout * 10):
                if not p.is_running():
                    self.processes[name]["status"] = "stopped"
                    self._save_pids()
                    return {"success": True, "message": "优雅退出"}
                time.sleep(0.1)
            
            # 超时强制杀死
            print(f"超时，发送 SIGKILL 到 {name}")
            p.kill()  # SIGKILL
            self.processes[name]["status"] = "stopped"
            self._save_pids()
            return {"success": True, "message": "强制终止"}
        
        except psutil.NoSuchProcess:
            self.processes[name]["status"] = "stopped"
            self._save_pids()
            return {"success": True, "message": "进程已不存在"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_status(self):
        """返回所有 Agent 实时状态"""
        status = {}
        for name in self.processes:
            status[name] = {
                **self.processes[name],
                "alive": self.is_alive(name)
            }
        return status
    
    def heartbeat(self, name: str):
        """Agent 调用此接口上报心跳"""
        if name in self.processes:
            self.processes[name]["last_heartbeat"] = datetime.now().isoformat()
            self._save_pids()
            return {"success": True}
        return {"success": False, "error": "Agent not found"}


if __name__ == "__main__":
    # 测试
    manager = AgentProcessManager()
    print("当前 Agent 状态:")
    print(json.dumps(manager.get_all_status(), indent=2, ensure_ascii=False))
