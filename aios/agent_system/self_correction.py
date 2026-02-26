"""
Self-Correction Loop - 自我修正
职责：失败时自动分析和修复
"""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path


class SelfCorrection:
    """自我修正 - 失败分析和自动修复"""
    
    def __init__(self):
        self.correction_history = []
        
    def analyze_failure(
        self,
        step: Dict[str, Any],
        error: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析失败原因
        
        Args:
            step: 失败的步骤
            error: 错误信息
            context: 执行上下文
            
        Returns:
            分析结果
        """
        analysis = {
            "error_type": self._classify_error(error),
            "root_cause": self._identify_root_cause(error),
            "suggested_fix": None,
            "can_auto_fix": False
        }
        
        # 根据错误类型生成修复建议
        if analysis["error_type"] == "file_not_found":
            analysis["suggested_fix"] = {
                "action": "check_file_path",
                "params": self._extract_file_path(error)
            }
            analysis["can_auto_fix"] = False  # 需要用户确认
            
        elif analysis["error_type"] == "timeout":
            analysis["suggested_fix"] = {
                "action": "increase_timeout",
                "params": {"timeout": step.get("timeout", 60) * 2}
            }
            analysis["can_auto_fix"] = True
            
        elif analysis["error_type"] == "missing_params":
            analysis["suggested_fix"] = {
                "action": "add_default_params",
                "params": self._infer_params(step, context)
            }
            analysis["can_auto_fix"] = True
            
        elif analysis["error_type"] == "encoding_error":
            analysis["suggested_fix"] = {
                "action": "fix_encoding",
                "params": {"encoding": "utf-8", "errors": "ignore"}
            }
            analysis["can_auto_fix"] = True
            
        else:
            analysis["suggested_fix"] = {
                "action": "manual_intervention",
                "params": {"error": error}
            }
            analysis["can_auto_fix"] = False
        
        return analysis
    
    def apply_fix(
        self,
        step: Dict[str, Any],
        fix: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用修复
        
        Args:
            step: 原始步骤
            fix: 修复方案
            
        Returns:
            修复后的步骤
        """
        fixed_step = step.copy()
        action = fix.get("action")
        params = fix.get("params", {})
        
        if action == "increase_timeout":
            fixed_step["timeout"] = params["timeout"]
            print(f"  [FIX] 增加超时: {step.get('timeout')}s → {params['timeout']}s")
            
        elif action == "add_default_params":
            fixed_step["params"].update(params)
            print(f"  [FIX] 添加默认参数: {params}")
            
        elif action == "fix_encoding":
            if "params" not in fixed_step:
                fixed_step["params"] = {}
            fixed_step["params"]["encoding"] = params["encoding"]
            fixed_step["params"]["errors"] = params["errors"]
            print(f"  [FIX] 修复编码: {params}")
            
        else:
            print(f"  [FIX] 无法自动修复: {action}")
        
        return fixed_step
    
    def should_retry(
        self,
        step: Dict[str, Any],
        attempt: int,
        max_retries: int = 3
    ) -> bool:
        """判断是否应该重试"""
        if attempt >= max_retries:
            return False
        
        # 某些错误不值得重试
        error_type = step.get("error_type")
        if error_type in ["file_not_found", "agent_not_found"]:
            return False
        
        return True
    
    def _classify_error(self, error: str) -> str:
        """分类错误类型"""
        error_lower = error.lower()
        
        if "filenotfound" in error_lower or "no such file" in error_lower:
            return "file_not_found"
        elif "timeout" in error_lower:
            return "timeout"
        elif "missing" in error_lower or "required" in error_lower:
            return "missing_params"
        elif "encoding" in error_lower or "codec" in error_lower:
            return "encoding_error"
        elif "agent not found" in error_lower:
            return "agent_not_found"
        else:
            return "unknown"
    
    def _identify_root_cause(self, error: str) -> str:
        """识别根本原因"""
        error_type = self._classify_error(error)
        
        causes = {
            "file_not_found": "文件路径不存在或无权限访问",
            "timeout": "执行时间超过限制",
            "missing_params": "缺少必需参数",
            "encoding_error": "字符编码不兼容",
            "agent_not_found": "Agent 未注册或已禁用",
            "unknown": "未知错误"
        }
        
        return causes.get(error_type, "未知原因")
    
    def _extract_file_path(self, error: str) -> Dict[str, str]:
        """从错误信息中提取文件路径"""
        import re
        
        # 匹配常见路径格式
        patterns = [
            r"'([^']+)'",  # 单引号
            r'"([^"]+)"',  # 双引号
            r'([A-Za-z]:\\[^\s]+)',  # Windows 路径
            r'(/[^\s]+)'  # Unix 路径
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error)
            if match:
                return {"file_path": match.group(1)}
        
        return {}
    
    def _infer_params(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """推断缺失的参数"""
        inferred = {}
        
        # 根据 Agent 类型推断参数
        agent_id = step.get("agent", "")
        
        if "document" in agent_id:
            # 文档处理 Agent 需要文件路径
            # 尝试从上下文中获取
            if "file_path" in context:
                inferred["file_path"] = context["file_path"]
            else:
                inferred["file_path"] = "input.txt"  # 默认值
        
        return inferred


# 测试代码
if __name__ == "__main__":
    corrector = SelfCorrection()
    
    # 测试场景 1：文件不存在
    print("=== 测试 1：文件不存在 ===")
    step1 = {
        "agent": "document-agent",
        "action": "process",
        "params": {"file_path": "/path/to/missing.txt"},
        "timeout": 60
    }
    error1 = "FileNotFoundError: [Errno 2] No such file or directory: '/path/to/missing.txt'"
    
    analysis1 = corrector.analyze_failure(step1, error1, {})
    print(f"错误类型: {analysis1['error_type']}")
    print(f"根本原因: {analysis1['root_cause']}")
    print(f"可自动修复: {analysis1['can_auto_fix']}")
    print(f"修复建议: {analysis1['suggested_fix']}")
    
    # 测试场景 2：超时
    print("\n=== 测试 2：超时 ===")
    step2 = {
        "agent": "slow-agent",
        "action": "execute",
        "params": {},
        "timeout": 30
    }
    error2 = "TimeoutError: Agent execution timeout (30s)"
    
    analysis2 = corrector.analyze_failure(step2, error2, {})
    print(f"错误类型: {analysis2['error_type']}")
    print(f"可自动修复: {analysis2['can_auto_fix']}")
    
    if analysis2['can_auto_fix']:
        fixed_step = corrector.apply_fix(step2, analysis2['suggested_fix'])
        print(f"修复后超时: {fixed_step['timeout']}s")
    
    # 测试场景 3：编码错误
    print("\n=== 测试 3：编码错误 ===")
    step3 = {
        "agent": "text-processor",
        "action": "process",
        "params": {},
        "timeout": 60
    }
    error3 = "UnicodeEncodeError: 'gbk' codec can't encode character"
    
    analysis3 = corrector.analyze_failure(step3, error3, {})
    print(f"错误类型: {analysis3['error_type']}")
    print(f"可自动修复: {analysis3['can_auto_fix']}")
    
    if analysis3['can_auto_fix']:
        fixed_step = corrector.apply_fix(step3, analysis3['suggested_fix'])
        print(f"修复后参数: {fixed_step['params']}")
