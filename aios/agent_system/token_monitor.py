"""
AIOS Token Monitor v1.0

实时监控 Token 使用量，自动优化策略，避免爆炸。

核心功能：
1. 实时监控 - 每次心跳检查 Token 使用量
2. 阈值告警 - 超过预算自动告警
3. 自动优化 - 超预算时自动切换策略（降模型/减频率/批量处理）
4. 可视化报告 - 每日/每周生成报告

灵感来源：珊瑚海的 TOKEN 管理避免爆炸方案
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class TokenMonitor:
    """Token 使用监控器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化 Token Monitor
        
        Args:
            config_path: 配置文件路径（默认：token_monitor_config.json）
        """
        self.root = Path(__file__).parent
        self.config_path = config_path or self.root / 'token_monitor_config.json'
        self.usage_log = self.root / 'token_usage.jsonl'
        self.alerts_file = self.root / 'alerts.jsonl'
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化统计
        self.stats = {
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_model': {},
            'by_task_type': {},
            'last_check': None,
        }
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        default_config = {
            # 预算设置
            'budget': {
                'daily_limit': 1000000,  # 每日 Token 上限（100万）
                'weekly_limit': 5000000,  # 每周 Token 上限（500万）
                'monthly_limit': 20000000,  # 每月 Token 上限（2000万）
            },
            
            # 告警阈值
            'thresholds': {
                'warning': 0.7,  # 70% 时警告
                'critical': 0.9,  # 90% 时严重告警
            },
            
            # 自动优化策略
            'optimization': {
                'enabled': True,
                'strategies': [
                    {
                        'name': 'switch_to_cheaper_model',
                        'trigger': 0.8,  # 80% 时触发
                        'action': 'switch_model',
                        'params': {
                            'from': 'claude-opus-4-6',
                            'to': 'claude-sonnet-4-6',
                        }
                    },
                    {
                        'name': 'reduce_heartbeat_frequency',
                        'trigger': 0.85,  # 85% 时触发
                        'action': 'reduce_frequency',
                        'params': {
                            'from': 30,  # 30秒
                            'to': 60,  # 60秒
                        }
                    },
                    {
                        'name': 'batch_processing',
                        'trigger': 0.9,  # 90% 时触发
                        'action': 'enable_batch',
                        'params': {
                            'batch_size': 5,
                        }
                    },
                ],
            },
            
            # 模型价格（每1M tokens，单位：美元）
            'pricing': {
                'claude-opus-4-6': {
                    'input': 15.0,
                    'output': 75.0,
                },
                'claude-sonnet-4-6': {
                    'input': 3.0,
                    'output': 15.0,
                },
                'claude-haiku-4-5': {
                    'input': 0.8,
                    'output': 4.0,
                },
            },
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建默认配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def log_usage(self, model: str, input_tokens: int, output_tokens: int, 
                  task_type: str = 'unknown', task_id: str = None):
        """
        记录 Token 使用量
        
        Args:
            model: 模型名称
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数
            task_type: 任务类型
            task_id: 任务 ID
        """
        total_tokens = input_tokens + output_tokens
        
        # 计算成本
        pricing = self.config['pricing'].get(model, {})
        input_cost = (input_tokens / 1_000_000) * pricing.get('input', 0)
        output_cost = (output_tokens / 1_000_000) * pricing.get('output', 0)
        total_cost = input_cost + output_cost
        
        # 记录到日志
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'cost': round(total_cost, 6),
            'task_type': task_type,
            'task_id': task_id,
        }
        
        with open(self.usage_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        # 更新统计
        self.stats['total_tokens'] += total_tokens
        self.stats['total_cost'] += total_cost
        
        if model not in self.stats['by_model']:
            self.stats['by_model'][model] = {'tokens': 0, 'cost': 0.0}
        self.stats['by_model'][model]['tokens'] += total_tokens
        self.stats['by_model'][model]['cost'] += total_cost
        
        if task_type not in self.stats['by_task_type']:
            self.stats['by_task_type'][task_type] = {'tokens': 0, 'cost': 0.0}
        self.stats['by_task_type'][task_type]['tokens'] += total_tokens
        self.stats['by_task_type'][task_type]['cost'] += total_cost
    
    def check_usage(self, period: str = 'daily') -> dict:
        """
        检查 Token 使用量
        
        Args:
            period: 时间周期（daily/weekly/monthly）
        
        Returns:
            使用统计
        """
        now = datetime.now()
        
        # 确定时间范围
        if period == 'daily':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            limit = self.config['budget']['daily_limit']
        elif period == 'weekly':
            start_time = now - timedelta(days=now.weekday())
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            limit = self.config['budget']['weekly_limit']
        elif period == 'monthly':
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            limit = self.config['budget']['monthly_limit']
        else:
            raise ValueError(f"Invalid period: {period}")
        
        # 统计使用量
        total_tokens = 0
        total_cost = 0.0
        by_model = {}
        by_task_type = {}
        
        if self.usage_log.exists():
            with open(self.usage_log, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    
                    # 只统计时间范围内的
                    if entry_time < start_time:
                        continue
                    
                    total_tokens += entry['total_tokens']
                    total_cost += entry['cost']
                    
                    # 按模型统计
                    model = entry['model']
                    if model not in by_model:
                        by_model[model] = {'tokens': 0, 'cost': 0.0}
                    by_model[model]['tokens'] += entry['total_tokens']
                    by_model[model]['cost'] += entry['cost']
                    
                    # 按任务类型统计
                    task_type = entry.get('task_type', 'unknown')
                    if task_type not in by_task_type:
                        by_task_type[task_type] = {'tokens': 0, 'cost': 0.0}
                    by_task_type[task_type]['tokens'] += entry['total_tokens']
                    by_task_type[task_type]['cost'] += entry['cost']
        
        # 计算使用率
        usage_rate = total_tokens / limit if limit > 0 else 0
        
        return {
            'period': period,
            'start_time': start_time.isoformat(),
            'end_time': now.isoformat(),
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 2),
            'limit': limit,
            'usage_rate': round(usage_rate, 4),
            'remaining': max(0, limit - total_tokens),
            'by_model': by_model,
            'by_task_type': by_task_type,
        }
    
    def check_and_alert(self) -> Optional[dict]:
        """
        检查使用量并发出告警
        
        Returns:
            告警信息（如果有）
        """
        # 检查每日使用量
        daily_usage = self.check_usage('daily')
        usage_rate = daily_usage['usage_rate']
        
        thresholds = self.config['thresholds']
        
        # 判断告警级别
        alert_level = None
        if usage_rate >= thresholds['critical']:
            alert_level = 'critical'
        elif usage_rate >= thresholds['warning']:
            alert_level = 'warning'
        
        if alert_level:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'level': alert_level,
                'title': f'Token 使用量告警 ({usage_rate*100:.1f}%)',
                'body': (
                    f"每日使用量: {daily_usage['total_tokens']:,} / {daily_usage['limit']:,}\n"
                    f"使用率: {usage_rate*100:.1f}%\n"
                    f"剩余: {daily_usage['remaining']:,} tokens\n"
                    f"成本: ${daily_usage['total_cost']:.2f}"
                ),
                'sent': False,
            }
            
            # 写入告警文件
            with open(self.alerts_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert, ensure_ascii=False) + '\n')
            
            return alert
        
        return None
    
    def auto_optimize(self) -> List[dict]:
        """
        自动优化策略
        
        Returns:
            已应用的优化策略列表
        """
        if not self.config['optimization']['enabled']:
            return []
        
        # 检查每日使用量
        daily_usage = self.check_usage('daily')
        usage_rate = daily_usage['usage_rate']
        
        applied_strategies = []
        
        for strategy in self.config['optimization']['strategies']:
            if usage_rate >= strategy['trigger']:
                # 应用策略
                applied_strategies.append({
                    'name': strategy['name'],
                    'action': strategy['action'],
                    'params': strategy['params'],
                    'timestamp': datetime.now().isoformat(),
                })
        
        return applied_strategies
    
    def generate_report(self, period: str = 'daily') -> str:
        """
        生成使用报告
        
        Args:
            period: 时间周期（daily/weekly/monthly）
        
        Returns:
            报告文本
        """
        usage = self.check_usage(period)
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║  Token 使用报告 - {period.upper()}  ║
╚══════════════════════════════════════════════════════════════╝

📊 总览:
   总使用量: {usage['total_tokens']:,} tokens
   预算上限: {usage['limit']:,} tokens
   使用率: {usage['usage_rate']*100:.1f}%
   剩余: {usage['remaining']:,} tokens
   总成本: ${usage['total_cost']:.2f}

📈 按模型统计:
"""
        
        for model, stats in usage['by_model'].items():
            report += f"   {model}:\n"
            report += f"      Tokens: {stats['tokens']:,}\n"
            report += f"      Cost: ${stats['cost']:.2f}\n"
        
        report += "\n📋 按任务类型统计:\n"
        for task_type, stats in usage['by_task_type'].items():
            report += f"   {task_type}:\n"
            report += f"      Tokens: {stats['tokens']:,}\n"
            report += f"      Cost: ${stats['cost']:.2f}\n"
        
        report += "\n" + "=" * 62
        
        return report


