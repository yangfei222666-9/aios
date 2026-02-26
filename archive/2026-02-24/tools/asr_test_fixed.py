import wave, json, os, sys
from vosk import Model, KaldiRecognizer

MODEL = r"C:\Users\A\.openclaw\models\vosk-cn"
# 使用 logs 目录下的 TTS 文件，或者创建新的测试文件
WAV = r"C:\Users\A\.openclaw\workspace\logs\tts_test.mp3"  # 这是 MP3 格式

print("=== Vosk ASR 测试 ===")
print(f"模型路径: {MODEL}")
print(f"音频文件: {WAV}")

# 检查文件
if not os.path.isdir(MODEL):
    print("ERROR: 模型目录不存在")
    sys.exit(2)

if not os.path.isfile(WAV):
    print("ERROR: 音频文件不存在")
    print("请先运行 TTS 测试创建音频文件")
    sys.exit(3)

# 尝试直接使用文件（即使格式可能不对）
try:
    # 先尝试作为 WAV 打开
    wf = wave.open(WAV, "rb")
    print(f"WAV 信息: {wf.getnchannels()}ch, {wf.getframerate()}Hz, {wf.getsampwidth()*8}bit")
except wave.Error as e:
    print(f"WAV 格式错误: {e}")
    print("文件可能是 MP3 格式，需要转换为 WAV")
    sys.exit(4)

# 加载模型
print("加载模型...")
model = Model(MODEL)
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)

print("开始语音识别...")
parts = []
while True:
    data = wf.readframes(4000)
    if not data:
        break
    if rec.AcceptWaveform(data):
        j = json.loads(rec.Result())
        if j.get("text"):
            parts.append(j["text"])

j = json.loads(rec.FinalResult())
if j.get("text"):
    parts.append(j["text"])

text = " ".join(parts).strip()
print("识别结果:", text if text else "(empty)")
