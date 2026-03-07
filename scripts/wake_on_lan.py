"""
Wake-on-LAN 脚本 - 远程唤醒电脑

使用方法：
1. 在 BIOS 中启用 Wake-on-LAN
2. 在网卡属性中启用"允许此设备唤醒计算机"
3. 获取目标电脑的 MAC 地址（ipconfig /all）
4. 运行此脚本：python wake_on_lan.py <MAC地址>
"""

import socket
import sys

def wake_on_lan(mac_address):
    """
    发送 WOL 魔术包唤醒电脑
    
    Args:
        mac_address: MAC 地址，格式如 "AA:BB:CC:DD:EE:FF" 或 "AA-BB-CC-DD-EE-FF"
    """
    # 移除分隔符
    mac_address = mac_address.replace(':', '').replace('-', '')
    
    # 验证 MAC 地址
    if len(mac_address) != 12:
        raise ValueError("Invalid MAC address")
    
    # 构建魔术包：6 个 0xFF + 16 次重复的 MAC 地址
    magic_packet = b'\xff' * 6 + bytes.fromhex(mac_address) * 16
    
    # 发送广播包
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ('<broadcast>', 9))
    
    print(f"✅ WOL 魔术包已发送到 {mac_address}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python wake_on_lan.py <MAC地址>")
        print("示例: python wake_on_lan.py AA:BB:CC:DD:EE:FF")
        sys.exit(1)
    
    try:
        wake_on_lan(sys.argv[1])
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
