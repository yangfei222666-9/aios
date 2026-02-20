# scripts/voice_ptt.py - Push-to-Talk 语音输入
"""
按住 Ctrl+Shift+F1 开始录音，松开结束。
录音 → faster-whisper 转文字 → 通过 OpenClaw cron wake 发送给小九。

用法：
  python voice_ptt.py          # 默认快捷键 ctrl+shift+f1
  python voice_ptt.py --key f2 # 自定义快捷键
"""
import sys, io, os, time, json, tempfile, threading, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import sounddevice as sd
import soundfile as sf
import keyboard
import subprocess

# ---- Config ----
SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL = "large-v3"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE = "float16"

# ---- Global state ----
recording = False
audio_frames = []
model = None  # lazy load

def load_model():
    global model
    if model is None:
        print("⏳ 加载 Whisper 模型...")
        from faster_whisper import WhisperModel
        model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
        print("✅ 模型就绪")
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
    print("⏹️ 录音结束，转写中...")
    
    if not audio_frames:
        print("⚠️ 没有录到音频")
        return
    
    # 拼接音频并保存临时文件
    import numpy as np
    audio_data = np.concatenate(audio_frames, axis=0)
    
    # 检查音量（静音检测）
    rms = np.sqrt(np.mean(audio_data ** 2))
    if rms < 0.005:
        print("⚠️ 音量太低，跳过")
        return
    
    tmp_path = os.path.join(tempfile.gettempdir(), "ptt_recording.wav")
    sf.write(tmp_path, audio_data, SAMPLE_RATE)
    
    duration = len(audio_data) / SAMPLE_RATE
    print(f"📝 音频 {duration:.1f}s, RMS={rms:.4f}")
    
    # 转写
    t0 = time.time()
    m = load_model()
    segments, info = m.transcribe(
        tmp_path,
        language="zh",
        beam_size=5,
        no_speech_threshold=0.5,
        vad_filter=True,
    )
    
    text = "".join(seg.text for seg in segments).strip()
    elapsed = time.time() - t0
    
    if not text:
        print("⚠️ 未识别到语音")
        return
    
    print(f"💬 识别结果 ({elapsed:.1f}s): {text}")
    
    # 发送给 OpenClaw
    send_to_openclaw(text)
    
    # 清理
    try:
        os.remove(tmp_path)
    except:
        pass

def send_to_openclaw(text):
    """通过 openclaw CLI 发送 wake 事件"""
    try:
        result = subprocess.run(
            ["openclaw", "wake", text],
            capture_output=True, text=True, timeout=10,
            encoding='utf-8', errors='replace'
        )
        if result.returncode == 0:
            print(f"✅ 已发送给小九: {text}")
        else:
            # 备选：写到文件让心跳捡起来
            fallback_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "memory", "voice_inbox.jsonl"
            )
            with open(fallback_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": int(time.time()),
                    "text": text,
                    "source": "ptt",
                    "delivered": False,
                }, ensure_ascii=False) + "\n")
            print(f"📥 已存入 voice_inbox.jsonl (openclaw wake 失败)")
    except Exception as e:
        print(f"⚠️ 发送失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="Push-to-Talk 语音输入")
    parser.add_argument("--key", default="ctrl+shift+f1", help="快捷键 (默认 ctrl+shift+f1)")
    args = parser.parse_args()
    
    hotkey = args.key
    
    print(f"🐾 小九语音输入 (Push-to-Talk)")
    print(f"   快捷键: {hotkey}")
    print(f"   模型: {WHISPER_MODEL} ({WHISPER_DEVICE})")
    print(f"   按住说话，松开发送")
    print(f"   Ctrl+C 退出")
    print()
    
    # 预加载模型
    load_model()
    
    # 开启音频流
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        callback=audio_callback,
        dtype='float32',
    )
    stream.start()
    
    # 注册快捷键
    keyboard.on_press_key(hotkey.split('+')[-1], lambda e: start_recording() if keyboard.is_pressed(hotkey.rsplit('+', 1)[0]) else None)
    
    # 更简单的方式：用 hotkey
    keyboard.add_hotkey(hotkey, start_recording, trigger_on_release=False)
    
    # 松开检测
    release_key = hotkey.split('+')[-1]
    keyboard.on_release_key(release_key, lambda e: stop_recording())
    
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
