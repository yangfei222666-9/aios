#!/usr/bin/env python3
"""
语音唤醒系统 - 测试版本
不依赖实际音频硬件，用于验证逻辑
"""

import os
import sys
import time
import json
import logging
from dataclasses import dataclass
from typing import List, Optional
from logging.handlers import TimedRotatingFileHandler

# 模拟音频库
class MockSoundDevice:
    @staticmethod
    def query_devices():
        return [
            {"name": "Mock Microphone", "max_input_channels": 1, "default_samplerate": 16000}
        ]
    
    class RawInputStream:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            
        def __enter__(self):
            print(f"模拟音频输入流: {self.kwargs}")
            return self
            
        def __exit__(self, *args):
            print("关闭音频输入流")

# 模拟 vosk
class MockVosk:
    class Model:
        def __init__(self, path):
            self.path = path
            print(f"加载模型: {path}")
    
    class KaldiRecognizer:
        def __init__(self, model, sample_rate, grammar=None):
            self.model = model
            self.sample_rate = sample_rate
            self.grammar = grammar
            self.mock_responses = []
            
        def AcceptWaveform(self, data):
            # 模拟识别结果
            if self.mock_responses:
                return True
            return False
            
        def Result(self):
            if self.mock_responses:
                return json.dumps({"text": self.mock_responses.pop(0)})
            return json.dumps({"text": ""})
            
        def FinalResult(self):
            return json.dumps({"text": ""})

@dataclass
class VoiceWakeConfig:
    """测试配置"""
    enabled: bool = True
    model_path: str = r"C:\Users\A\.openclaw\models\vosk-cn"
    wake_phrases: List[str] = None
    command_timeout: float = 8.0
    cooldown: float = 2.0
    device: Optional[int] = None
    log_level: str = "INFO"
    pause_while_tts: bool = True
    tts_flag_path: str = r"logs\tts_playing.flag"
    
    def __post_init__(self):
        if self.wake_phrases is None:
            self.wake_phrases = ["小九", "你好小九", "小酒"]

