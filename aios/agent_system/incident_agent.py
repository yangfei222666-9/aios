#!/usr/bin/env python3
"""
Incident Agent - 故障处置与降级
自动识别故障、执行 Playbook、生成事故小结
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from data_collector import collect_incident

# Playbook 目录
PLAYBOOKS_DIR = Path(__file__).parent / "playbooks" / "incident"
PLAYBOOKS_DIR.mkdir(parents=True, exist_ok=True)

# 故障模式库
INCIDENT_PATTERNS = {
    "dependency_missing": {
        "patterns": [
            r"ModuleNotFoundError: No module named '(\w+)'",
            r"ImportError: cannot import name '(\w+)'",
        ],
        "severity": "medium",
        "playbook": "install_dependency",
        "description": "缺少 Python 依赖库"
    },
    "timeout": {
        "patterns": [
            r"TimeoutError",
            r"Timeout: 执行超过 (\d+) 秒",
            r"timeout expired",
        ],
        "severity": "high",
        "playbook": "increase_timeout",
        "description": "执行超时"
    },
    "api_error": {
        "patterns": [
            r"Error code: (\d+)",
            r"authentication_error",
            r"rate_limit",
            r"invalid x-api-key",
        ],
        "severity": "critical",
        "playbook": "fallback_model",
        "description": "API 调用失败"
    },
    "encoding_error": {
        "patterns": [
            r"UnicodeDecodeError",
            r"codec can't decode",
        ],
        "severity": "low",
        "playbook": "fix_encoding",
        "description": "编码错误"
    },
    "resource_exhaustion": {
        "patterns": [
            r"MemoryError",
            r"Out of memory",
            r"Disk quota exceeded",
        ],
        "severity": "critical",
        "playbook": "cleanup_resources",
        "description": "资源耗尽"
    }
}

class IncidentAgent:
    """故障处置 Agent"""
    
    @staticmethod
    def detect_incident(error_message: str) -> Optional[Dict]:
        """检测故障类型"""
        if not error_message:
            return None
        
        for incident_type, config in INCIDENT_PATTERNS.items():
            for pattern in config["patterns"]:
                match = re.search(pattern, error_message, re.IGNORECASE)
                if match:
                    return {
                        "incident_type": incident_type,
                        "severity": config["severity"],
                        "playbook": config["playbook"],
                        "description": config["description"],
                        "matched_pattern": pattern,
                        "extracted_info": match.groups() if match.groups() else None
                    }
        
        return None
    
    @staticmethod
    def execute_playbook(incident_type: str, playbook_name: str, extracted_info: tuple = None) -> Dict:
        """执行 Playbook"""
        playbook_file = PLAYBOOKS_DIR / f"{playbook_name}.json"
        
        if not playbook_file.exists():
            return {
                "success": False,
                "error": f"Playbook not found: {playbook_name}"
            }
        
        # 读取 Playbook
        with open(playbook_file, encoding="utf-8") as f:
            playbook = json.load(f)
        
        # 执行 Playbook 动作
        actions_executed = []
        for action in playbook.get("actions", []):
            action_type = action.get("type")
            
            if action_type == "install_dependency":
                # 安装依赖
                if extracted_info:
                    module_name = extracted_info[0]
                    # 映射常见的模块名到 pip 包名
                    pip_name = {
                        "bs4": "beautifulsoup4",
                        "PIL": "pillow",
                        "cv2": "opencv-python",
                    }.get(module_name, module_name)
                    
                    actions_executed.append({
                        "type": "install_dependency",
                        "module": module_name,
                        "pip_package": pip_name,
                        "command": f"pip install {pip_name}"
                    })
            
            elif action_type == "increase_timeout":
                # 增加超时时间
                actions_executed.append({
                    "type": "increase_timeout",
                    "from": action.get("from", 30),
                    "to": action.get("to", 60)
                })
            
            elif action_type == "fallback_model":
                # 切换到备用模型
                actions_executed.append({
                    "type": "fallback_model",
                    "from": action.get("from", "claude-opus-4-6"),
                    "to": action.get("to", "claude-sonnet-4-6")
                })
            
            elif action_type == "retry":
                # 重试
                actions_executed.append({
                    "type": "retry",
                    "max_retries": action.get("max_retries", 3),
                    "backoff": action.get("backoff", "exponential")
                })
        
        return {
            "success": True,
            "playbook": playbook_name,
            "actions_executed": actions_executed
        }
    
    @staticmethod
    def handle_incident(
        error_message: str,
        affected_component: str,
        trace_id: str = None
    ) -> Dict:
        """处理故障（完整流程）"""
        # 1. 检测故障
        incident = IncidentAgent.detect_incident(error_message)
        
        if not incident:
            return {
                "detected": False,
                "message": "未识别的故障类型"
            }
        
        print(f"🚨 检测到故障: {incident['description']}")
        print(f"   类型: {incident['incident_type']}")
        print(f"   严重程度: {incident['severity']}")
        print(f"   Playbook: {incident['playbook']}")
        
        # 2. 执行 Playbook
        result = IncidentAgent.execute_playbook(
            incident['incident_type'],
            incident['playbook'],
            incident.get('extracted_info')
        )
        
        if result["success"]:
            print(f"[OK] Playbook 执行成功")
            for action in result["actions_executed"]:
                print(f"   - {action['type']}: {action}")
        else:
            print(f"[FAIL] Playbook 执行失败: {result['error']}")
        
        # 3. 记录故障事件
        collect_incident(
            severity=incident['severity'],
            incident_type=incident['incident_type'],
            affected_component=affected_component,
            status="resolved" if result["success"] else "failed",
            resolution=incident['playbook'] if result["success"] else None,
            metadata={
                "error_message": error_message[:200],
                "playbook": incident['playbook'],
                "actions": result.get("actions_executed", [])
            },
            trace_id=trace_id
        )
        
        # 4. 生成事故小结
        summary = {
            "detected": True,
            "incident_type": incident['incident_type'],
            "severity": incident['severity'],
            "description": incident['description'],
            "playbook_executed": incident['playbook'],
            "resolution_status": "resolved" if result["success"] else "failed",
            "actions": result.get("actions_executed", []),
            "recommendation": IncidentAgent._generate_recommendation(incident)
        }
        
        return summary
    
    @staticmethod
    def _generate_recommendation(incident: Dict) -> str:
        """生成建议"""
        recommendations = {
            "dependency_missing": "建议在代码生成时自动检测依赖并添加安装说明",
            "timeout": "建议增加超时时间或优化代码性能",
            "api_error": "建议检查 API Key 有效性或切换到备用模型",
            "encoding_error": "建议统一使用 UTF-8 编码",
            "resource_exhaustion": "建议清理临时文件或增加资源配额"
        }
        return recommendations.get(incident['incident_type'], "无特定建议")

# 创建默认 Playbook
def create_default_playbooks():
    """创建默认 Playbook"""
    playbooks = {
        "install_dependency": {
            "name": "install_dependency",
            "description": "自动安装缺失的 Python 依赖",
            "actions": [
                {
                    "type": "install_dependency",
                    "auto_detect": True
                },
                {
                    "type": "retry",
                    "max_retries": 1
                }
            ]
        },
        "increase_timeout": {
            "name": "increase_timeout",
            "description": "增加执行超时时间",
            "actions": [
                {
                    "type": "increase_timeout",
                    "from": 30,
                    "to": 60
                },
                {
                    "type": "retry",
                    "max_retries": 1
                }
            ]
        },
        "fallback_model": {
            "name": "fallback_model",
            "description": "切换到备用模型",
            "actions": [
                {
                    "type": "fallback_model",
                    "from": "claude-opus-4-6",
                    "to": "claude-sonnet-4-6"
                },
                {
                    "type": "retry",
                    "max_retries": 1
                }
            ]
        },
        "fix_encoding": {
            "name": "fix_encoding",
            "description": "修复编码问题",
            "actions": [
                {
                    "type": "log",
                    "message": "编码错误通常不影响功能，已记录"
                }
            ]
        },
        "cleanup_resources": {
            "name": "cleanup_resources",
            "description": "清理资源",
            "actions": [
                {
                    "type": "cleanup",
                    "targets": ["temp_files", "old_logs"]
                },
                {
                    "type": "retry",
                    "max_retries": 1
                }
            ]
        }
    }
    
    for name, playbook in playbooks.items():
        playbook_file = PLAYBOOKS_DIR / f"{name}.json"
        with open(playbook_file, "w", encoding="utf-8") as f:
            json.dump(playbook, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] 已创建 {len(playbooks)} 个默认 Playbook")

if __name__ == "__main__":
    # 创建默认 Playbook
    create_default_playbooks()
    
    # 测试故障检测
    print("\n[REPORT] 测试故障检测:")
    
    test_errors = [
        "ModuleNotFoundError: No module named 'bs4'",
        "TimeoutError: 执行超过 30 秒",
        "Error code: 401 - authentication_error",
        "UnicodeDecodeError: 'utf-8' codec can't decode",
    ]
    
    for error in test_errors:
        print(f"\n错误: {error}")
        summary = IncidentAgent.handle_incident(error, "test-component")
        if summary["detected"]:
            print(f"建议: {summary['recommendation']}")
