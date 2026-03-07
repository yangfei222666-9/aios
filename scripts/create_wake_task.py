"""
创建 Windows 定时唤醒任务

功能：
- 每天指定时间自动唤醒电脑（从睡眠/休眠状态）
- 注意：无法从完全关机状态唤醒（需要 BIOS 支持）

使用方法：
1. 以管理员身份运行此脚本
2. 设置唤醒时间
"""

import subprocess
import sys
from datetime import datetime, timedelta

def create_wake_task(wake_time="08:00"):
    """
    创建定时唤醒任务
    
    Args:
        wake_time: 唤醒时间，格式 "HH:MM"（24小时制）
    """
    task_name = "AutoWakeUp"
    
    # 删除旧任务（如果存在）
    subprocess.run(
        f'schtasks /Delete /TN "{task_name}" /F',
        shell=True,
        capture_output=True
    )
    
    # 创建新任务
    # /SC DAILY - 每天执行
    # /ST - 开始时间
    # /TR - 要执行的程序（这里用 cmd /c echo 作为占位符）
    # /RL HIGHEST - 最高权限
    # /F - 强制创建
    cmd = f'''schtasks /Create /TN "{task_name}" /SC DAILY /ST {wake_time} /TR "cmd /c echo Wake up" /RL HIGHEST /F'''
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ 定时唤醒任务已创建")
        print(f"   唤醒时间: 每天 {wake_time}")
        print(f"   任务名称: {task_name}")
        
        # 启用唤醒功能
        enable_wake_cmd = f'powercfg /WAKETIMERS'
        subprocess.run(enable_wake_cmd, shell=True)
        
        # 设置任务可以唤醒计算机
        xml_file = f"C:\\Windows\\Temp\\{task_name}.xml"
        export_cmd = f'schtasks /Query /TN "{task_name}" /XML > "{xml_file}"'
        subprocess.run(export_cmd, shell=True)
        
        # 读取 XML 并添加唤醒设置
        try:
            with open(xml_file, 'r', encoding='utf-16') as f:
                xml_content = f.read()
            
            # 添加 WakeToRun 标签
            if '<WakeToRun>true</WakeToRun>' not in xml_content:
                xml_content = xml_content.replace(
                    '</Settings>',
                    '  <WakeToRun>true</WakeToRun>\n  </Settings>'
                )
                
                with open(xml_file, 'w', encoding='utf-16') as f:
                    f.write(xml_content)
                
                # 重新导入任务
                import_cmd = f'schtasks /Create /TN "{task_name}" /XML "{xml_file}" /F'
                subprocess.run(import_cmd, shell=True)
                
                print("✅ 已启用唤醒功能")
        except Exception as e:
            print(f"⚠️  警告: 无法自动启用唤醒功能，请手动设置")
            print(f"   错误: {e}")
            print(f"\n手动设置步骤:")
            print(f"   1. 打开任务计划程序")
            print(f"   2. 找到任务 '{task_name}'")
            print(f"   3. 右键 → 属性 → 条件")
            print(f"   4. 勾选 '唤醒计算机运行此任务'")
        
        print(f"\n查看任务: schtasks /Query /TN \"{task_name}\" /V /FO LIST")
        print(f"删除任务: schtasks /Delete /TN \"{task_name}\" /F")
    else:
        print(f"❌ 创建任务失败")
        print(f"   错误: {result.stderr}")
        sys.exit(1)

def check_admin():
    """检查是否以管理员身份运行"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if not check_admin():
        print("❌ 请以管理员身份运行此脚本")
        print("   右键 → 以管理员身份运行")
        sys.exit(1)
    
    # 默认每天 8:00 唤醒
    wake_time = input("请输入唤醒时间（格式 HH:MM，默认 08:00）: ").strip() or "08:00"
    
    try:
        # 验证时间格式
        datetime.strptime(wake_time, "%H:%M")
        create_wake_task(wake_time)
    except ValueError:
        print("❌ 时间格式错误，请使用 HH:MM 格式（例如 08:00）")
        sys.exit(1)
