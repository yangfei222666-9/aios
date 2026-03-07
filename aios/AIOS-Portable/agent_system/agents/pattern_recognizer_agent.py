"""
PatternRecognizer Agent - 模式识别Agent
集成到AIOS Agent System
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加 pattern_recognition 模块路径
pattern_recognition_path = Path(__file__).parent.parent.parent / "pattern_recognition"
sys.path.insert(0, str(pattern_recognition_path))

from pattern_recognizer import PatternRecognizerAgent as CorePatternRecognizer


class PatternRecognizerAgent:
    """模式识别Agent - AIOS集成版"""
    
    def __init__(self):
        self.name = "PatternRecognizer"
        self.description = "基于易经64卦识别系统状态并推荐策略"
        
        # 初始化核心Agent
        data_dir = Path(__file__).parent.parent.parent / "data"
        self.core_agent = CorePatternRecognizer(data_dir)
        
        # 状态
        self.last_run = None
        self.last_pattern = None
        self.alert_threshold = "critical"  # 只在critical时发送告警
    
    def run(self) -> dict:
        """
        运行模式识别
        
        Returns:
            {
                "status": "success" | "no_data" | "error",
                "pattern": "泰卦" | "否卦" | ...,
                "confidence": 0.0-1.0,
                "risk_level": "low" | "medium" | "high" | "critical",
                "strategy": {...},
                "alert": True | False,
                "message": "...",
            }
        """
        try:
            # 分析当前状态
            report = self.core_agent.analyze_current_state()
            
            if report["status"] == "no_data":
                return {
                    "status": "no_data",
                    "message": "没有足够的任务数据进行分析",
                    "alert": False,
                }
            
            # 提取关键信息
            primary_pattern = report.get("primary_pattern", {})
            pattern_name = primary_pattern.get("name")
            confidence = primary_pattern.get("confidence", 0)
            risk_level = primary_pattern.get("risk_level", "low")
            strategy = report.get("recommended_strategy", {})
            
            # 检测模式转变
            shift = self.core_agent.detect_pattern_shift()
            alert = False
            alert_message = None
            
            if shift:
                # 如果转变到高风险状态，发送告警
                to_risk = shift.get("to_risk")
                if to_risk in ["high", "critical"]:
                    alert = True
                    alert_message = f"⚠️ 系统状态转变: {shift['from_pattern']} → {shift['to_pattern']} (风险: {shift['from_risk']} → {to_risk})"
            
            # 如果当前就是critical，也发送告警
            if risk_level == "critical" and self.last_pattern != pattern_name:
                alert = True
                alert_message = f"🚨 系统进入危机状态: {pattern_name} (风险等级: {risk_level})"
            
            # 更新状态
            self.last_run = datetime.now()
            self.last_pattern = pattern_name
            
            return {
                "status": "success",
                "pattern": pattern_name,
                "confidence": confidence,
                "risk_level": risk_level,
                "strategy": strategy,
                "alert": alert,
                "alert_message": alert_message,
                "message": f"当前卦象: {pattern_name} (置信度: {confidence:.1%}, 风险: {risk_level})",
                "full_report": report,
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"模式识别失败: {e}",
                "alert": False,
            }
    
    def get_summary_report(self) -> str:
        """获取人类可读的摘要报告"""
        return self.core_agent.generate_summary_report()
    
    def get_current_strategy(self) -> dict:
        """获取当前推荐策略"""
        report = self.core_agent.analyze_current_state()
        if report["status"] == "success":
            return report.get("recommended_strategy", {})
        return {}


# 测试
if __name__ == "__main__":
    agent = PatternRecognizerAgent()
    result = agent.run()
    
    print("=== PatternRecognizer Agent 测试 ===\n")
    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")
    
    if result['status'] == 'success':
        print(f"\n当前卦象: {result['pattern']}")
        print(f"置信度: {result['confidence']:.1%}")
        print(f"风险等级: {result['risk_level']}")
        print(f"告警: {result['alert']}")
        
        if result['alert']:
            print(f"告警消息: {result['alert_message']}")
        
        print(f"\n推荐策略:")
        strategy = result['strategy']
        print(f"  优先级: {strategy.get('priority')}")
        print(f"  模型偏好: {strategy.get('model_preference')}")
        print(f"  风险容忍度: {strategy.get('risk_tolerance')}")
