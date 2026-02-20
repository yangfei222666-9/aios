import whisper, time, sys, io, torch

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

audio_path = sys.argv[1]

# Load model
t0 = time.time()
model = whisper.load_model('medium', device='cuda')
load_time = time.time() - t0

# Transcribe
t1 = time.time()
result = model.transcribe(audio_path, language='zh', no_speech_threshold=0.5)
transcribe_time = time.time() - t1

print(f"=== Whisper Medium + GPU (RTX 5070 Ti) ===")
print(f"Model load: {load_time:.2f}s")
print(f"Transcribe: {transcribe_time:.2f}s")
print(f"GPU mem: {torch.cuda.memory_allocated()/1024**2:.0f} MB")
print()
for seg in result['segments']:
    ns = seg['no_speech_prob']
    start = seg['start']
    end = seg['end']
    text = seg['text']
    print(f"[{start:.1f}-{end:.1f}] no_speech={ns:.3f} | {text}")
print()
print("FULL:", result['text'])