def setup_logging(level: str = "INFO"):
    """配置日志"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console)
    
    print(f"日志系统初始化完成 (级别: {level})")

def normalize_zh(s: str) -> str:
    """文本规范化"""
    if not s:
        return ""
    # 简单规范化：去空格
    return " ".join(s.strip().split())

def match_wake(text: str, wake_phrases: List[str]) -> bool:
    """唤醒词匹配"""
    t = normalize_zh(text).replace(" ", "")
    if not t:
        return False
    
    for p in wake_phrases:
        pn = normalize_zh(p).replace(" ", "")
        if pn and pn in t:
            return True
    return False

class MockVoiceWakeService:
    """模拟语音唤醒服务"""
    
    def __init__(self, config: VoiceWakeConfig):
        self.cfg = config
        self.state = "SLEEP"
        self.last_wake_ts = 0.0
        self.cmd_deadline = 0.0
        
        print(f"初始化语音唤醒服务")
        print(f"  唤醒词: {config.wake_phrases}")
        print(f"  命令超时: {config.command_timeout}秒")
        print(f"  冷却时间: {config.cooldown}秒")
    
    def on_wake(self, wake_text: str):
        """唤醒回调"""
        print(f"[WAKE] 唤醒: '{wake_text}'")
    
    def on_command(self, cmd_text: str):
        """命令回调"""
        cmd_text = cmd_text.strip()
        if not cmd_text:
            return
        
        print(f"[CMD] 命令: '{cmd_text}'")
        
        # 简单命令处理
        if "状态" in cmd_text or "检查" in cmd_text:
            self.handle_check_status(cmd_text)
        elif "笔记" in cmd_text:
            self.handle_add_note(cmd_text)
        elif "测试" in cmd_text:
            print("执行测试命令")
        elif "停止" in cmd_text:
            print("停止操作")
        else:
            print(f"未识别命令: {cmd_text}")
    
    def handle_check_status(self, cmd: str):
        """处理状态检查"""
        print("执行系统状态检查...")
        # 这里可以调用实际的检查脚本
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "tools/daily_check_asr_tts.py"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            if result.returncode == 0:
                # 提取摘要行
                for line in result.stdout.split('\n'):
                    if 'daily_check |' in line:
                        print(f"检查结果: {line}")
                        break
            else:
                print(f"检查失败: {result.stderr}")
        except Exception as e:
            print(f"检查异常: {e}")
    
    def handle_add_note(self, cmd: str):
        """处理添加笔记"""
        note_content = cmd.replace("添加笔记", "").replace("笔记", "").strip()
        if note_content:
            print(f"添加笔记: {note_content}")
            # 这里可以调用实际的笔记功能
        else:
            print("笔记内容为空")
    
    def simulate_interaction(self, user_input: str):
        """模拟用户交互"""
        current_time = time.time()
        
        if self.state == "SLEEP":
            # 检查是否唤醒
            if current_time - self.last_wake_ts >= self.cfg.cooldown and match_wake(user_input, self.cfg.wake_phrases):
                self.last_wake_ts = current_time
                self.on_wake(user_input)
                self.state = "COMMAND"
                self.cmd_deadline = current_time + self.cfg.command_timeout
                print(f"进入命令模式，超时: {self.cfg.command_timeout}秒")
                return True
            else:
                print(f"睡眠状态，输入: '{user_input}' (未唤醒)")
                return False
        
        elif self.state == "COMMAND":
            # 命令模式
            if user_input.strip():
                self.on_command(user_input)
                self.state = "SLEEP"
                print("返回睡眠状态")
                return True
            elif current_time > self.cmd_deadline:
                print("命令模式超时，返回睡眠状态")
                self.state = "SLEEP"
                return False
        
        return False

def run_test_scenarios():
    """运行测试场景"""
    config = VoiceWakeConfig()
    service = MockVoiceWakeService(config)
    
    print("\n" + "="*60)
    print("开始模拟测试")
    print("="*60)
    
    # 测试场景
    test_cases = [
        # 第一轮：初始状态 SLEEP
        ("小九", "wake", "唤醒测试"),
        ("检查系统状态", "command", "命令测试"),
        
        # 第二轮：返回 SLEEP 后
        ("等待冷却...", "wait", "冷却等待"),
        ("小酒", "wake", "同音字唤醒"),
        ("添加笔记测试语音功能", "command", "笔记命令"),
        
        # 第三轮：返回 SLEEP 后  
        ("等待冷却...", "wait", "冷却等待"),
        ("你好小九", "wake", "长唤醒词"),
        ("停止", "command", "停止命令"),
        
        # 第四轮
        ("等待冷却...", "wait", "冷却等待"),
        ("其他内容", "ignore", "非唤醒词"),
        ("测试语音识别", "wake", "测试命令需要先唤醒"),
    ]
    
    for user_input, expected_action, description in test_cases:
        print(f"\n测试: {description}")
        print(f"输入: '{user_input}'")
        
        if user_input == "等待冷却...":
            print("等待冷却时间...")
            time.sleep(2.5)  # 超过 2.0 秒冷却时间
            continue
        
        triggered = service.simulate_interaction(user_input)
        
        # 根据预期动作判断结果
        if expected_action == "wake":
            success = triggered and service.state == "COMMAND"
            print(f"状态: {service.state}, 触发: {triggered}")
            print(f"[{'PASS' if success else 'FAIL'}] 期望唤醒 -> {'成功' if success else '失败'}")
            
        elif expected_action == "command":
            success = triggered and service.state == "SLEEP"
            print(f"状态: {service.state}, 触发: {triggered}")
            print(f"[{'PASS' if success else 'FAIL'}] 期望命令 -> {'成功' if success else '失败'}")
            
        elif expected_action == "ignore":
            success = not triggered
            print(f"状态: {service.state}, 触发: {triggered}")
            print(f"[{'PASS' if success else 'FAIL'}] 期望忽略 -> {'成功' if success else '失败'}")
    
    print("\n" + "="*60)
    print("模拟测试完成")
    print("="*60)

def main():
    """主函数"""
    setup_logging("INFO")
    
    print("语音唤醒测试系统")
    print(f"工作目录: {os.getcwd()}")
    
    try:
        run_test_scenarios()
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()