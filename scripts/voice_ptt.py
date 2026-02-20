# scripts/voice_ptt.py - Push-to-Talk 语音输入
"""
按住快捷键说话，松开自动转写发送给小九。
使用 pynput，不需要管理员权限。

用法：
  python voice_ptt.py          # 默认快捷键 f2
  python voice_ptt.py --key f5 # 自定义快捷键
"""
import sys, os, io, time, json, tempfile, threading, argparse
os.environ['PYTHONUNBUFFERED'] = '1'

# 如果用 pythonw 运行（无控制台），输出到日志文件
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "voice_ptt.log")
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
from pynput import keyboard

# ---- Config ----
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL = "large-v3"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE = "int8_float16"

BOT_TOKEN = "8278846913:AAGX6omR8aXEOWgcMBX3Y0EsJUGI2b2BE0s"
CHAT_ID = "7986452220"

# ---- Global state ----
recording = False
audio_frames = []
model = None

def load_model():
    global model
    if model is None:
        print("⏳ 加载 Whisper 模型...")
        t0 = time.time()
        from faster_whisper import WhisperModel
        model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
        print(f"✅ 模型就绪 ({time.time()-t0:.1f}s)")
    return model

def audio_callback(indata, frames, time_info, status):
    if recording:
        audio_frames.append(indata.copy())

def start_recording():
    global recording, audio_frames
    if recording:
        return
    audio_frames = []
    recording = True
    print("🎙️ 录音中... (松开停止)")

def stop_recording():
    global recording
    if not recording:
        return
    recording = False

    if not audio_frames:
        print("⚠️ 没有录到音频")
        return

    print("⏹️ 录音结束，转写中...")
    frames_copy = list(audio_frames)
    t = threading.Thread(target=_transcribe_and_send, args=(frames_copy,), daemon=True)
    t.start()

def _transcribe_and_send(frames):
    audio_data = np.concatenate(frames, axis=0)

    rms = np.sqrt(np.mean(audio_data ** 2))
    if rms < 0.005:
        print("⚠️ 音量太低，跳过")
        return

    tmp_path = os.path.join(tempfile.gettempdir(), "ptt_recording.wav")
    sf.write(tmp_path, audio_data, SAMPLE_RATE)

    duration = len(audio_data) / SAMPLE_RATE
    print(f"📝 音频 {duration:.1f}s, RMS={rms:.4f}")

    t0 = time.time()
    m = load_model()
    t_model = time.time() - t0

    t1 = time.time()
    segments, info = m.transcribe(
        tmp_path,
        language="zh",
        beam_size=1,
        no_speech_threshold=0.5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )
    text = "".join(seg.text for seg in segments).strip()
    t_transcribe = time.time() - t1

    if not text:
        print("⚠️ 未识别到语音")
        return

    total = t_model + t_transcribe
    print(f"💬 识别结果: {text}")
    print(f"⏱️ 模型={t_model:.1f}s 转写={t_transcribe:.1f}s 总计={total:.1f}s")

    t2 = time.time()
    send_to_telegram(text)
    print(f"📤 发送={time.time()-t2:.1f}s")

    try:
        os.remove(tmp_path)
    except:
        pass

def send_to_telegram(text):
    import urllib.request
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": CHAT_ID, "text": f"🎙️ {text}"}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print(f"✅ 已发送给小九: {text}")
                return
    except Exception as e:
        print(f"⚠️ 发送失败: {e}")

    fallback_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "memory", "voice_inbox.jsonl"
    )
    with open(fallback_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": int(time.time()), "text": text,
            "source": "ptt", "delivered": False,
        }, ensure_ascii=False) + "\n")
    print(f"📥 已存入 voice_inbox.jsonl")

def main():
    parser = argparse.ArgumentParser(description="Push-to-Talk 语音输入")
    parser.add_argument("--key", default="f2", help="快捷键 (默认 f2)")
    args = parser.parse_args()

    # 映射键名到 pynput Key
    key_map = {
        "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10, "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
    }
    hotkey = key_map.get(args.key.lower())
    if not hotkey:
        print(f"⚠️ 不支持的快捷键: {args.key}，支持 f1-f12")
        sys.exit(1)

    print(f"🐾 小九语音输入 (Push-to-Talk)")
    print(f"   快捷键: {args.key}")
    print(f"   模型: {WHISPER_MODEL} ({WHISPER_COMPUTE})")
    print(f"   按住说话，松开发送")
    print(f"   关闭窗口或 Ctrl+C 退出")
    print()

    load_model()

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS,
        callback=audio_callback, dtype='float32',
    )
    stream.start()

    def on_press(key):
        if key == hotkey:
            start_recording()

    def on_release(key):
        if key == hotkey:
            stop_recording()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    print("🟢 就绪，等待语音输入...\n")

    try:
        listener.join()
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()
        print("\n👋 已退出")

if __name__ == "__main__":
    main()
