#!/usr/bin/env python3
"""
Resource Guard - 资源保护层
为lesson-004 (resource_exhausted) 提供资源使用检查和限制

核心功能：
1. 任务执行前检查可用资源
2. 执行中监控资源使用
3. 超限时自动降级或中止
4. 支持流式处理大文件
"""

import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

class ResourceGuard:
    """资源保护器"""
    
    # 默认限制（可配置）
    DEFAULT_LIMITS = {
        "memory_percent": 80,      # 内存使用不超过80%
        "memory_mb": 6000,         # 单任务最多6GB
        "cpu_percent": 90,         # CPU使用不超过90%
        "disk_mb": 1000            # 磁盘空间至少保留1GB
    }
    
    def __init__(self, limits: Optional[Dict[str, float]] = None):
        """
        初始化资源保护器
        
        Args:
            limits: 自定义资源限制，如 {"memory_percent": 70, "memory_mb": 4000}
        """
        self.limits = {**self.DEFAULT_LIMITS, **(limits or {})}
        self.start_memory = None
        self.start_time = None
    
    def check_available_resources(self) -> Dict[str, Any]:
        """
        检查当前可用资源
        
        Returns:
            资源状态字典，包含 available (bool) 和详细信息
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # 检查是否满足限制
        checks = {
            "memory_percent": memory.percent < self.limits["memory_percent"],
            "memory_available_mb": (memory.available / 1024 / 1024) > self.limits["memory_mb"],
            "cpu_percent": cpu_percent < self.limits["cpu_percent"],
            "disk_available_mb": (disk.free / 1024 / 1024) > self.limits["disk_mb"]
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "available": all(checks.values()),
            "checks": checks,
            "current": {
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / 1024 / 1024,
                "cpu_percent": cpu_percent,
                "disk_available_mb": disk.free / 1024 / 1024
            },
            "limits": self.limits
        }
    
    def can_start_task(self, estimated_memory_mb: Optional[float] = None) -> tuple[bool, str]:
        """
        检查是否可以启动任务
        
        Args:
            estimated_memory_mb: 预估任务需要的内存（MB）
        
        Returns:
            (can_start: bool, reason: str)
        """
        status = self.check_available_resources()
        
        if not status["available"]:
            failed_checks = [k for k, v in status["checks"].items() if not v]
            return False, f"资源不足: {', '.join(failed_checks)}"
        
        # 如果提供了预估内存，检查是否足够
        if estimated_memory_mb:
            available_mb = status["current"]["memory_available_mb"]
            if available_mb < estimated_memory_mb:
                return False, f"内存不足: 需要 {estimated_memory_mb:.0f}MB, 可用 {available_mb:.0f}MB"
        
        return True, "资源充足"
    
    @contextmanager
    def monitor_task(self, task_name: str, check_interval_ops: int = 1000):
        """
        监控任务执行期间的资源使用（上下文管理器）
        
        Args:
            task_name: 任务名称
            check_interval_ops: 每N次操作检查一次资源
        
        Usage:
            with guard.monitor_task("process_file"):
                # 执行任务
                for i, item in enumerate(items):
                    process(item)
                    if i % 1000 == 0:
                        guard.check_during_task()
        """
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        self.start_time = datetime.now()
        self.task_name = task_name
        self.check_count = 0
        
        print(f"[ResourceGuard] 开始监控任务: {task_name}")
        print(f"  初始内存: {self.start_memory:.1f}MB")
        
        try:
            yield self
        finally:
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            duration = (datetime.now() - self.start_time).total_seconds()
            
            print(f"[ResourceGuard] 任务完成: {task_name}")
            print(f"  结束内存: {end_memory:.1f}MB")
            print(f"  内存增长: {end_memory - self.start_memory:.1f}MB")
            print(f"  执行时间: {duration:.1f}s")
    
    def check_during_task(self) -> bool:
        """
        任务执行期间检查资源（由任务代码定期调用）
        
        Returns:
            True if resources OK, False if should abort
        """
        self.check_count += 1
        status = self.check_available_resources()
        
        if not status["available"]:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            print(f"[ResourceGuard] ⚠️ 资源超限 (检查#{self.check_count})")
            print(f"  当前内存: {current_memory:.1f}MB")
            print(f"  系统内存: {status['current']['memory_percent']:.1f}%")
            return False
        
        return True
    
    def stream_process_file(
        self, 
        file_path: Path, 
        process_func: Callable[[str], Any],
        chunk_size: int = 8192,
        encoding: str = 'utf-8'
    ):
        """
        流式处理大文件（避免一次性加载到内存）
        
        Args:
            file_path: 文件路径
            process_func: 处理函数，接收每行/块内容
            chunk_size: 块大小（字节）
            encoding: 文件编码
        
        Yields:
            处理结果
        """
        with self.monitor_task(f"stream_process: {file_path.name}"):
            with open(file_path, 'r', encoding=encoding) as f:
                line_count = 0
                
                for line in f:
                    # 每1000行检查一次资源
                    if line_count % 1000 == 0 and line_count > 0:
                        if not self.check_during_task():
                            raise ResourceExhaustedError(
                                f"资源耗尽，已处理 {line_count} 行"
                            )
                    
                    result = process_func(line)
                    line_count += 1
                    yield result
    
    def batch_process_with_limit(
        self,
        items: list,
        process_func: Callable,
        batch_size: int = 100,
        max_memory_mb: Optional[float] = None
    ):
        """
        分批处理数据（避免内存溢出）
        
        Args:
            items: 待处理项目列表
            process_func: 处理函数
            batch_size: 批次大小
            max_memory_mb: 最大内存限制（MB），超过则暂停
        
        Yields:
            处理结果
        """
        max_memory_mb = max_memory_mb or self.limits["memory_mb"]
        
        with self.monitor_task(f"batch_process: {len(items)} items"):
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                
                # 检查内存
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > max_memory_mb:
                    print(f"[ResourceGuard] ⚠️ 内存超限 ({current_memory:.1f}MB > {max_memory_mb:.1f}MB)")
                    print(f"  已处理: {i}/{len(items)}")
                    raise ResourceExhaustedError(
                        f"内存超限: {current_memory:.1f}MB > {max_memory_mb:.1f}MB"
                    )
                
                # 处理批次
                results = [process_func(item) for item in batch]
                yield from results
                
                # 定期检查系统资源
                if i % (batch_size * 10) == 0:
                    if not self.check_during_task():
                        raise ResourceExhaustedError(
                            f"系统资源不足，已处理 {i}/{len(items)}"
                        )

class ResourceExhaustedError(Exception):
    """资源耗尽异常"""
    pass

def demo_usage():
    """使用示例"""
    guard = ResourceGuard(limits={
        "memory_percent": 75,
        "memory_mb": 4000
    })
    
    # 1. 检查是否可以启动任务
    can_start, reason = guard.can_start_task(estimated_memory_mb=2000)
    print(f"Can start task: {can_start} - {reason}")
    
    if not can_start:
        print("❌ 资源不足，任务中止")
        return
    
    # 2. 监控任务执行
    with guard.monitor_task("demo_task"):
        # 模拟处理
        data = []
        for i in range(10000):
            data.append(f"item_{i}" * 100)
            
            # 每1000次检查资源
            if i % 1000 == 0 and i > 0:
                if not guard.check_during_task():
                    print("❌ 资源超限，任务中止")
                    break
    
    print("✅ 任务完成")

if __name__ == '__main__':
    demo_usage()
