#!/usr/bin/env python3
"""
语音唤醒监听器 - 生产版本
基于 vosk + sounddevice 的实时语音唤醒系统
"""

# 编码修复（Windows 兼容性）
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        # Python 3.7 以下版本
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import time
import json
import queue
import logging
from dataclasses import dataclass
from typing import List, Optional
from logging.handlers import TimedRotatingFileHandler

# 导入依赖
try:
    import numpy as np
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
    import yaml  # pyyaml
except ImportError as e:
    print(f"错误: 缺少依赖 - {e}")
    print("请运行: pip install vosk sounddevice numpy pyyaml")
    sys.exit(1)

# -----------------------------
# Unicode 清理函数
# -----------------------------
def sanitize_unicode(s: str) -> str:
    """
    清理 Unicode 字符串
    
    参数:
        s: 输入字符串
    
    返回:
        清理后的字符串
    """
    if not s:
        return ""
    
    try:
        # 优先使用专业的 Unicode 清理工具
        from tools.unicode_sanitizer import sanitize_unicode as su
        return su(s)
    except ImportError:
        # 回退到简单清理
        import unicodedata
        
        # Unicode NFC 规范化
        s = unicodedata.normalize("NFC", s)
        
        # 移除零宽字符
        zero_width_chars = "\u200b\u200c\u200d\u200e\u200f\u2060\ufeff"
        for ch in zero_width_chars:
            s = s.replace(ch, " ")
        
        # 压缩空白
        s = " ".join(s.split())
        
        return s.strip()

# -----------------------------
# 配置类
# -----------------------------
@dataclass
class VoiceWakeConfig:
    """语音唤醒配置"""
    enabled: bool = True
    model_path: str = r"C:\Users\A\.openclaw\models\vosk-cn"
    wake_phrases: List[str] = None
    command_timeout: float = 8.0
    cooldown: float = 2.0
    device: Optional[int] = None
    log_level: str = "INFO"
    pause_while_tts: bool = True
    tts_flag_path: str = r"logs\tts_playing.flag"
    vad_end_silence_ms: int = 800
    vad_energy_threshold: float = 0.015
    sample_rate: int = 16000
    blocksize: int = 8000  # 0.5秒
    
    def __post_init__(self):
        if self.wake_phrases is None:
            self.wake_phrases = ["小九", "你好小九", "小酒"]

def load_config(yaml_path: str) -> VoiceWakeConfig:
    """从 YAML 文件加载配置"""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"警告: 配置文件 {yaml_path} 不存在，使用默认配置")
        data = {}
    except Exception as e:
        print(f"错误: 读取配置文件失败 - {e}")
        data = {}
    
    vw = data.get("voice_wake") or {}
    
    # 创建配置对象
    cfg = VoiceWakeConfig(
        enabled=bool(vw.get("enabled", True)),
        model_path=str(vw.get("model_path", VoiceWakeConfig.model_path)),
        wake_phrases=list(vw.get("wake_phrases", ["小九", "你好小九", "小酒"])),
        command_timeout=float(vw.get("command_timeout", 8)),
        cooldown=float(vw.get("cooldown", 2)),
        device=vw.get("device", None),
        log_level=str(vw.get("log_level", "INFO")).upper(),
        pause_while_tts=bool(vw.get("pause_while_tts", True)),
        vad_end_silence_ms=int(vw.get("vad_end_silence_ms", 800)),
    )
    
    # 可选配置项
    if "tts_flag_path" in vw:
        cfg.tts_flag_path = str(vw["tts_flag_path"])
    if "vad_energy_threshold" in vw:
        cfg.vad_energy_threshold = float(vw["vad_energy_threshold"])
    if "sample_rate" in vw:
        cfg.sample_rate = int(vw["sample_rate"])
    if "blocksize" in vw:
        cfg.blocksize = int(vw["blocksize"])
    
    return cfg

