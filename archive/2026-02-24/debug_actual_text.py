import json, wave
from vosk import Model, KaldiRecognizer
import re
import unicodedata

def normalize_zh(s: str) -> str:
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'[\u200b-\u200f\u2060\ufeff]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

model_path = r'C:\Users\A\.openclaw\models\vosk-cn'
wav_path = r'logs\voice_16k_resampled.wav'

wf = wave.open(wav_path, 'rb')
model = Model(model_path)
rec = KaldiRecognizer(model, wf.getframerate())

texts = []
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        text = result.get('text', '')
        if text:
            texts.append(text)

final = json.loads(rec.FinalResult())
final_text = final.get('text', '')
if final_text:
    texts.append(final_text)

text = ' '.join([t for t in texts if t]).strip()

print('=== 实际识别分析 ===')
print('原始文本:', repr(text))
print('文本长度:', len(text))
print()

# 规范化
normalized = normalize_zh(text)
print('规范化文本:', repr(normalized))
print('规范化长度:', len(normalized))
print()

# 检查包含关系
search_text = '小九'
print(f'检查 "{search_text}":')
print(f'  在原始文本中: {search_text in text}')
print(f'  在规范化文本中: {search_text in normalized}')
print()

# 详细字符分析
print('字符分析 (前20个):')
for i, char in enumerate(text):
    if i < 20:
        hex_code = f'U+{ord(char):04X}'
        print(f'  {i:2}: {repr(char):<6} {hex_code:8} ', end='')
        # 标记特殊字符
        if ord(char) < 32 or ord(char) > 126:
            print('(非ASCII)', end='')
        print()
print()

# 搜索所有位置
print(f'搜索 "{search_text}" 所有位置:')
found = False
for i in range(len(text) - len(search_text) + 1):
    if text[i:i+len(search_text)] == search_text:
        print(f'  在位置 {i} 找到')
        found = True
if not found:
    print('  未找到')
    
# 检查是否可能是其他字符
print()
print('检查位置 7-8 的字符:')
if len(text) >= 9:
    print(f'  text[7]: {repr(text[7])} (U+{ord(text[7]):04X})')
    print(f'  text[8]: {repr(text[8])} (U+{ord(text[8]):04X})')
    print(f'  text[7:9]: {repr(text[7:9])}')
    print(f'  等于 "小九": {text[7:9] == "小九"}')
else:
    print('  文本长度不足')