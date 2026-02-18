#!/usr/bin/env python3
"""
列出音频输入设备
"""

import sys

try:
    import sounddevice as sd
except ImportError:
    print("错误: 需要安装 sounddevice 库")
    print("运行: pip install sounddevice")
    sys.exit(1)

def list_input_devices():
    """列出所有音频输入设备"""
    print("=" * 60)
    print("音频输入设备列表")
    print("=" * 60)
    
    try:
        devices = sd.query_devices()
        input_count = 0
        
        for i, device in enumerate(devices):
            max_input = device.get('max_input_channels', 0)
            if max_input > 0:
                input_count += 1
                print(f"\n设备 #{i}: {device['name']}")
                print(f"  输入通道: {max_input}")
                print(f"  默认采样率: {device.get('default_samplerate', 'N/A')}")
                print(f"  设备ID: {i}")
                
                # 检查是否支持 16000Hz
                if 'default_samplerate' in device:
                    sr = device['default_samplerate']
                    if sr >= 16000:
                        print(f"  ✅ 支持 16000Hz (当前: {sr}Hz)")
                    else:
                        print(f"  ⚠️ 采样率可能过低: {sr}Hz")
        
        print(f"\n{'='*60}")
        print(f"找到 {input_count} 个输入设备")
        
        if input_count == 0:
            print("警告: 未找到音频输入设备!")
            print("请检查:")
            print("  1. 麦克风是否连接")
            print("  2. 音频驱动是否正常")
            print("  3. 系统音频设置")
        
        return input_count > 0
        
    except Exception as e:
        print(f"查询设备时出错: {e}")
        return False

def test_device(device_id=None):
    """测试指定设备"""
    print(f"\n{'='*60}")
    print(f"测试设备 #{device_id if device_id is not None else '默认'}")
    print("=" * 60)
    
    try:
        # 测试录音
        duration = 2  # 秒
        samplerate = 16000
        
        print(f"正在录制 {duration} 秒音频...")
        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype='int16',
            device=device_id
        )
        sd.wait()  # 等待录制完成
        
        print("✅ 录制成功!")
        print(f"  采样数: {len(recording)}")
        print(f"  时长: {len(recording)/samplerate:.2f}秒")
        
        # 计算能量
        import numpy as np
        energy = np.sqrt(np.mean(recording.astype(np.float32) ** 2))
        print(f"  平均能量: {energy:.6f}")
        
        if energy < 0.001:
            print("⚠️  能量过低，可能是静音或麦克风问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 列出设备
    has_devices = list_input_devices()
    
    if has_devices:
        # 询问是否测试
        print("\n是否测试默认设备? (y/n): ", end="")
        choice = input().strip().lower()
        
        if choice == 'y':
            test_device()
        
        # 询问是否测试特定设备
        print("\n是否测试特定设备? (输入设备ID或按回车跳过): ", end="")
        device_input = input().strip()
        
        if device_input.isdigit():
            test_device(int(device_input))