# 全局实例
monitor = TokenMonitor()


def log_usage(model: str, input_tokens: int, output_tokens: int, 
              task_type: str = 'unknown', task_id: str = None):
    """记录 Token 使用量（全局函数）"""
    monitor.log_usage(model, input_tokens, output_tokens, task_type, task_id)


def check_usage(period: str = 'daily') -> dict:
    """检查 Token 使用量（全局函数）"""
    return monitor.check_usage(period)


def check_and_alert() -> Optional[dict]:
    """检查使用量并发出告警（全局函数）"""
    return monitor.check_and_alert()


def auto_optimize() -> List[dict]:
    """自动优化策略（全局函数）"""
    return monitor.auto_optimize()


def generate_report(period: str = 'daily') -> str:
    """生成使用报告（全局函数）"""
    return monitor.generate_report(period)


if __name__ == '__main__':
    import sys
    import io
    
    # 设置 UTF-8 输出
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # 测试
    print("Token Monitor v1.0 - Test")
    print("=" * 62)
    
    # 模拟一些使用
    log_usage('claude-opus-4-6', 1000, 500, 'code', 'task-001')
    log_usage('claude-sonnet-4-6', 2000, 1000, 'analysis', 'task-002')
    log_usage('claude-haiku-4-5', 500, 200, 'monitor', 'task-003')
    
    # 检查使用量
    usage = check_usage('daily')
    print(f"\n每日使用量: {usage['total_tokens']:,} tokens")
    print(f"使用率: {usage['usage_rate']*100:.1f}%")
    print(f"成本: ${usage['total_cost']:.2f}")
    
    # 生成报告
    report = generate_report('daily')
    print(report)
