"""
tool_registry.py - 工具注册中心

统一管理所有 Agent 工具的定义、验证、执行。

v0.1 (2026-03-14):
  - 工具注册与查询
  - JSON Schema 参数验证
  - 自动重试机制
  - 工具使用统计
"""

from __future__ import annotations
import time
import json
import jsonschema
from typing import Dict, Callable, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# 数据结构
# ══════════════════════════════════════════════════════════════

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    func: Callable
    schema: Dict[str, Any]  # JSON Schema for parameters
    tags: List[str] = field(default_factory=list)
    max_retries: int = 3
    retry_backoff: float = 1.0  # seconds
    timeout: Optional[float] = None  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含 func）"""
        d = asdict(self)
        d.pop("func", None)
        return d


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    params: Dict[str, Any]
    success: bool
    result: Any
    error: Optional[str]
    duration: float  # seconds
    retries: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ══════════════════════════════════════════════════════════════
# 工具注册中心
# ══════════════════════════════════════════════════════════════

class ToolRegistry:
    """工具注册中心 - 单例模式"""
    
    _instance: Optional[ToolRegistry] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tools: Dict[str, ToolDefinition] = {}
        self._stats = ToolStats()
        self._call_history: List[ToolCallRecord] = []
        self._initialized = True
    
    def register(self, tool: ToolDefinition) -> None:
        """注册工具"""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """注销工具"""
        self._tools.pop(name, None)
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(name)
    
    def list_all(self) -> List[ToolDefinition]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def list_by_tag(self, tag: str) -> List[ToolDefinition]:
        """按标签筛选工具"""
        return [t for t in self._tools.values() if tag in t.tags]
    
    def validate_params(self, tool_name: str, params: Dict[str, Any]) -> tuple[bool, str]:
        """验证工具参数"""
        tool = self.get(tool_name)
        if not tool:
            return False, f"Tool {tool_name} not found"
        
        try:
            jsonschema.validate(params, tool.schema)
            return True, ""
        except jsonschema.ValidationError as e:
            return False, f"Parameter validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        skip_validation: bool = False
    ) -> tuple[bool, Any, ToolCallRecord]:
        """
        执行工具（带重试）
        
        Returns:
            (success, result, call_record)
        """
        tool = self.get(tool_name)
        if not tool:
            record = ToolCallRecord(
                tool_name=tool_name,
                params=params,
                success=False,
                result=None,
                error=f"Tool {tool_name} not found",
                duration=0.0,
                retries=0
            )
            return False, None, record
        
        # 参数验证
        if not skip_validation:
            valid, error = self.validate_params(tool_name, params)
            if not valid:
                record = ToolCallRecord(
                    tool_name=tool_name,
                    params=params,
                    success=False,
                    result=None,
                    error=error,
                    duration=0.0,
                    retries=0
                )
                return False, None, record
        
        # 执行（带重试）
        start_time = time.time()
        last_error = None
        
        for attempt in range(tool.max_retries):
            try:
                result = tool.func(**params)
                duration = time.time() - start_time
                
                # 记录成功
                record = ToolCallRecord(
                    tool_name=tool_name,
                    params=params,
                    success=True,
                    result=result,
                    error=None,
                    duration=duration,
                    retries=attempt
                )
                self._record_call(record)
                return True, result, record
                
            except Exception as e:
                last_error = str(e)
                if attempt < tool.max_retries - 1:
                    # 指数退避
                    time.sleep(tool.retry_backoff * (2 ** attempt))
                    continue
        
        # 所有重试都失败
        duration = time.time() - start_time
        record = ToolCallRecord(
            tool_name=tool_name,
            params=params,
            success=False,
            result=None,
            error=last_error,
            duration=duration,
            retries=tool.max_retries
        )
        self._record_call(record)
        return False, None, record
    
    def _record_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        self._call_history.append(record)
        self._stats.record_call(
            record.tool_name,
            record.success,
            record.duration,
            record.retries
        )
    
    def get_stats(self) -> ToolStats:
        """获取统计信息"""
        return self._stats
    
    def get_call_history(self, limit: int = 100) -> List[ToolCallRecord]:
        """获取调用历史"""
        return self._call_history[-limit:]
    
    def export_stats(self, path: str) -> None:
        """导出统计信息"""
        data = {
            "tools": [t.to_dict() for t in self._tools.values()],
            "stats": self._stats.to_dict(),
            "recent_calls": [r.to_dict() for r in self._call_history[-100:]]
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ══════════════════════════════════════════════════════════════
# 工具统计
# ══════════════════════════════════════════════════════════════

class ToolStats:
    """工具使用统计"""
    
    def __init__(self):
        self.calls: Dict[str, int] = {}
        self.successes: Dict[str, int] = {}
        self.failures: Dict[str, int] = {}
        self.total_duration: Dict[str, float] = {}
        self.total_retries: Dict[str, int] = {}
    
    def record_call(self, tool_name: str, success: bool, duration: float, retries: int) -> None:
        """记录一次调用"""
        self.calls[tool_name] = self.calls.get(tool_name, 0) + 1
        
        if success:
            self.successes[tool_name] = self.successes.get(tool_name, 0) + 1
        else:
            self.failures[tool_name] = self.failures.get(tool_name, 0) + 1
        
        self.total_duration[tool_name] = self.total_duration.get(tool_name, 0.0) + duration
        self.total_retries[tool_name] = self.total_retries.get(tool_name, 0) + retries
    
    def get_success_rate(self, tool_name: str) -> float:
        """获取成功率"""
        total = self.calls.get(tool_name, 0)
        if total == 0:
            return 0.0
        return self.successes.get(tool_name, 0) / total
    
    def get_failure_rate(self, tool_name: str) -> float:
        """获取失败率"""
        return 1.0 - self.get_success_rate(tool_name)
    
    def get_avg_duration(self, tool_name: str) -> float:
        """获取平均耗时"""
        total = self.calls.get(tool_name, 0)
        if total == 0:
            return 0.0
        return self.total_duration.get(tool_name, 0.0) / total
    
    def get_avg_retries(self, tool_name: str) -> float:
        """获取平均重试次数"""
        total = self.calls.get(tool_name, 0)
        if total == 0:
            return 0.0
        return self.total_retries.get(tool_name, 0) / total
    
    def get_top_tools(self, n: int = 10) -> List[tuple[str, int]]:
        """获取最常用的 N 个工具"""
        return sorted(self.calls.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def get_worst_tools(self, n: int = 10) -> List[tuple[str, float]]:
        """获取失败率最高的 N 个工具"""
        tools_with_rate = [(name, self.get_failure_rate(name)) for name in self.calls.keys()]
        return sorted(tools_with_rate, key=lambda x: x[1], reverse=True)[:n]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_calls": sum(self.calls.values()),
            "total_successes": sum(self.successes.values()),
            "total_failures": sum(self.failures.values()),
            "by_tool": {
                name: {
                    "calls": self.calls.get(name, 0),
                    "successes": self.successes.get(name, 0),
                    "failures": self.failures.get(name, 0),
                    "success_rate": self.get_success_rate(name),
                    "avg_duration": self.get_avg_duration(name),
                    "avg_retries": self.get_avg_retries(name)
                }
                for name in self.calls.keys()
            }
        }


# ══════════════════════════════════════════════════════════════
# 便捷函数
# ══════════════════════════════════════════════════════════════

def register_tool(
    name: str,
    func: Callable,
    description: str,
    schema: Dict[str, Any],
    tags: List[str] = None,
    max_retries: int = 3,
    retry_backoff: float = 1.0
) -> None:
    """注册工具（便捷函数）"""
    tool = ToolDefinition(
        name=name,
        description=description,
        func=func,
        schema=schema,
        tags=tags or [],
        max_retries=max_retries,
        retry_backoff=retry_backoff
    )
    ToolRegistry().register(tool)


def execute_tool(tool_name: str, params: Dict[str, Any]) -> tuple[bool, Any]:
    """执行工具（便捷函数）"""
    success, result, _ = ToolRegistry().execute(tool_name, params)
    return success, result


# ══════════════════════════════════════════════════════════════
# 示例工具
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 示例：注册一个简单的工具
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    register_tool(
        name="add",
        func=add_numbers,
        description="Add two numbers",
        schema={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"}
            },
            "required": ["a", "b"]
        },
        tags=["math", "basic"]
    )
    
    # 测试调用
    success, result = execute_tool("add", {"a": 1, "b": 2})
    print(f"Success: {success}, Result: {result}")
    
    # 测试参数验证
    success, result = execute_tool("add", {"a": "not a number", "b": 2})
    print(f"Success: {success}, Result: {result}")
    
    # 查看统计
    stats = ToolRegistry().get_stats()
    print(f"Stats: {json.dumps(stats.to_dict(), indent=2)}")
