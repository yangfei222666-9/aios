"""Health Monitor - AIOS 健康度监控"""
import json
import sys
from datetime import datetime
from pathlib import Path

# 确保能 import paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ALERTS, AGENTS_STATE, TASK_QUEUE

class HealthMonitor:
    def __init__(self):
        self.agents_file = AGENTS_STATE
        self.queue_file = TASK_QUEUE
        self.alert_file = ALERTS
        
    def check_health(self):
        """检查 AIOS 健康度"""
        print("=" * 80)
        print("Health Monitor - AIOS 健康度检查")
        print("=" * 80)
        
        health_score = 100
        issues = []
        warnings = []
        
        # 1. 检查 Agent 状态
        agent_health = self._check_agents()
        health_score -= agent_health["penalty"]
        if agent_health["issues"]:
            issues.extend(agent_health["issues"])
        if agent_health["warnings"]:
            warnings.extend(agent_health["warnings"])
        
        # 2. 检查任务队列
        queue_health = self._check_queue()
        health_score -= queue_health["penalty"]
        if queue_health["issues"]:
            issues.extend(queue_health["issues"])
        if queue_health["warnings"]:
            warnings.extend(queue_health["warnings"])
        
        # 3. 检查系统资源
        resource_health = self._check_resources()
        health_score -= resource_health["penalty"]
        if resource_health["warnings"]:
            warnings.extend(resource_health["warnings"])
        
        # 4. 生成健康度报告
        health_status = self._get_health_status(health_score)
        
        print(f"\n📊 健康度评分: {health_score}/100 ({health_status})")
        
        if issues:
            print(f"\n🚨 严重问题 ({len(issues)} 个):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️  警告 ({len(warnings)} 个):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        if not issues and not warnings:
            print("\n✓ 系统运行正常")
        
        # 5. 发送告警（如果需要）
        if health_score < 60:
            self._send_alert(health_score, issues, warnings)
        
        # 6. 保存健康度记录
        self._save_health_record(health_score, issues, warnings)
        
        print(f"\n{'=' * 80}")
    
    def _check_agents(self):
        """检查 Agent 状态"""
        penalty = 0
        issues = []
        warnings = []
        
        if not self.agents_file.exists():
            issues.append("agents.json 文件不存在")
            return {"penalty": 50, "issues": issues, "warnings": warnings}
        
        with open(self.agents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 支持两种格式：列表 或 {"agents": [...]}
        agents = data if isinstance(data, list) else data.get("agents", [])
        
        for agent in agents:
            name = agent.get("name", "unknown")
            stats = agent.get("stats", {})
            
            # 检查失败率
            success_rate = stats.get("success_rate", 0)
            if success_rate == 0 and stats.get("tasks_total", 0) > 0:
                issues.append(f"{name}: 成功率 0%（{stats.get('tasks_failed', 0)} 次失败）")
                penalty += 20
            elif success_rate < 50:
                warnings.append(f"{name}: 成功率低于 50% ({success_rate:.1f}%)")
                penalty += 10
            
            # 检查平均耗时
            avg_duration = stats.get("avg_duration", 0)
            if avg_duration > 120:
                warnings.append(f"{name}: 平均耗时过长 ({avg_duration:.1f}秒)")
                penalty += 5
        
        return {"penalty": min(penalty, 50), "issues": issues, "warnings": warnings}
    
    def _check_queue(self):
        """检查任务队列"""
        penalty = 0
        issues = []
        warnings = []
        
        if not self.queue_file.exists():
            return {"penalty": 0, "issues": issues, "warnings": warnings}
        
        tasks = []
        with open(self.queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        
        if len(pending_tasks) > 50:
            issues.append(f"任务队列堆积严重 ({len(pending_tasks)} 个待处理)")
            penalty += 30
        elif len(pending_tasks) > 20:
            warnings.append(f"任务队列较多 ({len(pending_tasks)} 个待处理)")
            penalty += 10
        
        # 检查高优先级任务
        urgent_tasks = [t for t in pending_tasks if t.get("priority") == "urgent"]
        if urgent_tasks:
            warnings.append(f"有 {len(urgent_tasks)} 个紧急任务未处理")
            penalty += 5
        
        return {"penalty": min(penalty, 40), "issues": issues, "warnings": warnings}
    
    def _check_resources(self):
        """检查系统资源"""
        penalty = 0
        warnings = []
        
        # 检查磁盘空间（简化版）
        data_dir = Path("data")
        if data_dir.exists():
            total_size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
            total_mb = total_size / (1024 * 1024)
            
            if total_mb > 1000:  # 超过 1GB
                warnings.append(f"数据目录占用空间较大 ({total_mb:.1f} MB)")
                penalty += 5
        
        return {"penalty": penalty, "warnings": warnings}
    
    def _get_health_status(self, score):
        """获取健康度状态"""
        if score >= 90:
            return "优秀 ✨"
        elif score >= 80:
            return "良好 ✓"
        elif score >= 60:
            return "一般 ⚠️"
        else:
            return "危险 🚨"
    
    def _send_alert(self, score, issues, warnings):
        """发送告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "critical" if score < 40 else "warning",
            "title": f"AIOS 健康度告警 ({score}/100)",
            "body": f"严重问题: {len(issues)} 个\n警告: {len(warnings)} 个\n\n" + 
                    "\n".join(issues[:3]) if issues else "\n".join(warnings[:3]),
            "sent": False
        }
        
        with open(self.alert_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        
        print(f"\n🔔 已生成告警通知")
    
    def _save_health_record(self, score, issues, warnings):
        """保存健康度记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "status": self._get_health_status(score),
            "issues": issues,
            "warnings": warnings
        }
        
        record_file = Path("data/health/health_records.jsonl")
        record_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(record_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    monitor = HealthMonitor()
    monitor.check_health()
