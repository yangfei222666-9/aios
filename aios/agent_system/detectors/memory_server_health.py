"""
Memory Server 健康检查器

检查 Memory Server (端口 7788) 的健康状态
"""

import requests
import time
from typing import Dict, Any
from datetime import datetime


class MemoryServerHealthDetector:
    """Memory Server 健康检查器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7788, timeout: int = 5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
    
    def check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            {
                "status": "healthy" | "degraded" | "down",
                "severity": "info" | "warning" | "error" | "critical",
                "response_time_ms": float,
                "error": str | None,
                "details": dict
            }
        """
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            response_time_ms = (time.time() - start_time) * 1000
            
            # 检查响应状态
            if response.status_code == 200:
                # 正常
                if response_time_ms < 100:
                    status = "healthy"
                    severity = "info"
                elif response_time_ms < 500:
                    status = "degraded"
                    severity = "warning"
                else:
                    status = "degraded"
                    severity = "error"
                
                return {
                    "status": status,
                    "severity": severity,
                    "response_time_ms": round(response_time_ms, 2),
                    "error": None,
                    "details": {
                        "status_code": response.status_code,
                        "endpoint": "/status",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            else:
                # HTTP 错误
                return {
                    "status": "degraded",
                    "severity": "error",
                    "response_time_ms": round(response_time_ms, 2),
                    "error": f"HTTP {response.status_code}",
                    "details": {
                        "status_code": response.status_code,
                        "endpoint": "/status",
                        "timestamp": datetime.now().isoformat()
                    }
                }
        
        except requests.exceptions.Timeout:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "status": "down",
                "severity": "critical",
                "response_time_ms": round(response_time_ms, 2),
                "error": "timeout",
                "details": {
                    "timeout_seconds": self.timeout,
                    "endpoint": "/status",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        except requests.exceptions.ConnectionError:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "status": "down",
                "severity": "critical",
                "response_time_ms": round(response_time_ms, 2),
                "error": "connection_refused",
                "details": {
                    "host": self.host,
                    "port": self.port,
                    "endpoint": "/status",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "status": "down",
                "severity": "critical",
                "response_time_ms": round(response_time_ms, 2),
                "error": str(e),
                "details": {
                    "exception_type": type(e).__name__,
                    "endpoint": "/status",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def generate_event(self, check_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        从检查结果生成标准事件
        
        Args:
            check_result: check() 的返回结果
        
        Returns:
            标准事件对象
        """
        status = check_result["status"]
        severity = check_result["severity"]
        error = check_result.get("error")
        response_time = check_result["response_time_ms"]
        
        # 生成摘要
        if status == "healthy":
            summary = f"Memory Server 健康 (响应时间: {response_time}ms)"
        elif status == "degraded":
            if error:
                summary = f"Memory Server 降级 ({error}, 响应时间: {response_time}ms)"
            else:
                summary = f"Memory Server 降级 (响应时间: {response_time}ms)"
        else:  # down
            summary = f"Memory Server 不可达 ({error})"
        
        # 生成建议动作
        if status == "healthy":
            suggested_action = None
        elif status == "degraded":
            suggested_action = "health_probe"
        else:  # down
            suggested_action = "create_repair_task"
        
        event = {
            "event_id": f"evt-memory-server-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "source": "memory_server_health_detector",
            "entity_type": "service",
            "entity_id": "memory_server",
            "event_type": "service_health_check",
            "severity": severity,
            "status": "detected",
            "summary": summary,
            "evidence": {
                "health_status": status,
                "response_time_ms": response_time,
                "error": error,
                "details": check_result["details"]
            },
            "suggested_action": suggested_action,
            "cooldown_key": f"service:memory_server:health_check",
            "requires_verification": status != "healthy",
            "trace_id": f"trace-memory-server-{int(time.time())}"
        }
        
        return event


def main():
    """测试 Memory Server 健康检查"""
    detector = MemoryServerHealthDetector()
    
    print("Memory Server 健康检查")
    print("=" * 60)
    
    # 执行检查
    result = detector.check()
    
    print(f"\n状态: {result['status']}")
    print(f"严重级别: {result['severity']}")
    print(f"响应时间: {result['response_time_ms']}ms")
    if result['error']:
        print(f"错误: {result['error']}")
    
    # 生成事件
    event = detector.generate_event(result)
    
    print(f"\n事件摘要: {event['summary']}")
    print(f"建议动作: {event['suggested_action']}")
    
    print("\n完整事件:")
    import json
    print(json.dumps(event, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
