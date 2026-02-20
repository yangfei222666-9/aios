# scripts/whisper_transcribe.py - Whisper 语音转文字
"""
v2: faster-whisper + large-v3 (GPU)
- 比原版 openai-whisper 快 2-4x
- large-v3 中文准确率更高
- 首次运行自动下载模型 (~3GB)
"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from faster_whisper import WhisperModel

MODEL_SIZE = "large-v3"
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"  # 比 float16 快 30-40%

def transcribe(audio_path, language="zh"):
    t0 = time.time()
    
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    load_time = time.time() - t0
    
    t1 = time.time()
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        no_speech_threshold=0.5,
        vad_filter=True,  # VAD 过滤静音段
    )
    
    full_text = []
    for seg in segments:
        print(f"[{seg.start:.1f}-{seg.end:.1f}] no_speech={seg.no_speech_prob:.3f} | {seg.text}")
        full_text.append(seg.text)
    
    transcribe_time = time.time() - t1
    result = "".join(full_text).strip()
    
    print(f"\nFULL: {result}")
    print(f"\n--- model={MODEL_SIZE} device={DEVICE} load={load_time:.1f}s transcribe={transcribe_time:.1f}s lang={info.language} prob={info.language_probability:.2f} ---")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python whisper_transcribe.py <audio_file> [language]")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "zh"
    transcribe(audio_path, lang)
