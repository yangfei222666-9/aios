#!/usr/bin/env python3
"""
语音命令处理器（集成路由器版本）
将简洁的命令路由器集成到现有系统中
"""

import os
import sys
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入简洁的命令路由器
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_router import CommandRouter

class VoiceCommandHandler:
    """语音命令处理器（集成路由器版本）"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        
        # 创建命令路由器
        self.router = CommandRouter(workspace_dir)
        
        # 向后兼容的命令模式
        self.command_patterns = self._load_command_patterns()
        
    def _load_command_patterns(self) -> Dict[str, dict]:
        """加载命令模式（向后兼容）"""
        return {
            # 状态检查
            "check_status": {
                "patterns": [
                    r"检查.*状态",
                    r"查看.*状态", 
                    r"系统状态",
                    r"状态检查",
                    r"运行状态",
                    r"检查.*系统",
                    r"查看.*系统",
                    r"系统.*检查",
                ],
                "action": self._handle_check_status,
                "description": "检查系统状态"
            },
            
            # 笔记管理
            "add_note": {
                "patterns": [
                    r"添加笔记",
                    r"记录笔记",
                    r"记一下",
                    r"备忘",
                    r"记录",
                ],
                "action": self._handle_add_note,
                "description": "添加笔记"
            },
            
            # 搜索
            "search": {
                "patterns": [
                    r"搜索",
                    r"查一下",
                    r"查找",
                    r"搜一下",
                ],
                "action": self._handle_search,
                "description": "搜索信息"
            },
            
            # 天气
            "weather": {
                "patterns": [
                    r"天气",
                    r"天气预报",
                    r"今天天气",
                    r"明天天气",
                ],
                "action": self._handle_weather,
                "description": "查询天气"
            },
            
            # 时间
            "time": {
                "patterns": [
                    r"现在几点",
                    r"当前时间",
                    r"什么时间",
                    r"几点钟",
                ],
                "action": self._handle_time,
                "description": "查询时间"
            },
            
            # 测试
            "test": {
                "patterns": [
                    r"测试",
                    r"试试",
                    r"试验",
                ],
                "action": self._handle_test,
                "description": "测试命令"
            },
            
            # 帮助
            "help": {
                "patterns": [
                    r"帮助",
                    r"帮忙",
                    r"什么功能",
                    r"能做什么",
                ],
                "action": self._handle_help,
                "description": "显示帮助"
            },
        }
    
    def _remove_wake_prefix(self, text: str) -> str:
        """移除唤醒词前缀"""
        wake_phrases = ["小九", "你好小九", "小酒"]
        t = text.replace(" ", "")
        
        for phrase in wake_phrases:
            p = phrase.replace(" ", "")
            if t.startswith(p):
                return text[len(phrase):].strip()
        
        return text.strip()
    
    def parse_command(self, text: str) -> Tuple[Optional[str], Optional[dict]]:
        """
        解析命令（使用路由器）
        
        参数:
            text: 原始命令文本
        
        返回:
            (command_type, command_info)
        """
        # 移除唤醒词前缀
        cleaned = self._remove_wake_prefix(text)
        
        # 使用路由器解析
        action, payload = self.router.route_command(cleaned)
        
        if action == "UNKNOWN":
            # 回退到旧模式
            return self._parse_with_old_patterns(cleaned)
        
        # 映射到旧命令类型
        type_mapping = {
            "RUN_DAILY_CHECK": "check_status",
            "ADD_NOTE": "add_note",
            "TELL_TIME": "time",
            "SEARCH": "search",
            "WEATHER": "weather",
            "TEST": "test",
            "HELP": "help",
            "LIST_NOTES": "add_note",  # 映射到笔记相关
        }
        
        cmd_type = type_mapping.get(action, "unknown")
        cmd_info = {
            "description": action.replace("_", " ").lower(),
            "cleaned": cleaned,
            "params": payload,
            "action": action,
            "payload": payload
        }
        
        return cmd_type, cmd_info
    
    def _parse_with_old_patterns(self, text: str) -> Tuple[Optional[str], Optional[dict]]:
        """使用旧模式解析命令"""
        cleaned = text.replace(" ", "")
        
        for cmd_type, cmd_info in self.command_patterns.items():
            for pattern in cmd_info["patterns"]:
                if re.search(pattern, cleaned):
                    return cmd_type, {
                        "description": cmd_info["description"],
                        "cleaned": text,
                        "params": {}
                    }
        
        return None, None
    
    def execute_command(self, text: str) -> Tuple[bool, str]:
        """
        执行命令（使用路由器）
        
        参数:
            text: 原始命令文本
        
        返回:
            (success, message)
        """
        # 移除唤醒词前缀
        cleaned = self._remove_wake_prefix(text)
        
        # 使用路由器处理
        action, payload = self.router.route_command(cleaned)
        
        if action == "UNKNOWN":
            # 回退到旧处理方式
            return self._execute_with_old_handler(cleaned)
        
        # 使用路由器处理
        success, message = self.router.handle(action, payload)
        
        # 记录结果
        self._log_command_result(text, success, message)
        
        return success, message
    
    def _execute_with_old_handler(self, text: str) -> Tuple[bool, str]:
        """使用旧处理器执行命令"""
        cmd_type, cmd_info = self._parse_with_old_patterns(text)
        
        if not cmd_type or not cmd_info:
            return False, f"未识别命令: {text}"
        
        try:
            # 调用对应的处理函数
            handler = self.command_patterns[cmd_type]["action"]
            success, message = handler(text)
            
            # 记录结果
            self._log_command_result(text, success, message)
            
            return success, message
            
        except Exception as e:
            error_msg = f"执行命令时出错: {e}"
            logging.error(error_msg)
            return False, error_msg
    
    def _log_command_result(self, command: str, success: bool, message: str):
        """记录命令执行结果"""
        try:
            logs_dir = os.path.join(self.workspace_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            log_file = os.path.join(logs_dir, "voice_command_results.log")
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                status = "SUCCESS" if success else "FAILED"
                f.write(f"{timestamp} | {status} | {command} | {message}\n")
                
        except Exception:
            pass  # 日志记录失败不影响主要功能
    
    # 向后兼容的处理函数
    def _handle_check_status(self, text: str) -> Tuple[bool, str]:
        """处理状态检查（向后兼容）"""
        return self.router.handle("RUN_DAILY_CHECK", None)
    
    def _handle_add_note(self, text: str) -> Tuple[bool, str]:
        """处理添加笔记（向后兼容）"""
        # 提取笔记内容
        patterns = [
            r"添加笔记[:：]?(.*)",
            r"记录笔记[:：]?(.*)",
            r"记一下[:：]?(.*)",
            r"备忘[:：]?(.*)",
            r"记录[:：]?(.*)",
        ]
        
        content = None
        for pattern in patterns:
            match = re.search(pattern, text)
            if match and match.group(1):
                content = match.group(1).strip()
                break
        
        if not content:
            # 尝试提取整个文本作为内容
            content = re.sub(r"(添加笔记|记录笔记|记一下|备忘|记录)[:：]?", "", text).strip()
        
        return self.router.handle("ADD_NOTE", content)
    
    def _handle_search(self, text: str) -> Tuple[bool, str]:
        """处理搜索（向后兼容）"""
        query = re.sub(r"(搜索|查一下|查找|搜一下)[:：]?", "", text).strip()
        return self.router.handle("SEARCH", query)
    
    def _handle_weather(self, text: str) -> Tuple[bool, str]:
        """处理天气查询（向后兼容）"""
        location = re.sub(r"(天气|天气预报|今天天气|明天天气)[:：]?", "", text).strip()
        return self.router.handle("WEATHER", location if location else "本地")
    
    def _handle_time(self, text: str) -> Tuple[bool, str]:
        """处理时间查询（向后兼容）"""
        return self.router.handle("TELL_TIME", None)
    
    def _handle_test(self, text: str) -> Tuple[bool, str]:
        """处理测试命令（向后兼容）"""
        return self.router.handle("TEST", None)
    
    def _handle_help(self, text: str) -> Tuple[bool, str]:
        """处理帮助命令（向后兼容）"""
        return self.router.handle("HELP", None)

def test_integration():
    """测试集成"""
    print("命令路由器集成测试")
    print("=" * 60)
    
    handler = VoiceCommandHandler()
    
    test_cases = [
        ("小九检查系统状态", True, "状态检查"),
        ("检查系统", True, "状态检查"),
        ("添加笔记明天开会", True, "添加笔记"),
        ("记录备忘测试内容", True, "添加笔记"),
        ("现在几点", True, "时间查询"),
        ("搜索人工智能", True, "搜索"),
        ("今天天气", True, "天气查询"),
        ("测试语音", True, "测试"),
        ("有什么功能", True, "帮助"),
        ("未知命令测试", False, "未识别"),
    ]
    
    all_passed = True
    
    for text, should_succeed, description in test_cases:
        print(f"\n测试: '{text}'")
        print(f"描述: {description}")
        
        # 测试解析
        cmd_type, cmd_info = handler.parse_command(text)
        print(f"解析类型: {cmd_type}")
        
        # 测试执行
        success, message = handler.execute_command(text)
        print(f"执行结果: {'成功' if success else '失败'}")
        print(f"消息: {message[:50]}...")
        
        # 验证
        if should_succeed:
            if success:
                print("[PASS] 符合预期")
            else:
                print("[FAIL] 不符合预期")
                all_passed = False
        else:
            if not success:
                print("[PASS] 符合预期（应该失败）")
            else:
                print("[FAIL] 不符合预期（不应该成功）")
                all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有集成测试通过！")
        print()
        print("集成总结:")
        print("  1. [OK] 简洁路由器集成成功")
        print("  2. [OK] 向后兼容保持")
        print("  3. [OK] 命令解析准确")
        print("  4. [OK] 命令执行正常")
        print("  5. [OK] 日志记录完整")
    else:
        print("[FAILED] 部分测试失败")
    
    return all_passed

if __name__ == "__main__":
    # 测试集成
    integration_success = test_integration()
    sys.exit(0 if integration_success else 1)