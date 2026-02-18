import os, json, wave, sys, subprocess
from datetime import datetime
from pathlib import Path

def file_ok(p, min_size=1):
    return os.path.exists(p) and os.path.getsize(p) >= min_size

def run_encoding_check(project_root: Path) -> tuple[bool, str]:
    """
    返回 (ok, detail)
    ok=True 表示编码检查通过（exit 0）
    """
    py = sys.executable  # 当前 Python
    tool = project_root / "tools" / "simple_libcst_fix.py"
    
    if not tool.exists():
        return False, f"tool_not_found={tool}"
    
    cmd = [py, str(tool), str(project_root), "--dry-run"]
    
    try:
        p = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding="utf-8", 
            errors="replace"
        )
        ok = (p.returncode == 0)
        
        # detail 控制长度：只截前 200 字符，避免刷屏
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        tail = (err if err else out)[:200].replace("\n", " | ")
        detail = f"exit={p.returncode}" + (f" msg={tail}" if tail else "")
        
        return ok, detail
    except Exception as e:
        return False, f"exception={type(e).__name__}:{e}"

def tts_check():
    mp3 = r"logs\tts_test.mp3"
    if file_ok(mp3, 1000):
        return True, mp3, os.path.getsize(mp3)
    return False, mp3, (os.path.getsize(mp3) if os.path.exists(mp3) else 0)

def asr_check_strict():
    from vosk import Model, KaldiRecognizer
    
    model_path = r"C:\Users\A\.openclaw\models\vosk-cn"
    wav_path = r"logs\voice_16k_resampled.wav"
    
    if not os.path.isdir(model_path):
        return False, "model_missing", ""
    
    if not file_ok(wav_path, 1000):
        return False, "wav_missing", ""
    
    wf = wave.open(wav_path, "rb")
    model = Model(model_path)
    rec = KaldiRecognizer(model, wf.getframerate())
    
    texts = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            texts.append(json.loads(rec.Result()).get("text",""))
    
    texts.append(json.loads(rec.FinalResult()).get("text",""))
    text = " ".join([t for t in texts if t]).strip()
    
    # 文本规范化（解决零宽字符等问题）
    try:
        from tools.text_normalize import normalize_zh
        t = normalize_zh(text)
    except ImportError:
        # 回退方案：简单规范化
        import re
        import unicodedata
        t = unicodedata.normalize("NFC", text)
        t = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", t)
        t = re.sub(r"\s+", " ", t).strip()
    
    # === 简洁检查逻辑（带同音字处理）===
    # t = normalize_zh(asr_text)
    # has_xiaojiu = "小九" in t
    # has_yuyinshibie = ("语音识别" in t) or ("语音" in t and "识别" in t)
    # asr_ok = has_xiaojiu and has_yuyinshibie
    
    # 由于 ASR 可能将 "小九" 识别为 "小酒"，需要处理同音字
    # 检查 "小九" 或同音字变体
    has_xiaojiu = any(keyword in t for keyword in ["小九", "小酒"])
    has_yuyinshibie = ("语音识别" in t) or ("语音" in t and "识别" in t)
    ok = has_xiaojiu and has_yuyinshibie
    
    # 调试信息（仅在失败时显示）
    if not ok:
        print(f"DEBUG: 原始文本: {repr(text)}")
        print(f"DEBUG: 规范化文本: {repr(t)}")
        print(f"DEBUG: has_xiaojiu: {has_xiaojiu}")
        print(f"DEBUG: has_yuyinshibie: {has_yuyinshibie}")
    
    return ok, wav_path, text

def main():
    tts_ok, tts_path, tts_size = tts_check()
    asr_ok, asr_path, asr_text = asr_check_strict()
    
    # 编码检查（使用更准确的路径解析）
    project_root = Path(__file__).resolve().parents[1]  # tools/.. = 项目根
    encoding_ok, encoding_detail = run_encoding_check(project_root)
    
    tts_str = "OK" if tts_ok else "FAIL"
    asr_str = "OK" if asr_ok else "FAIL"
    encoding_str = "OK" if encoding_ok else "FAIL"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 一行摘要（给 daily_check / 写入 notes 用）
    print(f"daily_check | ASR={asr_str} TTS={tts_str} ENCODING={encoding_str} | tts={tts_size}B | asr_text=\"{asr_text[:80]}\" | {encoding_detail} | {now}")
    
    # 详细信息（需要时再看）
    print("DETAIL:")
    print(" TTS:", tts_str, tts_path, tts_size)
    print(" ASR:", asr_str, asr_path)
    print(" ASR_TEXT:", asr_text if asr_text else "(empty)")
    print(" ENCODING:", encoding_str, encoding_detail)
    
    # 退出码：编码失败就整体失败（exit 2），保持和现有体系一致
    if not encoding_ok:
        sys.exit(2)
    
    # 原有的 ASR/TTS 检查逻辑
    all_ok = tts_ok and asr_ok
    sys.exit(0 if all_ok else 2)

if __name__ == "__main__":
    main()
