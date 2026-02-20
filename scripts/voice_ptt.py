# scripts/voice_ptt.py - Push-to-Talk 语音输入
"""
按住快捷键说话，松开自动转写发送给小九。

用法：
  python voice_ptt.py          # 默认快捷键 f2
  python voice_ptt.py --key f5 # 自定义快捷键
"""
import sys, os, io, time, json, tempfile, threading, argparse
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import numpy as np
import sounddevice as sd
import soundfile as sf
import keyboard

# ---- Config ----
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL = "large-v3"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE = "int8_float16"

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
    # 后台线程转写，不阻塞快捷键监听
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
    
    # 分步计时
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
    
    # 发送
    t2 = time.time()
    send_to_openclaw(text)
    t_send = time.time() - t2
    print(f"📤 发送={t_send:.1f}s")
    
    try:
        os.remove(tmp_path)
    except:
        pass

def send_to_openclaw(text):
    """直接通过 Telegram Bot API 发消息，最快的方式"""
    import urllib.request, urllib.error
    
    bot_token = "8278846913:AAGX6omR8aXEOWgcMBX3Y0EsJUGI2b2BE0s"
    chat_id = "7986452220"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": f"🎙️ {text}",
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print(f"✅ 已发送给小九: {text}")
                return
    except Exception as e:
        print(f"⚠️ Telegram 发送失败: {e}")
    
    # 备选：写文件
    fallback_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "memory", "voice_inbox.jsonl"
    )
    with open(fallback_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": int(time.time()),
            "text": text,
            "source": "ptt",
            "delivered": False,
        }, ensure_ascii=False) + "\n")
    print(f"📥 已存入 voice_inbox.jsonl")

def main():
    parser = argparse.ArgumentParser(description="Push-to-Talk 语音输入")
    parser.add_argument("--key", default="f2", help="快捷键 (默认 f2)")
    args = parser.parse_args()
    
    hotkey = args.key
    
    print(f"🐾 小九语音输入 (Push-to-Talk)")
    print(f"   快捷键: {hotkey}")
    print(f"   模型: {WHISPER_MODEL} ({WHISPER_COMPUTE})")
    print(f"   按住说话，松开发送")
    print(f"   Ctrl+C 退出")
    print()
    
    load_model()
    
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        callback=audio_callback,
        dtype='float32',
    )
    stream.start()
    
    last_key = hotkey.split('+')[-1]
    if '+' in hotkey:
        keyboard.add_hotkey(hotkey, start_recording, suppress=False)
    else:
        keyboard.on_press_key(last_key, lambda e: start_recording(), suppress=False)
    keyboard.on_release_key(last_key, lambda e: stop_recording(), suppress=False)
    
    print("🟢 就绪，等待语音输入...\n")
    
    try:
        keyboard.wait('ctrl+c')
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()
        print("\n👋 已退出")

if __name__ == "__main__":
    main()
