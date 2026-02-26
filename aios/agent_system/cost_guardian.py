#!/usr/bin/env python3
"""
CostGuardian Agent - 成本守门员
监控 API 成本，自动降级和预算控制
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_collector import collect_cost

# 配置文件
CONFIG_FILE = Path(__file__).parent / "cost_config.json"
EVENTS_DIR = Path(__file__).parent / "data" / "events"

# 默认配置
DEFAULT_CONFIG = {
    "budget_daily": 1.0,  # 每日预算（美元）
    "budget_monthly": 30.0,  # 每月预算（美元）
    "alert_threshold": 0.8,  # 告警阈值（80%）
    "model_costs": {
        # 每 1M tokens 的成本（美元）
        "claude-opus-4-6": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5": {"input": 0.8, "output": 4.0}
    },
    "task_priority_models": {
        # 任务优先级对应的模型
        "critical": "claude-opus-4-6",
        "high": "claude-sonnet-4-6",
        "normal": "claude-sonnet-4-6",
        "low": "claude-haiku-4-5"
    },
    "fallback_chain": [
        # 降级链：成本从高到低
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5"
    ]
}

class CostGuardian:
    """成本守门员"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        else:
            # 创建默认配置
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            return DEFAULT_CONFIG
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        costs = self.config["model_costs"].get(model, {"input": 3.0, "output": 15.0})
        
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        
        return input_cost + output_cost
    
    def get_today_usage(self) -> Dict:
        """获取今日使用情况"""
        today = datetime.now().strftime("%Y-%m-%d")
        events_file = EVENTS_DIR / "by_date" / f"{today}.jsonl"
        
        if not events_file.exists():
            return {
                "total_cost": 0.0,
                "task_count": 0,
                "api_calls": 0,
                "by_model": {}
            }
        
        total_cost = 0.0
        task_count = 0
        api_calls = 0
        by_model = {}
        
        with open(events_file, encoding="utf-8") as f:
            for line in f:
                event = json.loads(line)
                
                if event["event_type"] == "task":
                    task_count += 1
                    if event.get("cost_usd"):
                        total_cost += event["cost_usd"]
                
                elif event["event_type"] == "api_call":
                    api_calls += 1
                    if event.get("cost_usd"):
                        total_cost += event["cost_usd"]
                        model = event.get("model", "unknown")
                        by_model[model] = by_model.get(model, 0) + event["cost_usd"]
        
        return {
            "total_cost": total_cost,
            "task_count": task_count,
            "api_calls": api_calls,
            "by_model": by_model
        }
    
    def check_budget(self) -> Dict:
        """检查预算状态"""
        usage = self.get_today_usage()
        budget_daily = self.config["budget_daily"]
        alert_threshold = self.config["alert_threshold"]
        
        remaining = budget_daily - usage["total_cost"]
        usage_percent = (usage["total_cost"] / budget_daily) * 100
        
        status = "ok"
        if usage["total_cost"] >= budget_daily:
            status = "exceeded"
        elif usage["total_cost"] >= budget_daily * alert_threshold:
            status = "warning"
        
        return {
            "status": status,
            "budget_daily": budget_daily,
            "used": usage["total_cost"],
            "remaining": remaining,
            "usage_percent": usage_percent,
            "task_count": usage["task_count"],
            "api_calls": usage["api_calls"],
            "by_model": usage["by_model"]
        }
    
    def recommend_model(self, task_priority: str, current_model: str = None) -> Dict:
        """推荐模型（基于优先级和预算）"""
        budget_status = self.check_budget()
        
        # 根据优先级获取推荐模型
        recommended = self.config["task_priority_models"].get(
            task_priority, 
            "claude-sonnet-4-6"
        )
        
        # 如果预算告警或超支，降级
        if budget_status["status"] == "exceeded":
            # 预算超支，使用最便宜的模型
            recommended = self.config["fallback_chain"][-1]
            reason = "budget_exceeded"
        
        elif budget_status["status"] == "warning":
            # 预算告警，降级一级
            if recommended in self.config["fallback_chain"]:
                idx = self.config["fallback_chain"].index(recommended)
                if idx < len(self.config["fallback_chain"]) - 1:
                    recommended = self.config["fallback_chain"][idx + 1]
                    reason = "budget_warning"
                else:
                    reason = "normal"
            else:
                reason = "normal"
        else:
            reason = "normal"
        
        return {
            "recommended_model": recommended,
            "reason": reason,
            "budget_status": budget_status["status"],
            "remaining_budget": budget_status["remaining"]
        }
    
    def should_allow_task(self, estimated_cost: float) -> Dict:
        """判断是否允许执行任务"""
        budget_status = self.check_budget()
        
        if budget_status["status"] == "exceeded":
            return {
                "allowed": False,
                "reason": "daily_budget_exceeded",
                "message": f"今日预算已用完（${budget_status['used']:.3f}/${budget_status['budget_daily']:.2f}）"
            }
        
        if budget_status["remaining"] < estimated_cost:
            return {
                "allowed": False,
                "reason": "insufficient_budget",
                "message": f"剩余预算不足（需要${estimated_cost:.3f}，剩余${budget_status['remaining']:.3f}）"
            }
        
        return {
            "allowed": True,
            "reason": "ok",
            "message": "预算充足"
        }
    
    def record_cost(self, model: str, input_tokens: int, output_tokens: int, trace_id: str = None):
        """记录成本"""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        usage = self.get_today_usage()
        
        collect_cost(
            cost_type="api",
            provider="anthropic",
            model=model,
            cost_usd=cost,
            budget_daily=self.config["budget_daily"],
            budget_used=usage["total_cost"] + cost,
            trace_id=trace_id
        )
        
        return cost
    
    def generate_report(self) -> str:
        """生成成本报告"""
        budget_status = self.check_budget()
        
        report = f"""
📊 成本报告 - {datetime.now().strftime('%Y-%m-%d')}

💰 预算状态: {budget_status['status'].upper()}
   每日预算: ${budget_status['budget_daily']:.2f}
   已使用: ${budget_status['used']:.3f} ({budget_status['usage_percent']:.1f}%)
   剩余: ${budget_status['remaining']:.3f}

📈 使用统计:
   任务数: {budget_status['task_count']}
   API调用: {budget_status['api_calls']}

💵 按模型分类:
"""
        for model, cost in budget_status['by_model'].items():
            report += f"   {model}: ${cost:.3f}\n"
        
        return report

# 便捷函数
def check_budget():
    """检查预算"""
    guardian = CostGuardian()
    return guardian.check_budget()

def recommend_model(task_priority: str):
    """推荐模型"""
    guardian = CostGuardian()
    return guardian.recommend_model(task_priority)

def calculate_cost(model: str, input_tokens: int, output_tokens: int):
    """计算成本"""
    guardian = CostGuardian()
    return guardian.calculate_cost(model, input_tokens, output_tokens)

if __name__ == "__main__":
    # 测试
    print("💰 CostGuardian Agent 测试\n")
    
    guardian = CostGuardian()
    
    # 检查预算
    print("1. 检查预算状态:")
    budget = guardian.check_budget()
    print(f"   状态: {budget['status']}")
    print(f"   已用: ${budget['used']:.3f}")
    print(f"   剩余: ${budget['remaining']:.3f}")
    
    # 推荐模型
    print("\n2. 推荐模型:")
    for priority in ["critical", "high", "normal", "low"]:
        rec = guardian.recommend_model(priority)
        print(f"   {priority}: {rec['recommended_model']} ({rec['reason']})")
    
    # 生成报告
    print("\n3. 成本报告:")
    print(guardian.generate_report())