# -----------------------------
# 日志配置
# -----------------------------
def setup_logging(level: str, log_path: str = "voice_wake.log"):
    """配置日志系统"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    
    # 文件处理器（按天轮转）
    file_handler = TimedRotatingFileHandler(
        log_path,
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

# -----------------------------
# 文本规范化
# -----------------------------
def _normalize_zh_fallback(s: str) -> str:
    """轻量级文本规范化（备用）"""
    if not s:
        return ""
    
    # 移除零宽字符
    zero_width = ["\u200b", "\u200c", "\u200d", "\ufeff"]
    for ch in zero_width:
        s = s.replace(ch, "")
    
    # 规范化空白
    return " ".join(s.strip().split())

def normalize_zh(s: str) -> str:
    """文本规范化（优先使用新的 Unicode 清理工具）"""
    try:
        # 尝试导入新的 Unicode 清理工具
        from tools.unicode_sanitizer import clean_asr_text
        return clean_asr_text(s)
    except ImportError:
        try:
            # 回退到旧的规范化模块
            from tools.text_normalize import normalize_zh as nz
            return nz(s)
        except ImportError:
            # 最终备用方案
            return _normalize_zh_fallback(s)

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

# -----------------------------
# VAD (Voice Activity Detection)
# -----------------------------
class EnergyVAD:
    """基于能量的语音活动检测"""
    
    def __init__(self, end_silence_ms: int = 800, energy_threshold: float = 0.015):
        self.end_silence_ms = end_silence_ms
        self.energy_threshold = energy_threshold
        self.in_speech = False
        self.last_voice_ts = 0.0
    
    def _energy(self, pcm16_bytes: bytes) -> float:
        """计算音频能量"""
        if not pcm16_bytes:
            return 0.0
        
        # 转换为浮点数并计算 RMS
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32)
        if samples.size == 0:
            return 0.0
        
        rms = np.sqrt(np.mean(samples * samples)) / 32768.0
        return float(rms)
    
    def process(self, pcm16_bytes: bytes) -> str:
        """处理音频块，返回状态"""
        now = time.time()
        energy = self._energy(pcm16_bytes)
        
        if energy >= self.energy_threshold:
            # 检测到语音
            self.last_voice_ts = now
            if not self.in_speech:
                self.in_speech = True
                return "speech_start"
            return "speech"
        else:
            # 静音
            if self.in_speech:
                silence_ms = (now - self.last_voice_ts) * 1000.0
                if silence_ms >= self.end_silence_ms:
                    self.in_speech = False
                    return "end_of_speech"
            return "silence"

# -----------------------------
# 命令过滤器
# -----------------------------
IGNORE_CMDS = {"你好", "在吗", "喂", "哈喽", "hello", "hi", "hey", "嗨"}

def is_meaningful_command(cmd: str, wake_phrases: list[str]) -> bool:
    """
    判断命令是否有意义
    
    参数:
        cmd: 原始命令文本
        wake_phrases: 唤醒词列表
    
    返回:
        bool: True 表示有意义，False 表示应忽略
    """
    # 规范化命令
    t = cmd.replace(" ", "").strip()
    if not t:
        return False
    
    # 规范化唤醒词
    normalized_wake_phrases = [wp.replace(" ", "") for wp in wake_phrases]
    
    # 规则1: 只包含唤醒词 -> 忽略
    if any(t == wp for wp in normalized_wake_phrases):
        return False
    
    # 规则2: 只包含寒暄词 -> 忽略
    if t in IGNORE_CMDS:
        return False
    
    # 规则3: 太短 -> 忽略（可调整阈值）
    if len(t) <= 2:
        return False
    
    # 规则4: 检查是否只是唤醒词+寒暄的组合
    for wp in normalized_wake_phrases:
        if t.startswith(wp):
            remaining = t[len(wp):]
            if not remaining or remaining in IGNORE_CMDS or len(remaining) <= 1:
                return False
    
    # 规则5: 检查是否只是寒暄+唤醒词的组合
    for greeting in IGNORE_CMDS:
        if t.startswith(greeting):
            remaining = t[len(greeting):]
            if not remaining or remaining in normalized_wake_phrases:
                return False
    
    # 默认认为有效
    return True

# -----------------------------
# 核心服务
# -----------------------------
class VoiceWakeService:
    """语音唤醒服务"""
    
    def __init__(self, cfg: VoiceWakeConfig):
        self.cfg = cfg
        self.q = queue.Queue(maxsize=50)
        
        # 加载模型
        logging.info(f"加载语音模型: {cfg.model_path}")
        self.model = Model(cfg.model_path)
        
        # 唤醒识别器（使用语法限制）
        grammar = json.dumps(cfg.wake_phrases, ensure_ascii=False)
        self.wake_rec = KaldiRecognizer(self.model, cfg.sample_rate, grammar)
        
        # 状态
        self.state = "SLEEP"
        self.cmd_rec = None
        self.vad = None
        self.cmd_deadline = 0.0
        self.last_wake_ts = 0.0
    
    def is_tts_playing(self) -> bool:
        """检查 TTS 是否正在播放"""
        if not self.cfg.pause_while_tts:
            return False
        return os.path.exists(self.cfg.tts_flag_path)
    
    def audio_callback(self, indata, frames, time_info, status):
        """音频回调函数"""
        if status:
            logging.warning(f"音频状态: {status}")
        
        try:
            # 将音频数据放入队列
            self.q.put_nowait(bytes(indata))
        except queue.Full:
            # 队列满时丢弃数据（避免阻塞回调线程）
            pass
    
    def on_wake(self, wake_text: str):
        """唤醒回调"""
        logging.info(f'WAKE: "{wake_text}"')
        
        # 设置状态为 PROMPT（等待 TTS 响应）
        self.state = "PROMPT"
        logging.info("状态: SLEEP → PROMPT")
        
        # 调用 TTS 语音反馈
        self._speak_wake_response()
    
    def _speak_wake_response(self):
        """播放唤醒响应"""
        try:
            # 导入 TTS 模块
            from tools.simple_tts import SimpleTTS
            
            tts = SimpleTTS()
            
            # 异步播放唤醒响应
            response_text = "我在，请说命令"
            
            # 使用上下文管理器确保标志文件管理
            with tts.speak_with_guard(response_text):
                logging.info(f'TTS: "{response_text}"')
                
                # TTS 播放完成后进入命令模式
                # 这里依赖 TTS 上下文管理器自动清理标志
                # 在 _check_tts_flag 中会检测到标志消失，然后进入命令模式
                
        except ImportError:
            logging.warning("TTS 模块未安装，跳过语音反馈")
            # 如果没有 TTS，直接进入命令模式
            self._enter_command_mode()
        except Exception as e:
            logging.error(f"播放唤醒响应时出错: {e}")
            # 出错时也进入命令模式
            self._enter_command_mode()
    
    def _enter_command_mode(self):
        """进入命令模式"""
        self.state = "COMMAND"
        self.cmd_deadline = time.time() + self.config.command_timeout
        logging.info(f"状态: PROMPT → COMMAND (超时: {self.config.command_timeout}s)")
    
    def on_command(self, cmd_text: str):
        """命令回调"""
        cmd_text = cmd_text.strip()
        if not cmd_text:
            logging.info("命令为空，忽略")
            return
        
        # 检查命令是否有意义
        if not is_meaningful_command(cmd_text, self.cfg.wake_phrases):
            logging.info(f'CMD ignored: "{cmd_text}"')
            return
        
        # ✅ 真正命令才处理
        logging.info(f'CMD: "{cmd_text}"')
        
        # 保存命令到文件（用于调试）
        os.makedirs("logs", exist_ok=True)
        with open(r"logs\voice_command.latest.txt", "w", encoding="utf-8", errors="replace") as f:
            f.write(cmd_text + "\n")
        
        # 执行命令处理
        self._execute_voice_command(cmd_text)
    
    def _execute_voice_command(self, cmd_text: str):
        """执行语音命令"""
        try:
            # 导入命令处理器
            from tools.voice_command_handler import VoiceCommandHandler
            
            handler = VoiceCommandHandler()
            success, message = handler.execute_command(cmd_text)
            
            if success:
                logging.info(f"命令执行成功: {message}")
            else:
                logging.warning(f"命令执行失败: {message}")
                
        except ImportError:
            logging.warning("命令处理器未安装，跳过命令执行")
        except Exception as e:
            logging.error(f"执行命令时出错: {e}")
    
    def enter_command_mode(self):
        """进入命令模式（从 PROMPT 状态调用）"""
        if self.state != "PROMPT":
            logging.warning(f"尝试从 {self.state} 状态进入命令模式，忽略")
            return
            
        self.state = "COMMAND"
        self.cmd_rec = KaldiRecognizer(self.model, self.cfg.sample_rate)
        self.vad = EnergyVAD(
            end_silence_ms=self.cfg.vad_end_silence_ms,
            energy_threshold=self.cfg.vad_energy_threshold,
        )
        self.cmd_deadline = time.time() + float(self.cfg.command_timeout)
        logging.info("状态: PROMPT → COMMAND")
    
    def exit_to_sleep(self):
        """返回睡眠模式"""
        self.state = "SLEEP"
        self.cmd_rec = None
        self.vad = None
        self.cmd_deadline = 0.0
        
        # 重置唤醒识别器
        grammar = json.dumps(self.cfg.wake_phrases, ensure_ascii=False)
        self.wake_rec = KaldiRecognizer(self.model, self.cfg.sample_rate, grammar)
        
        logging.info("返回睡眠模式")
    
    def finalize_command(self):
        """结束当前命令"""
        if not self.cmd_rec:
            self.exit_to_sleep()
            return
        
        try:
            # 获取最终识别结果
            result_json = self.cmd_rec.FinalResult() or "{}"
            result = json.loads(result_json)
            text = (result.get("text") or "").strip()
            
            if text:
                self.on_command(text)
            else:
                logging.info("命令为空")
        
        except Exception as e:
            logging.error(f"处理命令时出错: {e}")
        
        finally:
            self.exit_to_sleep()
    
    def run_forever(self):
        """主循环"""
        if not self.cfg.enabled:
            logging.warning("语音唤醒已禁用")
            return
        
        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)
        
        logging.info("语音唤醒服务启动...")
        logging.info(f"模型路径: {self.cfg.model_path}")
        logging.info(f"唤醒词: {self.cfg.wake_phrases}")
        logging.info(f"音频设备: {self.cfg.device}")
        logging.info(f"采样率: {self.cfg.sample_rate}")
        
        try:
            # 打开音频流
            with sd.RawInputStream(
                samplerate=self.cfg.sample_rate,
                blocksize=self.cfg.blocksize,
                dtype="int16",
                channels=1,
                device=self.cfg.device,
                callback=self.audio_callback,
            ):
                logging.info("音频流已打开，进入睡眠模式")
                
                # 主循环
                while True:
                    # 获取音频数据
                    data = self.q.get()
                    
                    # 防自唤醒：TTS 播放时跳过处理
                    if self.is_tts_playing():
                        continue
                    
                    now = time.time()
                    
                    if self.state == "SLEEP":
                        # 睡眠模式：检测唤醒词
                        if self.wake_rec.AcceptWaveform(data):
                            try:
                                result_json = self.wake_rec.Result() or "{}"
                                result = json.loads(result_json)
                                text = (result.get("text") or "").strip()
                                
                                # Unicode 清理
                                text = sanitize_unicode(text)
                                
                                # 检查冷却时间和唤醒词匹配
                                if (now - self.last_wake_ts) >= float(self.cfg.cooldown):
                                    if match_wake(text, self.cfg.wake_phrases):
                                        self.last_wake_ts = now
                                        self.on_wake(text)
                                        # 注意：这里不调用 enter_command_mode()
                                        # 因为 on_wake() 会设置状态为 PROMPT
                                        # 等待 TTS 播放完成后再进入命令模式
                                
                            except Exception as e:
                                logging.error(f"处理唤醒结果时出错: {e}")
                    
                    elif self.state == "PROMPT":
                        # PROMPT 状态：等待 TTS 播放完成
                        # 检查 TTS 标志是否消失
                        if not self.is_tts_playing():
                            # TTS 播放完成，进入命令模式
                            self.enter_command_mode()
                    
                    elif self.state == "COMMAND":
                        # 命令模式
                        
                        # 1. VAD 检测
                        if self.vad:
                            vad_event = self.vad.process(data)
                            if vad_event == "end_of_speech":
                                logging.info("VAD 检测到语音结束，结束命令")
                                self.finalize_command()
                                continue
                        
                        # 2. 识别中间结果
                        if self.cmd_rec and self.cmd_rec.AcceptWaveform(data):
                            try:
                                result_json = self.cmd_rec.Result() or "{}"
                                result = json.loads(result_json)
                                text = (result.get("text") or "").strip()
                                
                                # Unicode 清理
                                text = sanitize_unicode(text)
                                
                                if text:
                                    self.on_command(text)
                                    self.exit_to_sleep()
                                    continue
                                
                            except Exception as e:
                                logging.error(f"处理命令结果时出错: {e}")
                        
                        # 3. 超时检查
                        if now > self.cmd_deadline:
                            logging.info("命令模式超时，结束命令")
                            self.finalize_command()
        
        except KeyboardInterrupt:
            logging.info("收到中断信号，正在退出...")
        except Exception as e:
            logging.error(f"音频流错误: {e}")
            raise

# -----------------------------
# 设备列表
# -----------------------------
def list_input_devices():
    """列出音频输入设备"""
    print("音频输入设备列表:")
    print("=" * 60)
    
    try:
        devices = sd.query_devices()
        input_count = 0
        
        for i, device in enumerate(devices):
            max_input = device.get('max_input_channels', 0)
            if max_input > 0:
                input_count += 1
                print(f"\n设备 #{i}: {device['name']}")
                print(f"  输入通道: {max_input}")
                print(f"  默认采样率: {device.get('default_samplerate', 'N/A')}")
                print(f"  设备ID: {i}")
        
        print(f"\n{'='*60}")
        print(f"找到 {input_count} 个输入设备")
        
        if input_count == 0:
            print("警告: 未找到音频输入设备!")
        
    except Exception as e:
        print(f"查询设备时出错: {e}")

# -----------------------------
# 主函数
# -----------------------------
def main():
    """主函数"""
    # 解析参数
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        list_input_devices()
        return
    
    # 配置文件路径
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "openclaw.yaml"
    
    # 加载配置
    try:
        cfg = load_config(cfg_path)
    except Exception as e:
        print(f"加载配置失败: {e}")
        sys.exit(1)
    
    # 设置日志
    setup_logging(cfg.log_level)
    
    # 创建服务
    svc = VoiceWakeService(cfg)
    
    # 崩溃自动重启
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            svc.run_forever()
            break  # 正常退出
            
        except KeyboardInterrupt:
            logging.info("用户中断，退出")
            break
            
        except Exception as e:
            restart_count += 1
            logging.exception(f"语音唤醒服务崩溃 (重启 {restart_count}/{max_restarts})")
            
            if restart_count >= max_restarts:
                logging.error("达到最大重启次数，退出")
                break
            
            # 等待后重启
            time.sleep(2)

if __name__ == "__main__":
    main()