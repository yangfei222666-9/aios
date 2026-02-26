import wave, json, os, sys
from vosk import Model, KaldiRecognizer

MODEL = r"C:\Users\A\.openclaw\models\vosk-cn"
WAV = r"C:\Users\A\.openclaw\workspace\asr_test.wav"  # 使用新创建的 WAV 文件

print("=== Vosk ASR 测试 ===")
print(f"模型路径: {MODEL}")
print(f"音频文件: {WAV}")

# 检查文件
if not os.path.isdir(MODEL):
    print("ERROR: 模型目录不存在")
    sys.exit(2)

if not os.path.isfile(WAV):
    print("ERROR: 音频文件不存在")
    sys.exit(3)

try:
    # 打开 WAV 文件
    wf = wave.open(WAV, "rb")
    print(f"WAV 信息: {wf.getnchannels()}声道, {wf.getframerate()}Hz, {wf.getsampwidth()*8}位")
    print(f"总帧数: {wf.getnframes()}, 时长: {wf.getnframes()/wf.getframerate():.2f}秒")
    
except Exception as e:
    print(f"打开 WAV 文件失败: {e}")
    sys.exit(4)

# 加载模型
print("加载模型...")
try:
    model = Model(MODEL)
    print("模型加载成功")
except Exception as e:
    print(f"模型加载失败: {e}")
    sys.exit(5)

# 创建识别器
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)

print("开始语音识别...")
parts = []
frame_count = 0
while True:
    data = wf.readframes(4000)
    if not data:
        break
    
    frame_count += len(data) / (wf.getsampwidth() * wf.getnchannels())
    if rec.AcceptWaveform(data):
        j = json.loads(rec.Result())
        if j.get("text"):
            parts.append(j["text"])

# 获取最终结果
j = json.loads(rec.FinalResult())
if j.get("text"):
    parts.append(j["text"])

text = " ".join(parts).strip()
print("=" * 40)
print("识别结果:", text if text else "(empty)")
print("=" * 40)

wf.close()
