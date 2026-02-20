# scripts/voice_handler.py - 自动处理 Telegram 语音消息
"""
监听 Telegram 语音消息，自动转写并执行。
配合 OpenClaw 的消息钩子使用。
"""
import sys, os, io, json, tempfile, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def transcribe_voice(audio_path):
    """用 Whisper 转写音频文件"""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
        segments, info = model.transcribe(
            audio_path, language="zh", beam_size=1,
            no_speech_threshold=0.5, vad_filter=True,
        )
        text = "".join(seg.text for seg in segments).strip()
        return text
    except Exception as e:
        print(f"转写失败: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python voice_handler.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    text = transcribe_voice(audio_file)
    
    if text:
        print(f"转写结果: {text}")
        # 输出到 stdout 供 OpenClaw 捕获
        print(f"TRANSCRIBED:{text}")
    else:
        print("未识别到语音")
        sys.exit(1)
