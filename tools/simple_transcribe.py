#!/usr/bin/env python3
"""
简单转录音频 - 不依赖 ffmpeg
尝试直接读取 OGG 或使用系统工具
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def try_system_conversion(audio_path: str) -> str:
    """尝试使用系统工具转换音频"""
    wav_path = tempfile.mktemp(suffix='.wav')
    
    # 尝试不同的转换方法
    methods = [
        # 方法1: 使用 Python 音频库
        lambda: try_pydub_conversion(audio_path, wav_path),
        # 方法2: 使用系统命令
        lambda: try_system_command(audio_path, wav_path),
    ]
    
    for method in methods:
        try:
            result = method()
            if result and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                return wav_path
        except:
            continue
    
    return None

def try_pydub_conversion(audio_path: str, wav_path: str) -> bool:
    """使用 pydub 转换音频"""
    try:
        from pydub import AudioSegment
        
        print("尝试使用 pydub 转换音频...")
        audio = AudioSegment.from_file(audio_path)
        
        # 转换为单声道，16kHz
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        
        # 导出为 WAV
        audio.export(wav_path, format="wav")
        return True
        
    except ImportError:
        print("pydub 未安装，跳过此方法")
        return False
    except Exception as e:
        print(f"pydub 转换失败: {e}")
        return False

def try_system_command(audio_path: str, wav_path: str) -> bool:
    """尝试使用系统命令转换"""
    # 检查是否有可用的音频工具
    tools = ['ffmpeg', 'avconv', 'sox']
    
    for tool in tools:
        try:
            result = subprocess.run([tool, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"找到音频工具: {tool}")
                
                if tool == 'ffmpeg' or tool == 'avconv':
                    cmd = [
                        tool, '-i', audio_path,
                        '-ar', '16000',
                        '-ac', '1',
                        '-acodec', 'pcm_s16le',
                        '-y', wav_path
                    ]
                elif tool == 'sox':
                    cmd = [
                        tool, audio_path,
                        '-r', '16000',
                        '-c', '1',
                        '-b', '16',
                        wav_path
                    ]
                
                print(f"执行命令: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return True
                else:
                    print(f"{tool} 转换失败: {result.stderr}")
                    
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"{tool} 执行出错: {e}")
    
    return False

def transcribe_with_vosk(wav_path: str) -> str:
    """使用 vosk 转录音频"""
    try:
        from vosk import Model, KaldiRecognizer
        import wave
        import json
        
        # 模型路径
        model_path = r"C:\Users\A\.openclaw\models\vosk-cn"
        
        if not os.path.exists(model_path):
            print(f"模型路径不存在: {model_path}")
            return None
        
        print(f"加载模型: {model_path}")
        model = Model(model_path)
        
        # 打开音频文件
        wf = wave.open(wav_path, "rb")
        
        # 创建识别器
        rec = KaldiRecognizer(model, wf.getframerate())
        
        # 识别音频
        print("开始语音识别...")
        text_parts = []
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get("text"):
                    text_parts.append(result["text"])
        
        # 获取最终结果
        final_result = json.loads(rec.FinalResult())
        if final_result.get("text"):
            text_parts.append(final_result["text"])
        
        wf.close()
        
        # 合并结果
        full_text = " ".join(text_parts).strip()
        return full_text
        
    except Exception as e:
        print(f"语音识别失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python simple_transcribe.py <音频文件>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"文件不存在: {audio_path}")
        sys.exit(1)
    
    print(f"处理音频文件: {audio_path}")
    print(f"文件大小: {os.path.getsize(audio_path)} bytes")
    
    # 尝试转换音频
    wav_path = None
    try:
        wav_path = try_system_conversion(audio_path)
        
        if not wav_path or not os.path.exists(wav_path):
            print("音频转换失败")
            
            # 尝试直接读取（如果是 WAV 格式）
            if audio_path.lower().endswith('.wav'):
                print("尝试直接使用 WAV 文件...")
                wav_path = audio_path
            else:
                print("请安装 ffmpeg 或 pydub 来处理音频文件")
                print("安装命令:")
                print("  pip install pydub")
                print("  或")
                print("  winget install Gyan.FFmpeg")
                sys.exit(1)
        
        # 转录音频
        text = transcribe_with_vosk(wav_path)
        
        if text:
            print("\n" + "="*60)
            print("语音识别结果:")
            print("="*60)
            print(text)
            print("="*60)
            
            # 保存结果
            output_file = Path(audio_path).with_suffix('.txt')
            with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(text)
            print(f"结果已保存到: {output_file}")
            
            return text
        else:
            print("未能识别出文本")
            return None
            
    finally:
        # 清理临时文件
        if wav_path and wav_path != audio_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
                print(f"已清理临时文件: {wav_path}")
            except:
                pass

if __name__ == "__main__":
    main()