"""
AIOS Heartbeat v6.0 - 集成模式识别
每小时运行一次模式识别，根据卦象调整系统策略
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "agents"))
sys.path.insert(0, str(Path(__file__).parent / "core"))

from pattern_recognizer_agent import PatternRecognizerAgent
from scheduler_enhancement import SchedulerEnhancement


class HeartbeatV6:
    """Heartbeat v6.0 - 集成模式识别"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.data_dir / "heartbeat_state.json"
        self.alerts_file = self.data_dir.parent / "alerts.jsonl"
        
        # 初始化组件
        self.pattern_agent = PatternRecognizerAgent()
        self.scheduler_enhancer = SchedulerEnhancement()
        
        # 加载状态
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """加载心跳状态"""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_pattern_check": None,
            "pattern_check_interval_hours": 1,
            "last_pattern": None,
            "pattern_change_count": 0,
        }
    
    def _save_state(self):
        """保存心跳状态"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def _should_run_pattern_check(self) -> bool:
        """判断是否应该运行模式识别"""
        last_check = self.state.get("last_pattern_check")
        if not last_check:
            return True
        
        last_check_time = datetime.fromisoformat(last_check)
        interval_hours = self.state.get("pattern_check_interval_hours", 1)
        
        return datetime.now() - last_check_time >= timedelta(hours=interval_hours)
    
    def _send_alert(self, level: str, title: str, body: str):
        """发送告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "body": body,
            "sent": False,
        }
        
        with open(self.alerts_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")
    
    def run_pattern_check(self) -> dict:
        """运行模式识别检查"""
        print("[PATTERN] Running pattern recognition...")
        
        # 运行模式识别
        result = self.pattern_agent.run()
        
        if result["status"] != "success":
            print(f"  Status: {result['status']}")
            print(f"  Message: {result['message']}")
            return result
        
        # 输出结果
        print(f"  Current Pattern: {result['pattern']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Risk Level: {result['risk_level']}")
        
        # 更新调度器策略
        self.scheduler_enhancer.update_pattern()
        strategy_summary = self.scheduler_enhancer.get_status_summary()
        print(f"  Strategy: {strategy_summary['strategy']}")
        print(f"  Model Preference: {strategy_summary['model_preference']}")
        print(f"  Risk Tolerance: {strategy_summary['risk_tolerance']}")
        
        # 检查是否需要发送告警
        if result.get("alert"):
            alert_message = result.get("alert_message")
            print(f"  [!] Alert: {alert_message}")
            
            # 发送告警
            self._send_alert(
                level="warning" if result['risk_level'] == "high" else "critical",
                title=f"系统状态变化: {result['pattern']}",
                body=alert_message,
            )
        
        # 更新状态
        last_pattern = self.state.get("last_pattern")
        if last_pattern and last_pattern != result['pattern']:
            self.state["pattern_change_count"] = self.state.get("pattern_change_count", 0) + 1
        
        self.state["last_pattern_check"] = datetime.now().isoformat()
        self.state["last_pattern"] = result['pattern']
        self._save_state()
        
        return result
    
    def run(self):
        """运行心跳检查"""
        print("AIOS Heartbeat v6.0 Started\n")
        
        # 1. 模式识别（每小时）
        if self._should_run_pattern_check():
            pattern_result = self.run_pattern_check()
            print()
        else:
            print("[PATTERN] Skipped (not yet time)")
            print()
        
        # 2. 其他心跳任务（保留原有功能）
        # TODO: 集成 v5.0 的任务队列处理
        
        print("HEARTBEAT_OK")
        print("\nHeartbeat Completed")


def main():
    """主函数"""
    heartbeat = HeartbeatV6()
    heartbeat.run()


if __name__ == "__main__":
    main()
