# scripts/voice_wakeword.py - 语音唤醒 + Push-to-Talk
"""
持续监听麦克风，检测到"小九"后开始录音，
静音后自动停止并转写发送。

也支持 F2 按住说话（兼容 PTT 模式）。

用法：
  pythonw voice_wakeword.py        # 无窗口后台运行
  python -u voice_wakeword.py      # 有窗口调试
"""
import sys, os, io, time, json, tempfile, threading, argparse, collections
os.environ['PYTHONUNBUFFERED'] = '1'

LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "voice_wakeword.log")
if sys.stdout is None or not hasattr(sys.stdout, 'buffer'):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log_file = open(LOG_PATH, "a", encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard as kb

# ---- Config ----
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL = "large-v3"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE = "int8_float16"

BOT_TOKEN = "8278846913:AAGX6omR8aXEOWgcMBX3Y0EsJUGI2b2BE0s"
CHAT_ID = "7986452220"

WAKE_WORD = "小九"
WAKE_WINDOW_SEC = 1.2       # 唤醒检测窗口
WAKE_CHECK_INTERVAL = 0.6   # 每0.6秒检测一次
SILENCE_TIMEOUT = 3.0       # 静音3秒再停止，给思考时间
SILENCE_THRESHOLD = 0.008   # 静音 RMS 阈值
MIN_RECORD_SEC = 0.5        # 最短录音时长

# ---- State ----
class State:
    model = None
    recording = False       # PTT 录音中
    wake_listening = False  # 唤醒后录音中
    audio_frames = []
    wake_buffer = collections.deque(maxlen=int(SAMPLE_RATE * WAKE_WINDOW_SEC))
    last_wake_check = 0
    lock = threading.Lock()

S = State()

def load_model():
    if S.model is None:
        print(f"[{ts()}] ⏳ 加载 Whisper 模型...")
        t0 = time.time()
        from faster_whisper import WhisperModel
        S.model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
        print(f"[{ts()}] ✅ 模型就绪 ({time.time()-t0:.1f}s)")
    return S.model

def ts():
    return time.strftime("%H:%M:%S")

def audio_callback(indata, frames, time_info, status):
    flat = indata[:, 0]
    
    # 始终填充唤醒缓冲区
    S.wake_buffer.extend(flat)
    
    # PTT 或唤醒录音中
    if S.recording or S.wake_listening:
        S.audio_frames.append(flat.copy())

def transcribe_audio(audio_data):
    """转写音频，返回文本"""
    if len(audio_data) < SAMPLE_RATE * 0.3:
        return ""
    
    tmp_path = os.path.join(tempfile.gettempdir(), "wakeword_rec.wav")
    sf.write(tmp_path, audio_data, SAMPLE_RATE)
    
    m = load_model()
    segments, info = m.transcribe(
        tmp_path, language="zh", beam_size=1,
        no_speech_threshold=0.5, vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )
    text = "".join(seg.text for seg in segments).strip()
    
    try:
        os.remove(tmp_path)
    except:
        pass
    
    return text

def send_to_telegram(text):
    import urllib.request
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": CHAT_ID, "text": f"🎙️ {text}"}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print(f"[{ts()}] ✅ 已发送: {text}")
                return True
    except Exception as e:
        print(f"[{ts()}] ⚠️ 发送失败: {e}")
    return False

# ---- 唤醒检测 ----
def check_wake_word():
    """检查唤醒缓冲区是否包含唤醒词"""
    now = time.time()
    if now - S.last_wake_check < WAKE_CHECK_INTERVAL:
        return False
    if S.recording or S.wake_listening:
        return False
    
    S.last_wake_check = now
    
    buf = np.array(list(S.wake_buffer), dtype=np.float32)
    if len(buf) < SAMPLE_RATE * 0.5:
        return False
    
    rms = np.sqrt(np.mean(buf ** 2))
    if rms < 0.003:  # 降低阈值，更灵敏
        return False
    
    text = transcribe_audio(buf)
    if WAKE_WORD in text:
        print(f"[{ts()}] 🔔 唤醒词检测到: \"{text}\"")
        return True
    return False

def wake_record_loop():
    """唤醒后开始录音，静音自动停止"""
    S.wake_listening = True
    S.audio_frames = []
    
    # 播放提示音
    try:
        import winsound
        winsound.Beep(800, 150)  # 800Hz, 150ms
    except:
        pass
    
    print(f"[{ts()}] 🎙️ 唤醒录音开始，说话吧...")
    
    last_sound_time = time.time()
    
    while S.wake_listening:
        time.sleep(0.1)
        
        if S.audio_frames:
            recent = S.audio_frames[-1] if S.audio_frames else np.zeros(1)
            rms = np.sqrt(np.mean(recent ** 2))
            
            if rms > SILENCE_THRESHOLD:
                last_sound_time = time.time()
            elif time.time() - last_sound_time > SILENCE_TIMEOUT:
                break
    
    S.wake_listening = False
    
    if not S.audio_frames:
        print(f"[{ts()}] ⚠️ 没有录到音频")
        return
    
    audio_data = np.concatenate(S.audio_frames)
    duration = len(audio_data) / SAMPLE_RATE
    
    if duration < MIN_RECORD_SEC:
        print(f"[{ts()}] ⚠️ 录音太短 ({duration:.1f}s)")
        return
    
    print(f"[{ts()}] ⏹️ 录音结束 ({duration:.1f}s)，转写中...")
    
    t0 = time.time()
    text = transcribe_audio(audio_data)
    elapsed = time.time() - t0
    
    # 去掉唤醒词本身（只去第一个）
    if WAKE_WORD in text:
        idx = text.index(WAKE_WORD)
        text = text[idx + len(WAKE_WORD):]
    text = text.lstrip("，。,. !！?？")
    
    if not text:
        print(f"[{ts()}] ⚠️ 未识别到有效内容")
        return
    
    print(f"[{ts()}] 💬 识别结果 ({elapsed:.1f}s): {text}")
    send_to_telegram(text)

# ---- PTT (F2) ----
def ptt_start():
    if S.recording or S.wake_listening:
        return
    S.recording = True
    S.audio_frames = []
    print(f"[{ts()}] 🎙️ PTT 录音中... (松开停止)")

def ptt_stop():
    if not S.recording:
        return
    S.recording = False
    
    if not S.audio_frames:
        return
    
    frames_copy = list(S.audio_frames)
    t = threading.Thread(target=_ptt_transcribe, args=(frames_copy,), daemon=True)
    t.start()

def _ptt_transcribe(frames):
    audio_data = np.concatenate(frames)
    rms = np.sqrt(np.mean(audio_data ** 2))
    if rms < 0.005:
        return
    
    duration = len(audio_data) / SAMPLE_RATE
    print(f"[{ts()}] 📝 PTT 音频 {duration:.1f}s")
    
    t0 = time.time()
    text = transcribe_audio(audio_data)
    elapsed = time.time() - t0
    
    if text:
        print(f"[{ts()}] 💬 PTT 结果 ({elapsed:.1f}s): {text}")
        send_to_telegram(text)

# ---- Main ----
def main():
    print(f"[{ts()}] 🐾 小九语音助手")
    print(f"[{ts()}]    唤醒词: \"{WAKE_WORD}\"")
    print(f"[{ts()}]    PTT快捷键: F2")
    print(f"[{ts()}]    模型: {WHISPER_MODEL} ({WHISPER_COMPUTE})")
    print()
    
    load_model()
    
    # 音频流
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS,
        callback=audio_callback, dtype='float32',
        blocksize=int(SAMPLE_RATE * 0.1),  # 100ms 块
    )
    stream.start()
    
    # PTT 快捷键
    def on_press(key):
        if key == kb.Key.f2:
            ptt_start()
    
    def on_release(key):
        if key == kb.Key.f2:
            ptt_stop()
    
    listener = kb.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    print(f"[{ts()}] 🟢 就绪，说\"{WAKE_WORD}\"唤醒 或按 F2 说话\n")
    
    # 主循环：唤醒检测
    try:
        while True:
            time.sleep(0.2)
            
            if not S.recording and not S.wake_listening:
                if check_wake_word():
                    # 清空缓冲区，开始录音
                    S.wake_buffer.clear()
                    t = threading.Thread(target=wake_record_loop, daemon=True)
                    t.start()
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()
        listener.stop()
        print(f"\n[{ts()}] 👋 已退出")

if __name__ == "__main__":
    main()
