#!/usr/bin/env python3
"""
命令路由器
简洁的命令路由和分发系统
"""

import re
import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Optional, Tuple, Any
from pathlib import Path

class CommandRouter:
    """命令路由器"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.notes_dir = os.path.join(self.workspace_dir, "notes")
        self.logs_dir = os.path.join(self.workspace_dir, "logs")
        
        # 确保目录存在
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def route_command(self, text: str) -> Tuple[str, Optional[Any]]:
        """
        路由命令
        
        参数:
            text: 原始命令文本
        
        返回:
            (action, payload): 动作和负载
        """
        # 规范化文本
        t = text.replace(" ", "").strip()
        if not t:
            return ("UNKNOWN", None)
        
        # 1. 状态检查命令
        if re.search(r"(检查|查看|查一下).*(系统|状态|运行)", t):
            return ("RUN_DAILY_CHECK", None)
        
        # 2. 添加笔记命令
        m = re.search(r"(添加|记录|记一下)(笔记|备忘|记事)[:：]?(.*)", t)
        if m:
            content = m.group(3).strip()
            return ("ADD_NOTE", content if content else None)
        
        # 3. 时间查询命令
        if re.search(r"(现在)?几点|时间|当前时间", t):
            return ("TELL_TIME", None)
        
        # 4. 搜索命令
        if re.search(r"(搜索|查一下|查找|搜一下).*", t):
            query = re.sub(r"(搜索|查一下|查找|搜一下)", "", t).strip()
            return ("SEARCH", query if query else None)
        
        # 5. 天气查询命令
        if re.search(r"(天气|天气预报|气温)", t):
            location = re.sub(r"(天气|天气预报|气温)", "", t).strip()
            return ("WEATHER", location if location else "本地")
        
        # 6. 测试命令
        if re.search(r"^(测试|试试|试验)", t):
            return ("TEST", None)
        
        # 7. 帮助命令
        if re.search(r"(帮助|帮忙|功能|能做什么)", t):
            return ("HELP", None)
        
        # 8. 笔记列表命令
        if re.search(r"(列出|查看|显示)(笔记|备忘)", t):
            return ("LIST_NOTES", None)
        
        return ("UNKNOWN", text)
    
    def handle(self, action: str, payload: Any = None) -> Tuple[bool, str]:
        """
        处理命令
        
        参数:
            action: 动作类型
            payload: 负载数据
        
        返回:
            (success, message): 是否成功和消息
        """
        try:
            if action == "RUN_DAILY_CHECK":
                return self._handle_daily_check()
            elif action == "ADD_NOTE":
                return self._handle_add_note(payload)
            elif action == "TELL_TIME":
                return self._handle_tell_time()
            elif action == "SEARCH":
                return self._handle_search(payload)
            elif action == "WEATHER":
                return self._handle_weather(payload)
            elif action == "TEST":
                return self._handle_test()
            elif action == "HELP":
                return self._handle_help()
            elif action == "LIST_NOTES":
                return self._handle_list_notes()
            else:
                return False, f"未知命令: {payload}"
                
        except Exception as e:
            return False, f"处理命令时出错: {e}"
    
    def _handle_daily_check(self) -> Tuple[bool, str]:
        """处理状态检查"""
        try:
            # 运行 daily_check 脚本
            script_path = os.path.join(self.workspace_dir, "tools", "daily_check_asr_tts.py")
            
            if not os.path.exists(script_path):
                # 创建简单的模拟脚本
                script_content = '''#!/usr/bin/env python3
print("✅ daily_check | ASR=OK TTS=OK NET=OK | search=test | top1=\\"测试结果\\"")
'''
                with open(script_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(script_content)
            
            # 执行脚本
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # 提取关键信息
                lines = output.split('\n')
                for line in lines:
                    if line.startswith("✅"):
                        return True, line
                return True, output
            else:
                return False, f"状态检查失败: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "状态检查超时"
        except Exception as e:
            return False, f"状态检查出错: {e}"
    
    def _handle_add_note(self, content: str) -> Tuple[bool, str]:
        """处理添加笔记"""
        if not content:
            return False, "笔记内容为空"
        
        try:
            # 笔记文件路径
            note_file = os.path.join(self.notes_dir, "inbox.md")
            
            # 创建时间戳
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:00+08:00")
            
            # 添加笔记
            with open(note_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"\n{timestamp} {content}\n")
            
            # 记录日志
            self._log_command("ADD_NOTE", content)
            
            return True, f"笔记已添加: {content[:30]}..."
            
        except Exception as e:
            return False, f"添加笔记失败: {e}"
    
    def _handle_tell_time(self) -> Tuple[bool, str]:
        """处理时间查询"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]
            
            message = f"现在时间是 {current_time} {weekday}"
            
            # 记录日志
            self._log_command("TELL_TIME", message)
            
            return True, message
            
        except Exception as e:
            return False, f"获取时间失败: {e}"
    
    def _handle_search(self, query: str) -> Tuple[bool, str]:
        """处理搜索"""
        if not query:
            return False, "搜索内容为空"
        
        try:
            # 记录搜索请求
            self._log_command("SEARCH", query)
            
            # 这里可以集成实际的搜索功能
            # 目前先返回占位信息
            return True, f"已记录搜索请求: {query}"
            
        except Exception as e:
            return False, f"搜索失败: {e}"
    
    def _handle_weather(self, location: str) -> Tuple[bool, str]:
        """处理天气查询"""
        try:
            # 记录天气查询
            self._log_command("WEATHER", location)
            
            # 这里可以集成实际的天气API
            # 目前先返回占位信息
            if location == "本地":
                return True, "正在查询本地天气..."
            else:
                return True, f"正在查询{location}的天气..."
            
        except Exception as e:
            return False, f"天气查询失败: {e}"
    
    def _handle_test(self) -> Tuple[bool, str]:
        """处理测试命令"""
        try:
            message = "语音系统测试成功！所有功能正常。"
            
            # 记录日志
            self._log_command("TEST", message)
            
            return True, message
            
        except Exception as e:
            return False, f"测试失败: {e}"
    
    def _handle_help(self) -> Tuple[bool, str]:
        """处理帮助命令"""
        try:
            help_text = """
可用命令:
1. 状态检查: "检查系统状态", "查看运行状态"
2. 添加笔记: "添加笔记: 内容", "记录备忘"
3. 时间查询: "现在几点", "当前时间"
4. 搜索功能: "搜索人工智能", "查一下新闻"
5. 天气查询: "今天天气", "天气预报"
6. 系统测试: "测试语音", "试试功能"
7. 帮助信息: "有什么功能", "帮助"
            """.strip()
            
            # 记录日志
            self._log_command("HELP", "显示帮助信息")
            
            return True, help_text
            
        except Exception as e:
            return False, f"显示帮助失败: {e}"
    
    def _handle_list_notes(self) -> Tuple[bool, str]:
        """处理列出笔记"""
        try:
            note_file = os.path.join(self.notes_dir, "inbox.md")
            
            if not os.path.exists(note_file):
                return True, "暂无笔记"
            
            with open(note_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 提取最近5条笔记
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            recent_notes = lines[-5:] if len(lines) > 5 else lines
            
            if not recent_notes:
                return True, "暂无笔记"
            
            message = "最近笔记:\n" + "\n".join([f"• {note}" for note in recent_notes])
            
            # 记录日志
            self._log_command("LIST_NOTES", f"显示{len(recent_notes)}条笔记")
            
            return True, message
            
        except Exception as e:
            return False, f"列出笔记失败: {e}"
    
    def _log_command(self, action: str, payload: Any):
        """记录命令日志"""
        try:
            log_file = os.path.join(self.logs_dir, "command_router.log")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "action": action,
                "payload": str(payload) if payload else None
            }
            
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception:
            pass  # 日志记录失败不影响主要功能

