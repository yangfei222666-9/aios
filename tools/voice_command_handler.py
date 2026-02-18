#!/usr/bin/env python3
"""
语音命令处理器
将语音命令集成到 OpenClaw 功能
"""

import os
import sys
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class VoiceCommandHandler:
    """语音命令处理器"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.command_patterns = self._load_command_patterns()
        
    def _load_command_patterns(self) -> Dict[str, dict]:
        """加载命令模式"""
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
            
            # 搜索功能
            "search": {
                "patterns": [
                    r"搜索",
                    r"查找",
                    r"查一下",
                    r"搜一下",
                ],
                "action": self._handle_search,
                "description": "搜索信息"
            },
            
            # 天气查询
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
            
            # 时间查询
            "time": {
                "patterns": [
                    r"时间",
                    r"现在几点",
                    r"当前时间",
                    r"什么时间",
                ],
                "action": self._handle_time,
                "description": "查询时间"
            },
            
            # 测试命令
            "test": {
                "patterns": [
                    r"测试",
                    r"测试语音",
                    r"测试命令",
                ],
                "action": self._handle_test,
                "description": "测试命令"
            },
            
            # 帮助命令
            "help": {
                "patterns": [
                    r"帮助",
                    r"怎么用",
                    r"有什么功能",
                    r"能做什么",
                ],
                "action": self._handle_help,
                "description": "显示帮助"
            },
        }
    
    def parse_command(self, cmd_text: str) -> Tuple[Optional[str], Optional[dict]]:
        """解析命令文本，返回命令类型和参数"""
        cmd_text = cmd_text.strip()
        if not cmd_text:
            return None, None
        
        # 移除可能的唤醒词前缀
        cleaned_text = self._remove_wake_prefix(cmd_text)
        
        # 尝试匹配命令模式
        for cmd_type, cmd_info in self.command_patterns.items():
            for pattern in cmd_info["patterns"]:
                if re.search(pattern, cleaned_text):
                    # 提取参数
                    params = self._extract_params(cleaned_text, pattern)
                    return cmd_type, {
                        "original": cmd_text,
                        "cleaned": cleaned_text,
                        "params": params,
                        "action": cmd_info["action"],
                        "description": cmd_info["description"]
                    }
        
        return None, None
    
    def _remove_wake_prefix(self, text: str) -> str:
        """移除唤醒词前缀"""
        wake_prefixes = ["小九", "小酒", "你好小九", "hi小九", "hey小九"]
        for prefix in wake_prefixes:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
        return text
    
    def _extract_params(self, text: str, pattern: str) -> Dict:
        """从命令文本中提取参数"""
        params = {}
        
        # 提取搜索关键词
        if "搜索" in pattern or "查找" in pattern:
            match = re.search(r"搜索\s*(.+)", text) or re.search(r"查找\s*(.+)", text)
            if match:
                params["query"] = match.group(1).strip()
        
        # 提取笔记内容
        elif "笔记" in pattern or "记录" in pattern:
            match = re.search(r"笔记\s*(.+)", text) or re.search(r"记录\s*(.+)", text)
            if match:
                params["content"] = match.group(1).strip()
            else:
                # 如果没有明确内容，使用整个命令
                params["content"] = text
        
        # 提取位置信息（用于天气）
        elif "天气" in pattern:
            match = re.search(r"(.+?)天气", text)
            if match:
                params["location"] = match.group(1).strip()
            else:
                params["location"] = "北京"  # 默认位置
        
        return params
    
    def execute_command(self, cmd_text: str) -> Tuple[bool, str]:
        """执行命令"""
        try:
            cmd_type, cmd_info = self.parse_command(cmd_text)
            
            if not cmd_type or not cmd_info:
                return False, f"未识别的命令: {cmd_text}"
            
            logging.info(f"执行命令: {cmd_type} - {cmd_info['description']}")
            logging.info(f"参数: {cmd_info['params']}")
            
            # 执行命令动作
            result = cmd_info["action"](cmd_info)
            
            if result:
                return True, f"命令执行成功: {cmd_info['description']}"
            else:
                return False, f"命令执行失败: {cmd_info['description']}"
                
        except Exception as e:
            logging.error(f"执行命令时出错: {e}")
            return False, f"命令执行出错: {str(e)}"
    
    # ===== 命令处理函数 =====
    
    def _handle_check_status(self, cmd_info: dict) -> bool:
        """处理状态检查命令"""
        try:
            # 运行 daily_check 脚本
            script_path = os.path.join(self.workspace_dir, "tools", "daily_check_asr_tts.py")
            
            if os.path.exists(script_path):
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    cwd=self.workspace_dir,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # 提取摘要
                    for line in result.stdout.split('\n'):
                        if 'daily_check |' in line:
                            logging.info(f"状态检查结果: {line}")
                            self._save_command_result("check_status", line)
                            return True
                else:
                    logging.error(f"状态检查失败: {result.stderr}")
            else:
                logging.warning(f"脚本不存在: {script_path}")
            
            return False
            
        except Exception as e:
            logging.error(f"状态检查出错: {e}")
            return False
    
    def _handle_add_note(self, cmd_info: dict) -> bool:
        """处理添加笔记命令"""
        try:
            content = cmd_info["params"].get("content", "")
            if not content:
                content = cmd_info["cleaned"]
            
            if not content:
                logging.warning("笔记内容为空")
                return False
            
            # 创建笔记目录
            notes_dir = os.path.join(self.workspace_dir, "notes")
            os.makedirs(notes_dir, exist_ok=True)
            
            # 笔记文件路径
            note_file = os.path.join(notes_dir, "inbox.md")
            
            # 添加时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:00+08:00")
            
            # 写入笔记
            with open(note_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"\n## {timestamp}\n")
                f.write(f"{content}\n")
            
            logging.info(f"笔记已添加: {content[:50]}...")
            self._save_command_result("add_note", f"添加笔记: {content}")
            return True
            
        except Exception as e:
            logging.error(f"添加笔记出错: {e}")
            return False
    
    def _handle_search(self, cmd_info: dict) -> bool:
        """处理搜索命令"""
        query = cmd_info["params"].get("query", "")
        if not query:
            query = cmd_info["cleaned"]
        
        if not query:
            logging.warning("搜索关键词为空")
            return False
        
        logging.info(f"搜索: {query}")
        self._save_command_result("search", f"搜索: {query}")
        
        # TODO: 实现实际的搜索功能
        # 可以调用 web_search 工具或使用其他搜索API
        
        return True
    
    def _handle_weather(self, cmd_info: dict) -> bool:
        """处理天气查询命令"""
        location = cmd_info["params"].get("location", "北京")
        
        logging.info(f"查询天气: {location}")
        self._save_command_result("weather", f"查询{location}天气")
        
        # TODO: 实现天气查询功能
        # 可以调用天气API
        
        return True
    
    def _handle_time(self, cmd_info: dict) -> bool:
        """处理时间查询命令"""
        from datetime import datetime
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"当前时间: {current_time}")
        self._save_command_result("time", f"当前时间: {current_time}")
        
        return True
    
    def _handle_test(self, cmd_info: dict) -> bool:
        """处理测试命令"""
        logging.info("测试命令执行成功")
        self._save_command_result("test", "语音命令测试成功")
        return True
    
    def _handle_help(self, cmd_info: dict) -> bool:
        """处理帮助命令"""
        help_text = "可用命令:\n"
        for cmd_type, cmd_info in self.command_patterns.items():
            help_text += f"- {cmd_info['description']}: {', '.join(cmd_info['patterns'][:2])}\n"
        
        logging.info(help_text)
        self._save_command_result("help", help_text)
        return True
    
    def _save_command_result(self, cmd_type: str, result: str):
        """保存命令结果"""
        try:
            logs_dir = os.path.join(self.workspace_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            result_file = os.path.join(logs_dir, "voice_command_results.log")
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(result_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"[{timestamp}] {cmd_type}: {result}\n")
                
        except Exception as e:
            logging.error(f"保存命令结果出错: {e}")
    
    def get_available_commands(self) -> List[str]:
        """获取可用命令列表"""
        commands = []
        for cmd_type, cmd_info in self.command_patterns.items():
            commands.append({
                "type": cmd_type,
                "description": cmd_info["description"],
                "patterns": cmd_info["patterns"][:3]  # 只显示前3个模式
            })
        return commands

def test_handler():
    """测试命令处理器"""
    handler = VoiceCommandHandler()
    
    test_commands = [
        "小九检查系统状态",
        "添加笔记明天开会",
        "搜索人工智能",
        "今天天气怎么样",
        "现在几点",
        "测试语音命令",
        "有什么功能",
        "无效命令测试",
    ]
    
    print("语音命令处理器测试")
    print("=" * 60)
    
    for cmd in test_commands:
        print(f"\n命令: '{cmd}'")
        
        cmd_type, cmd_info = handler.parse_command(cmd)
        if cmd_type and cmd_info:
            print(f"  类型: {cmd_type}")
            print(f"  描述: {cmd_info['description']}")
            print(f"  参数: {cmd_info['params']}")
            
            # 执行命令
            success, message = handler.execute_command(cmd)
            print(f"  结果: {message}")
        else:
            print("  未识别")
    
    print("\n" + "=" * 60)
    print("可用命令列表:")
    for cmd in handler.get_available_commands():
        print(f"- {cmd['description']}: {cmd['patterns']}")

if __name__ == "__main__":
    test_handler()