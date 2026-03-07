"""
AIOS 维护 Agent
负责定期检查、清理、备份 AIOS 系统
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

class AIOSMaintenanceAgent:
    def __init__(self):
        self.workspace = Path(r"C:\Users\A\.openclaw\workspace\aios")
        self.skills_dir = Path(r"C:\Users\A\.openclaw\workspace\skills")
        self.log_file = self.workspace / "maintenance.log"
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Windows 终端编码问题，只打印 ASCII
        try:
            print(log_entry.strip())
        except UnicodeEncodeError:
            print(log_entry.encode('ascii', 'ignore').decode('ascii').strip())
    
    def run_skill(self, skill_name, script_name):
        """运行 Skill"""
        skill_path = self.skills_dir / skill_name / script_name
        
        if not skill_path.exists():
            return {
                "ok": False,
                "result": {"error": f"Skill not found: {skill_path}"},
                "evidence": [],
                "next": []
            }
        
        try:
            result = subprocess.run(
                [r"C:\Program Files\Python312\python.exe", str(skill_path)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {
                    "ok": False,
                    "result": {"error": result.stderr},
                    "evidence": [],
                    "next": []
                }
        
        except Exception as e:
            return {
                "ok": False,
                "result": {"error": str(e)},
                "evidence": [],
                "next": []
            }
    
    def health_check(self):
        """健康检查"""
        self.log("=== 开始健康检查 ===")
        result = self.run_skill("aios-health-check", "check.py")
        
        if result["ok"]:
            self.log("[OK] 系统健康")
        else:
            issues = result["result"].get("issues", [])
            self.log(f"[WARN] 发现 {len(issues)} 个问题")
            
            for issue in issues:
                self.log(f"  - [{issue['severity']}] {issue['message']}")
                
                # 自动修复
                if issue["action"] == "cleanup_old_events":
                    self.cleanup()
                elif issue["action"] == "restart_degraded_agents":
                    self.restart_agents()
        
        return result
    
    def cleanup(self):
        """清理旧数据"""
        self.log("=== 开始清理旧数据 ===")
        result = self.run_skill("aios-cleanup", "cleanup.py")
        
        if result["ok"]:
            cleaned = result["result"].get("cleaned_count", 0)
            self.log(f"[OK] 清理完成，处理了 {cleaned} 项")
        else:
            self.log(f"[FAIL] 清理失败: {result['result'].get('error')}")
        
        return result
    
    def backup(self):
        """备份数据"""
        self.log("=== 开始备份 ===")
        result = self.run_skill("aios-backup", "backup.py")
        
        if result["ok"]:
            backup_dir = result["result"].get("backup_dir")
            count = result["result"].get("backed_up_count", 0)
            self.log(f"[OK] 备份完成，{count} 个文件 → {backup_dir}")
        else:
            self.log(f"[FAIL] 备份失败: {result['result'].get('error')}")
        
        return result
    
    def restart_agents(self):
        """重启降级的 Agent"""
        self.log("=== 重启降级 Agent ===")
        
        agents_file = self.workspace / "agent_system" / "agents.jsonl"
        if not agents_file.exists():
            self.log("⏭️ 没有 Agent 需要重启")
            return
        
        with open(agents_file, 'r', encoding='utf-8') as f:
            agents = [json.loads(line) for line in f]
        
        degraded = [a for a in agents if a.get("state") == "degraded"]
        
        for agent in degraded:
            agent_id = agent.get("id")
            self.log(f"  [SYNC] 重启 Agent: {agent_id}")
            
            # 重置状态
            agent["state"] = "idle"
            agent["error_count"] = 0
        
        # 写回
        with open(agents_file, 'w', encoding='utf-8') as f:
            for agent in agents:
                f.write(json.dumps(agent, ensure_ascii=False) + '\n')
        
        self.log(f"[OK] 重启了 {len(degraded)} 个 Agent")
    
    def run_daily_maintenance(self):
        """每日维护任务"""
        self.log("\n" + "="*50)
        self.log("开始每日维护")
        self.log("="*50)
        
        # 1. 健康检查
        health_result = self.health_check()
        
        # 2. 清理（每天）
        cleanup_result = self.cleanup()
        
        # 3. 备份（每天）
        backup_result = self.backup()
        
        # 4. 分析（每天）
        analysis_result = self.analyze()
        
        # 总结
        self.log("\n=== 维护完成 ===")
        
        all_ok = (
            health_result["ok"] and
            cleanup_result["ok"] and
            backup_result["ok"] and
            analysis_result["ok"]
        )
        
        if all_ok:
            self.log("[OK] 所有任务成功")
            return "MAINTENANCE_OK"
        else:
            self.log("[WARN] 部分任务失败，请检查日志")
            return "MAINTENANCE_PARTIAL"
    
    def analyze(self):
        """运行分析"""
        self.log("=== 开始分析 ===")
        
        # 运行 Analyst Agent
        analyst_script = self.workspace / "agent_system" / "analyst_agent.py"
        
        if not analyst_script.exists():
            self.log("⏭️ Analyst Agent 不存在")
            return {"ok": True, "result": {}, "evidence": [], "next": []}
        
        try:
            result = subprocess.run(
                [r"C:\Program Files\Python312\python.exe", "-X", "utf8", str(analyst_script)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # 忽略编码错误
                timeout=120
            )
            
            if result.returncode == 0:
                # 解析输出
                output = result.stdout.strip()
                if "ANALYSIS_INSIGHTS:" in output:
                    count = output.split("ANALYSIS_INSIGHTS:")[1].strip()
                    self.log(f"[OK] 分析完成，发现 {count} 个洞察")
                else:
                    self.log("[OK] 分析完成，无重要发现")
                
                return {"ok": True, "result": {}, "evidence": [], "next": []}
            else:
                self.log(f"[FAIL] 分析失败: {result.stderr}")
                return {"ok": False, "result": {"error": result.stderr}, "evidence": [], "next": []}
        
        except Exception as e:
            self.log(f"[FAIL] 分析失败: {str(e)}")
            return {"ok": False, "result": {"error": str(e)}, "evidence": [], "next": []}

if __name__ == "__main__":
    agent = AIOSMaintenanceAgent()
    result = agent.run_daily_maintenance()
    print(f"\n输出: {result}")