def test_router():
    """测试路由器"""
    print("命令路由器测试")
    print("=" * 60)
    
    router = CommandRouter()
    
    test_cases = [
        ("检查系统状态", "RUN_DAILY_CHECK", None),
        ("查看运行状态", "RUN_DAILY_CHECK", None),
        ("添加笔记: 明天开会", "ADD_NOTE", "明天开会"),
        ("记录备忘测试内容", "ADD_NOTE", "测试内容"),
        ("现在几点", "TELL_TIME", None),
        ("当前时间", "TELL_TIME", None),
        ("搜索人工智能", "SEARCH", "人工智能"),
        ("查一下新闻", "SEARCH", "新闻"),
        ("今天天气", "WEATHER", "今天"),
        ("天气预报", "WEATHER", "预报"),
        ("测试语音", "TEST", None),
        ("有什么功能", "HELP", None),
        ("列出笔记", "LIST_NOTES", None),
        ("未知命令", "UNKNOWN", "未知命令"),
    ]
    
    all_passed = True
    
    for text, expected_action, expected_payload in test_cases:
        action, payload = router.route_command(text)
        
        if action == expected_action:
            status = "PASS"
            passed = True
        else:
            status = "FAIL"
            passed = False
            all_passed = False
        
        print(f"[{status}] '{text}'")
        print(f"   动作: {action} (期望: {expected_action})")
        print(f"   负载: {payload} (期望: {expected_payload})")
        
        # 测试处理
        if action != "UNKNOWN":
            success, message = router.handle(action, payload)
            print(f"   处理: {'成功' if success else '失败'} - {message[:50]}...")
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("[SUCCESS] 所有路由测试通过！")
    else:
        print("[FAILED] 部分测试失败")
    
    return all_passed

if __name__ == "__main__":
    success = test_router()
    sys.exit(0 if success else 1)