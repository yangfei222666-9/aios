#!/usr/bin/env python3
"""
DataCollector Agent - 真实数据采集
收集所有任务执行数据，为进化提供基础
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# 事件存储路径
EVENTS_DIR = Path(__file__).parent / "data" / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_FILE = EVENTS_DIR / "events.jsonl"
EVENTS_BY_DATE_DIR = EVENTS_DIR / "by_date"
EVENTS_BY_DATE_DIR.mkdir(exist_ok=True)

class DataCollector:
    """数据采集器"""
    
    @staticmethod
    def generate_trace_id(prefix: str = "task") -> str:
        """生成 trace_id"""
        timestamp = int(time.time() * 1000)
        return f"{prefix}-{timestamp}-{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def collect_task_event(
        task_id: str,
        task_type: str,
        description: str,
        priority: str,
        status: str,
        duration_ms: int,
        model: str = None,
        cost_usd: float = None,
        retry_count: int = 0,
        error_type: str = None,
        error_message: str = None,
        metadata: Dict[str, Any] = None,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """收集任务事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "task",
            "trace_id": trace_id or task_id,
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "priority": priority,
            "status": status,
            "duration_ms": duration_ms,
            "model": model,
            "cost_usd": cost_usd,
            "retry_count": retry_count,
            "error_type": error_type,
            "error_message": error_message,
            "metadata": metadata or {}
        }
        
        DataCollector._write_event(event)
        return event
    
    @staticmethod
    def collect_api_call_event(
        provider: str,
        model: str,
        endpoint: str,
        status: str,
        duration_ms: int,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = None,
        error_type: str = None,
        error_message: str = None,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """收集 API 调用事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "api_call",
            "trace_id": trace_id or DataCollector.generate_trace_id("api"),
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "status": status,
            "duration_ms": duration_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "error_type": error_type,
            "error_message": error_message
        }
        
        DataCollector._write_event(event)
        return event
    
    @staticmethod
    def collect_execution_event(
        execution_type: str,
        status: str,
        duration_ms: int,
        exit_code: int = 0,
        stdout: str = None,
        stderr: str = None,
        error_type: str = None,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """收集执行事件"""
        # 截断输出（避免日志过大）
        if stdout and len(stdout) > 1000:
            stdout = stdout[:1000] + "...(truncated)"
        if stderr and len(stderr) > 1000:
            stderr = stderr[:1000] + "...(truncated)"
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "execution",
            "trace_id": trace_id or DataCollector.generate_trace_id("exec"),
            "execution_type": execution_type,
            "status": status,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "error_type": error_type
        }
        
        DataCollector._write_event(event)
        return event
    
    @staticmethod
    def collect_incident_event(
        severity: str,
        incident_type: str,
        affected_component: str,
        status: str,
        resolution: str = None,
        duration_ms: int = 0,
        metadata: Dict[str, Any] = None,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """收集故障事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "incident",
            "trace_id": trace_id or DataCollector.generate_trace_id("incident"),
            "severity": severity,
            "incident_type": incident_type,
            "affected_component": affected_component,
            "status": status,
            "resolution": resolution,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        }
        
        DataCollector._write_event(event)
        return event
    
    @staticmethod
    def collect_cost_event(
        cost_type: str,
        provider: str,
        model: str,
        cost_usd: float,
        budget_daily: float,
        budget_used: float,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """收集成本事件"""
        budget_remaining = budget_daily - budget_used
        alert_triggered = budget_remaining < budget_daily * 0.1  # 剩余<10%告警
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "cost",
            "trace_id": trace_id or DataCollector.generate_trace_id("cost"),
            "cost_type": cost_type,
            "provider": provider,
            "model": model,
            "cost_usd": cost_usd,
            "budget_daily": budget_daily,
            "budget_used": budget_used,
            "budget_remaining": budget_remaining,
            "alert_triggered": alert_triggered
        }
        
        DataCollector._write_event(event)
        return event
    
    @staticmethod
    def _write_event(event: Dict[str, Any]):
        """写入事件到文件"""
        # 写入主文件
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        # 写入按日期分类的文件
        date = datetime.now().strftime("%Y-%m-%d")
        date_file = EVENTS_BY_DATE_DIR / f"{date}.jsonl"
        with open(date_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

# 便捷函数
def collect_task(task_id, task_type, description, priority, status, duration_ms, **kwargs):
    """便捷函数：收集任务事件"""
    return DataCollector.collect_task_event(
        task_id, task_type, description, priority, status, duration_ms, **kwargs
    )

def collect_api_call(provider, model, endpoint, status, duration_ms, **kwargs):
    """便捷函数：收集 API 调用事件"""
    return DataCollector.collect_api_call_event(
        provider, model, endpoint, status, duration_ms, **kwargs
    )

def collect_execution(execution_type, status, duration_ms, **kwargs):
    """便捷函数：收集执行事件"""
    return DataCollector.collect_execution_event(
        execution_type, status, duration_ms, **kwargs
    )

def collect_incident(severity, incident_type, affected_component, status, **kwargs):
    """便捷函数：收集故障事件"""
    return DataCollector.collect_incident_event(
        severity, incident_type, affected_component, status, **kwargs
    )

def collect_cost(cost_type, provider, model, cost_usd, budget_daily, budget_used, **kwargs):
    """便捷函数：收集成本事件"""
    return DataCollector.collect_cost_event(
        cost_type, provider, model, cost_usd, budget_daily, budget_used, **kwargs
    )

if __name__ == "__main__":
    # 测试
    print("📊 DataCollector Agent 测试")
    
    # 测试任务事件
    trace_id = DataCollector.generate_trace_id()
    collect_task(
        task_id=trace_id,
        task_type="code",
        description="写一个函数计算斐波那契数列",
        priority="normal",
        status="success",
        duration_ms=5000,
        model="claude-sonnet-4-6",
        cost_usd=0.001,
        trace_id=trace_id
    )
    
    print(f"✅ 事件已记录到: {EVENTS_FILE}")
    print(f"✅ 按日期分类: {EVENTS_BY_DATE_DIR}")
