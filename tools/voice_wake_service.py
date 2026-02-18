#!/usr/bin/env python3
"""
语音唤醒服务 - 生产级版本
集成日志、异常恢复、守护进程
"""

import os
import sys
import time
import json
import queue
import logging
import traceback
from logging.handlers import TimedRotatingFileHandler

# 尝试导入音频和ASR库
try:
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
    AUDIO_AVAILABLE = True
except ImportError as e:
    logging.warning(f"音频库导入失败: {e}")
    AUDIO_AVAILABLE = False

# 配置
SAMPLE_RATE = 16000
MODEL_PATH = r"C:\Users\A\.openclaw\models\vosk-cn"
WAKE_PHRASES = ["小九", "你好小九", "小酒", "hi 小九"]
COOLDOWN = 2.0  # 唤醒冷却时间
COMMAND_TIMEOUT = 8.0  # 命令模式超时

def setup_logging():
    """配置结构化日志"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)
    
    # 文件输出（按天轮转）
    file_handler = TimedRotatingFileHandler(
        "logs/voice_wake.log",
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)
    
    logging.info("日志系统初始化完成")

def match_wake(text: str) -> bool:
    """唤醒词匹配（容错处理）"""
    if not text:
        return False
    
    # 移除空格和标点
    clean_text = text.replace(" ", "").replace("，", "").replace("。", "")
    
    for phrase in WAKE_PHRASES:
        clean_phrase = phrase.replace(" ", "")
        if clean_phrase in clean_text:
            logging.debug(f"唤醒词匹配: '{clean_phrase}' in '{clean_text}'")
            return True
    
    return False

def execute_command(command_text: str):
    """执行识别到的命令"""
    if not command_text or len(command_text.strip()) < 2:
        logging.warning(f"无效命令: '{command_text}'")
        return
    
    cmd = command_text.strip()
    logging.info(f"执行命令: {cmd}")
    
    # 命令映射
    command_handlers = {
        "检查状态": handle_check_status,
        "系统状态": handle_check_status,
        "添加笔记": handle_add_note,
        "查看日历": handle_check_calendar,
        "搜索": handle_search,
        "播放音乐": handle_play_music,
        "停止": handle_stop,
    }
    
    # 查找匹配的命令
    for key, handler in command_handlers.items():
        if key in cmd:
            try:
                handler(cmd)
                return
            except Exception as e:
                logging.error(f"命令执行失败 {key}: {e}")
                return
    
    # 未识别命令
    logging.warning(f"未识别命令: {cmd}")
    # 可以在这里添加默认处理或学习新命令

def handle_check_status(cmd: str):
    """处理状态检查命令"""
    logging.info("执行系统状态检查")
    # 调用 daily_check 脚本
    import subprocess
    result = subprocess.run(
        [sys.executable, "tools/daily_check_asr_tts.py"],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        logging.info(f"状态检查成功: {result.stdout[:100]}...")
    else:
        logging.error(f"状态检查失败: {result.stderr}")

def handle_add_note(cmd: str):
    """处理添加笔记命令"""
    # 提取笔记内容（移除"添加笔记"前缀）
    note_content = cmd.replace("添加笔记", "").strip()
    if note_content:
        logging.info(f"添加笔记: {note_content}")
        # 这里可以调用 note_add 函数
        # note_add(note_content)
    else:
        logging.warning("笔记内容为空")

def handle_check_calendar(cmd: str):
    """处理日历检查"""
    logging.info("检查日历事件")
    # 这里可以集成日历API

def handle_search(cmd: str):
    """处理搜索命令"""
    query = cmd.replace("搜索", "").strip()
    if query:
        logging.info(f"搜索: {query}")
        # 这里可以调用搜索功能
    else:
        logging.warning("搜索关键词为空")

def handle_play_music(cmd: str):
    """处理播放音乐命令"""
    logging.info("播放音乐")
    # 这里可以集成音乐播放

def handle_stop(cmd: str):
    """处理停止命令"""
    logging.info("停止当前操作")

def run_wake_loop():
    """主唤醒循环"""
    if not AUDIO_AVAILABLE:
        logging.error("音频库不可用，无法启动唤醒服务")
        return
    
    # 初始化模型
    logging.info(f"加载语音模型: {MODEL_PATH}")
    model = Model(MODEL_PATH)
    
    # 创建唤醒识别器（使用grammar限制）
    grammar = json.dumps(WAKE_PHRASES, ensure_ascii=False)
    wake_rec = KaldiRecognizer(model, SAMPLE_RATE, grammar)
    
    # 音频队列
    audio_queue = queue.Queue()
    
    def audio_callback(indata, frames, time_info, status):
        """音频回调函数"""
        if status:
            logging.warning(f"音频状态: {status}")
        audio_queue.put(bytes(indata))
    
    # 状态变量
    state = "SLEEP"
    cmd_rec = None
    cmd_deadline = 0
    last_wake_time = 0
    
    # 启动音频流
    logging.info("启动音频输入流...")
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        logging.info("语音唤醒服务已启动，等待唤醒词...")
        
        while True:
            # 获取音频数据
            try:
                data = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            if state == "SLEEP":
                # 唤醒词检测
                if wake_rec.AcceptWaveform(data):
                    result = json.loads(wake_rec.Result())
                    text = result.get("text", "")
                    
                    current_time = time.time()
                    if current_time - last_wake_time >= COOLDOWN and match_wake(text):
                        last_wake_time = current_time
                        logging.info(f"✅ 唤醒成功: {text}")
                        
                        # 切换到命令模式
                        cmd_rec = KaldiRecognizer(model, SAMPLE_RATE)
                        state = "COMMAND"
                        cmd_deadline = current_time + COMMAND_TIMEOUT
                        logging.info(f"进入命令模式，超时时间: {COMMAND_TIMEOUT}秒")
                
                # 可选：检查部分结果加速响应
                # partial = wake_rec.PartialResult()
                # if partial:
                #     partial_text = json.loads(partial).get("partial", "")
                #     if any(p in partial_text for p in WAKE_PHRASES):
                #         logging.debug(f"部分匹配: {partial_text}")
            
            elif state == "COMMAND":
                # 命令识别
                if cmd_rec.AcceptWaveform(data):
                    result = json.loads(cmd_rec.Result())
                    cmd_text = result.get("text", "").strip()
                    
                    if cmd_text:
                        logging.info(f"🎯 识别到命令: {cmd_text}")
                        execute_command(cmd_text)
                    else:
                        logging.info("命令识别为空")
                    
                    # 返回睡眠状态
                    state = "SLEEP"
                    logging.info("返回睡眠状态")
                
                # 检查超时
                elif time.time() > cmd_deadline:
                    logging.info("⌛ 命令模式超时，返回睡眠状态")
                    state = "SLEEP"

def main():
    """主函数 - 包含异常恢复"""
    setup_logging()
    
    logging.info("=" * 50)
    logging.info("语音唤醒服务启动")
    logging.info(f"Python版本: {sys.version}")
    logging.info(f"工作目录: {os.getcwd()}")
    logging.info(f"唤醒词: {WAKE_PHRASES}")
    logging.info("=" * 50)
    
    # 主循环（异常恢复）
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            logging.info(f"启动唤醒循环 (尝试 {restart_count + 1}/{max_restarts})")
            run_wake_loop()
            
        except KeyboardInterrupt:
            logging.info("收到中断信号，优雅退出")
            break
            
        except Exception as e:
            restart_count += 1
            logging.error(f"唤醒循环崩溃 (第{restart_count}次): {e}")
            logging.error(traceback.format_exc())
            
            if restart_count >= max_restarts:
                logging.critical(f"达到最大重启次数({max_restarts})，服务停止")
                break
            
            logging.info(f"2秒后重启...")
            time.sleep(2)
    
    logging.info("语音唤醒服务停止")

if __name__ == "__main__":
    # 确保 logs 目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 根据平台选择运行方式
    if os.name == "nt":  # Windows
        logging.info("Windows 平台 - 直接运行")
        main()
    else:  # Linux/macOS
        try:
            from daemon import DaemonContext
            logging.info("Unix 平台 - 守护进程模式")
            with DaemonContext():
                main()
        except ImportError:
            logging.warning("daemon 库未安装，以后台模式运行")
            import daemonize
            daemon = daemonize.Daemonize(app="voice_wake", pid="voice_wake.pid", action=main)
            daemon.start()