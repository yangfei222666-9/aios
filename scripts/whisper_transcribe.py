import whisper, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

audio_path = sys.argv[1]
model = whisper.load_model('small')
result = model.transcribe(audio_path, language='zh', no_speech_threshold=0.5)

for seg in result['segments']:
    ns = seg['no_speech_prob']
    print(f"[{seg['start']:.1f}-{seg['end']:.1f}] no_speech={ns:.3f} | {seg['text']}")

print("FULL:", result['text'])
