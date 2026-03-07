"""Cost Guardian - API 成本监控和预算控制"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class CostGuardian:
    def __init__(self):
        self.events_file = Path("data/events/events.jsonl")
        self.budget_file = Path("data/cost/budget.json")
        self.alert_file = Path("alerts.jsonl")
        
        # 模型价格（每 1M tokens）
        self.pricing = {
            "claude-opus-4-5": {"input": 15.0, "output": 75.0},
            "claude-opus-4-6": {"input": 15.0, "output": 75.0},
            "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
            "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
            "claude-haiku-4-5": {"input": 0.8, "output": 4.0},
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
        }
        
        # 默认预算
        self.default_budget = {
            "daily": 10.0,    # $10/天
            "weekly": 50.0,   # $50/周
            "monthly": 200.0  # $200/月
        }
    
    def check_cost(self):
        """检查成本使用情况"""
        print("=" * 80)
        print("Cost Guardian - API 成本监控")
        print("=" * 80)
        
        # 1. 加载预算
        budget = self._load_budget()
        
        # 2. 计算使用量
        usage = self._calculate_usage()
        
        # 3. 显示统计
        print(f"\n📊 成本统计:")
        print(f"  今日: ${usage['daily']:.2f} / ${budget['daily']:.2f} ({usage['daily']/budget['daily']*100:.1f}%)")
        print(f"  本周: ${usage['weekly']:.2f} / ${budget['weekly']:.2f} ({usage['weekly']/budget['weekly']*100:.1f}%)")
        print(f"  本月: ${usage['monthly']:.2f} / ${budget['monthly']:.2f} ({usage['monthly']/budget['monthly']*100:.1f}%)")
        
        # 4. 按模型分组
        print(f"\n💰 按模型分组:")
        for model, cost in sorted(usage['by_model'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {model}: ${cost:.2f}")
        
        # 5. 按 Agent 分组
        print(f"\n🤖 按 Agent 分组:")
        for agent, cost in sorted(usage['by_agent'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {agent}: ${cost:.2f}")
        
        # 6. 检查预算
        warnings = []
        if usage['daily'] > budget['daily'] * 0.8:
            warnings.append(f"今日成本接近预算 ({usage['daily']/budget['daily']*100:.1f}%)")
        if usage['weekly'] > budget['weekly'] * 0.8:
            warnings.append(f"本周成本接近预算 ({usage['weekly']/budget['weekly']*100:.1f}%)")
        if usage['monthly'] > budget['monthly'] * 0.8:
            warnings.append(f"本月成本接近预算 ({usage['monthly']/budget['monthly']*100:.1f}%)")
        
        if warnings:
            print(f"\n⚠️  预算警告:")
            for warning in warnings:
                print(f"  • {warning}")
            self._send_alert(usage, budget, warnings)
        else:
            print(f"\n✓ 成本在预算范围内")
        
        # 7. 保存记录
        self._save_cost_record(usage, budget)
        
        print(f"\n{'=' * 80}")
    
    def _load_budget(self):
        """加载预算配置"""
        if self.budget_file.exists():
            with open(self.budget_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return self.default_budget
    
    def _calculate_usage(self):
        """计算使用量"""
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        usage = {
            "daily": 0.0,
            "weekly": 0.0,
            "monthly": 0.0,
            "by_model": defaultdict(float),
            "by_agent": defaultdict(float)
        }
        
        if not self.events_file.exists():
            return usage
        
        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                event = json.loads(line)
                if event.get("type") != "llm_call":
                    continue
                
                # 解析时间
                timestamp = datetime.fromisoformat(event.get("timestamp", ""))
                event_date = timestamp.date()
                
                # 计算成本
                model = event.get("model", "")
                input_tokens = event.get("input_tokens", 0)
                output_tokens = event.get("output_tokens", 0)
                
                cost = self._calculate_cost(model, input_tokens, output_tokens)
                
                # 累加
                if event_date == today:
                    usage["daily"] += cost
                if event_date >= week_start:
                    usage["weekly"] += cost
                if event_date >= month_start:
                    usage["monthly"] += cost
                
                usage["by_model"][model] += cost
                usage["by_agent"][event.get("agent", "unknown")] += cost
        
        return usage
    
    def _calculate_cost(self, model, input_tokens, output_tokens):
        """计算单次调用成本"""
        pricing = self.pricing.get(model, {"input": 10.0, "output": 30.0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def _send_alert(self, usage, budget, warnings):
        """发送成本告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "warning",
            "title": "AIOS 成本告警",
            "body": f"今日: ${usage['daily']:.2f}/{budget['daily']:.2f}\n" +
                    f"本周: ${usage['weekly']:.2f}/{budget['weekly']:.2f}\n" +
                    f"本月: ${usage['monthly']:.2f}/{budget['monthly']:.2f}\n\n" +
                    "\n".join(warnings),
            "sent": False
        }
        
        with open(self.alert_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        
        print(f"\n🔔 已生成成本告警")
    
    def _save_cost_record(self, usage, budget):
        """保存成本记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "usage": usage,
            "budget": budget
        }
        
        record_file = Path("data/cost/cost_records.jsonl")
        record_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(record_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    guardian = CostGuardian()
    guardian.check_cost()
