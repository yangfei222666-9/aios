#!/usr/bin/env python3
"""
简单的 TTS 实现
使用 edge-tts 命令行工具
"""

import os
import sys
import tempfile
import subprocess
import threading
from pathlib import Path

class SimpleTTS:
    """简单的 TTS 实现"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.flag_path = os.path.join(self.workspace_dir, "logs", "tts_playing.flag")
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.flag_path), exist_ok=True)
        
        # 检查 edge-tts 是否可用
        self.edge_tts_available = self._check_edge_tts()
        
        print(f"TTS 初始化: edge-tts {'可用' if self.edge_tts_available else '不可用'}")
    
    def _check_edge_tts(self) -> bool:
        """检查 edge-tts 是否可用"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "edge_tts", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def create_flag(self):
        """创建 TTS 播放标志文件"""
        try:
            with open(self.flag_path, "w", encoding="utf-8", errors="replace") as f:
                f.write("tts_playing")
            return True
        except Exception as e:
            print(f"创建标志文件失败: {e}")
            return False
    
    def remove_flag(self):
        """移除 TTS 播放标志文件"""
        try:
            if os.path.exists(self.flag_path):
                os.remove(self.flag_path)
            return True
        except Exception as e:
            print(f"移除标志文件失败: {e}")
            return False
    
    def is_playing(self) -> bool:
        """检查 TTS 是否正在播放"""
        return os.path.exists(self.flag_path)
    
    def speak_with_edge_tts_cli(self, text: str) -> bool:
        """使用 edge-tts 命令行工具进行语音合成"""
        try:
            # 创建临时文件
            output_file = tempfile.mktemp(suffix='.mp3')
            
            # 构建命令
            cmd = [
                sys.executable, "-m", "edge_tts",
                "--voice", "zh-CN-XiaoxiaoNeural",
                "--text", text,
                "--write-media", output_file
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"edge-tts 合成失败: {result.stderr}")
                return False
            
            # 检查输出文件
            if not os.path.exists(output_file):
                print(f"输出文件未创建: {output_file}")
                return False
            
            # 播放音频
            self._play_audio(output_file)
            
            # 清理临时文件
            try:
                os.remove(output_file)
            except:
                pass
            
            return True
            
        except subprocess.TimeoutExpired:
            print("edge-tts 合成超时")
            return False
        except Exception as e:
            print(f"edge-tts 合成出错: {e}")
            return False
    
    def speak_with_system(self, text: str) -> bool:
        """使用系统 TTS（Windows）"""
        try:
            if sys.platform == "win32":
                # Windows 系统 TTS
                import win32com.client
                
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
                return True
            else:
                print(f"不支持的系统平台: {sys.platform}")
                return False
                
        except ImportError:
            print("pywin32 未安装，无法使用系统 TTS")
            return False
        except Exception as e:
            print(f"系统 TTS 失败: {e}")
            return False
    
    def _play_audio(self, audio_file: str):
        """播放音频文件"""
        try:
            if sys.platform == "win32":
                # Windows: 使用系统命令播放
                os.startfile(audio_file)
            else:
                print(f"不支持播放音频的平台: {sys.platform}")
                
        except Exception as e:
            print(f"播放音频失败: {e}")
    
    def speak(self, text: str, async_mode: bool = True) -> bool:
        """
        语音合成
        
        参数:
            text: 要合成的文本
            async_mode: 是否异步播放
        
        返回:
            bool: 是否成功
        """
        if not text:
            return False
        
        print(f"[TTS] 合成: '{text}'")
        
        # 创建标志文件
        if not self.create_flag():
            return False
        
        def _speak_task():
            """实际的语音合成任务"""
            try:
                # 尝试多种 TTS 方法
                success = False
                
                if self.edge_tts_available:
                    success = self.speak_with_edge_tts_cli(text)
                
                if not success and sys.platform == "win32":
                    success = self.speak_with_system(text)
                
                if not success:
                    print("[TTS] 所有方法都失败了")
                
            finally:
                # 无论成功与否，都移除标志文件
                self.remove_flag()
        
        try:
            if async_mode:
                # 异步播放
                thread = threading.Thread(target=_speak_task, daemon=True)
                thread.start()
                return True
            else:
                # 同步播放
                _speak_task()
                return True
                
        except Exception as e:
            print(f"[TTS] 语音合成出错: {e}")
            self.remove_flag()
            return False
    
    def speak_with_guard(self, text: str):
        """
        带防护的语音合成（上下文管理器）
        
        用法:
            with tts.speak_with_guard("你好"):
                # TTS 播放期间执行其他操作
                pass
        """
        class TTSGuard:
            def __init__(self, tts, text):
                self.tts = tts
                self.text = text
            
            def __enter__(self):
                if self.tts.create_flag():
                    # 异步播放
                    thread = threading.Thread(
                        target=self._speak_sync,
                        daemon=True
                    )
                    thread.start()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.tts.remove_flag()
            
            def _speak_sync(self):
                """同步语音合成"""
                if self.tts.edge_tts_available:
                    self.tts.speak_with_edge_tts_cli(self.text)
                elif sys.platform == "win32":
                    self.tts.speak_with_system(self.text)
        
        return TTSGuard(self, text)

def test_simple_tts():
    """测试简单的 TTS 功能"""
    print("简单 TTS 功能测试")
    print("=" * 60)
    
    tts = SimpleTTS()
    
    # 测试标志文件管理
    print("1. 测试标志文件管理...")
    tts.create_flag()
    print(f"   创建标志: {tts.is_playing()}")
    
    tts.remove_flag()
    print(f"   移除标志: {not tts.is_playing()}")
    
    # 测试语音合成
    print("\n2. 测试语音合成...")
    test_texts = [
        "我在，请说命令",
        "语音系统测试成功",
    ]
    
    for text in test_texts:
        print(f"   合成: '{text}'")
        success = tts.speak(text, async_mode=False)
        print(f"   结果: {'成功' if success else '失败'}")
    
    # 测试上下文管理器
    print("\n3. 测试上下文管理器...")
    with tts.speak_with_guard("测试上下文管理器"):
        print("   在 TTS 播放期间执行其他操作")
        print(f"   标志状态: {tts.is_playing()}")
    
    print(f"   播放后标志状态: {not tts.is_playing()}")
    
    print("\n" + "=" * 60)
    print("简单 TTS 测试完成")

if __name__ == "__main__":
    test_simple_tts()