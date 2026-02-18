#!/usr/bin/env python3
"""
语音唤醒服务 - 简化测试版本
不依赖实际音频硬件，用于测试逻辑
"""

import os
import sys
import time
import json
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging():
    """配置日志"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)
    
    # 文件输出
    os.makedirs("logs", exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        "logs/voice_wake_test.log",
        when="D",
        interval=1,
        backupCount=3,
        encoding="utf-8"
    )
    file_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)
    
    logging.info("测试日志系统初始化完成")

class MockVoiceWake:
    """模拟语音唤醒系统"""
    
    def __init__(self):
        self.wake_phrases = ["小九", "你好小九", "小酒"]
        self.state = "SLEEP"
        self.last_wake = 0
        self.cooldown = 2.0
        
    def match_wake(self, text: str) -> bool:
        """模拟唤醒词匹配"""
        if not text:
            return False
        
        clean_text = text.replace(" ", "").replace("，", "").replace("。", "")
        for phrase in self.wake_phrases:
            if phrase.replace(" ", "") in clean_text:
                return True
        return False
    
    def simulate_wake(self, text: str):
        """模拟唤醒事件"""
        current_time = time.time()
        
        if self.state == "SLEEP":
            if current_time - self.last_wake >= self.cooldown and self.match_wake(text):
                self.last_wake = current_time
                self.state = "COMMAND"
                logging.info(f"✅ 模拟唤醒: {text}")
                logging.info("进入命令模式 (模拟)")
                return True
        return False
    
    def simulate_command(self, text: str):
        """模拟命令识别"""
        if self.state == "COMMAND":
            logging.info(f"🎯 模拟命令: {text}")
            self.execute_command(text)
            self.state = "SLEEP"
            logging.info("返回睡眠状态")
            return True
        return False
    
    def execute_command(self, cmd: str):
        """执行命令"""
        cmd = cmd.strip()
        if not cmd:
            return
        
        logging.info(f"执行命令: {cmd}")
        
        # 简单命令处理
        if "状态" in cmd or "检查" in cmd:
            self.handle_check_status(cmd)
        elif "笔记" in cmd:
            self.handle_add_note(cmd)
        elif "停止" in cmd:
            logging.info("停止操作")
        else:
            logging.warning(f"未识别命令: {cmd}")
    
    def handle_check_status(self, cmd: str):
        """处理状态检查"""
        logging.info("执行系统状态检查")
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
                        logging.info(f"检查结果: {line}")
                        break
            else:
                logging.error(f"检查失败: {result.stderr}")
        except Exception as e:
            logging.error(f"检查异常: {e}")
    
    def handle_add_note(self, cmd: str):
        """处理添加笔记"""
        note_content = cmd.replace("添加笔记", "").replace("笔记", "").strip()
        if note_content:
            logging.info(f"添加笔记: {note_content}")
            # 这里可以调用实际的笔记功能
        else:
            logging.warning("笔记内容为空")

def run_test_loop():
    """测试循环 - 模拟用户交互"""
    wake_system = MockVoiceWake()
    
    # 测试用例
    test_scenarios = [
        ("小九", True),  # 唤醒
        ("检查系统状态", True),  # 命令
        ("小酒", True),  # 同音字唤醒
        ("添加笔记测试语音功能", True),  # 命令
        ("其他内容", False),  # 不应唤醒
        ("你好小九", True),  # 唤醒
        ("停止", True),  # 命令
    ]
    
    logging.info("开始模拟测试...")
    logging.info("=" * 50)
    
    for text, should_trigger in test_scenarios:
        logging.info(f"输入: '{text}' (应触发: {should_trigger})")
        
        if wake_system.state == "SLEEP":
            triggered = wake_system.simulate_wake(text)
            if triggered != should_trigger:
                logging.warning(f"⚠️ 唤醒触发不一致: 预期{should_trigger}, 实际{triggered}")
        elif wake_system.state == "COMMAND":
            triggered = wake_system.simulate_command(text)
            if not triggered and should_trigger:
                logging.warning(f"⚠️ 命令未触发: {text}")
        
        time.sleep(1)  # 模拟处理间隔
    
    logging.info("=" * 50)
    logging.info("模拟测试完成")

def main():
    """主函数"""
    setup_logging()
    
    logging.info("语音唤醒测试服务启动")
    logging.info(f"工作目录: {os.getcwd()}")
    
    restart_count = 0
    max_restarts = 3
    
    while restart_count < max_restarts:
        try:
            logging.info(f"第 {restart_count + 1} 次运行测试")
            run_test_loop()
            break  # 测试成功完成
            
        except KeyboardInterrupt:
            logging.info("测试被中断")
            break
            
        except Exception as e:
            restart_count += 1
            logging.error(f"测试失败 (第{restart_count}次): {e}")
            
            if restart_count >= max_restarts:
                logging.critical("达到最大重试次数")
                break
            
            logging.info("3秒后重试...")
            time.sleep(3)
    
    logging.info("测试服务停止")

if __name__ == "__main__":
    main()