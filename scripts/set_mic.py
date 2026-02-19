"""设置 PD200X 为默认录音设备"""
import subprocess, sys

# 用 pycaw 设置默认音频设备
try:
    from pycaw.pycaw import AudioUtilities
    devices = AudioUtilities.GetAllDevices()
    for d in devices:
        print(f"  {d.FriendlyName} | {d.id}")
except ImportError:
    print("pycaw not installed, trying pip install...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pycaw', '-q'])
    from pycaw.pycaw import AudioUtilities
    devices = AudioUtilities.GetAllDevices()
    for d in devices:
        print(f"  {d.FriendlyName} | {d.id}")
