"""
Demo 2: Windows 登录表单

演示如何使用 RPA Vision 自动化 Windows 应用登录：
1. 找"用户名"标签
2. 找相邻输入框
3. 输入用户名
4. 输入密码
5. 点击登录
6. 等待结果
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import RPAVision


def main():
    print("=== Demo 2: Windows 登录表单 ===\n")
    
    # 初始化 RPA Vision
    rpa = RPAVision(debug_mode=True, dry_run=False)
    
    print("步骤 1: 请打开一个包含登录表单的应用")
    print("（可以是网页登录页、桌面应用登录窗口等）")
    input("准备好后按 Enter 继续...")
    
    try:
        # 步骤 2: 截图并 OCR
        print("\n步骤 2: 识别表单元素...")
        rpa.capture_screen()
        ocr_result = rpa.extract_text()
        
        print(f"✓ 识别到 {len(ocr_result)} 个文本元素")
        
        # 步骤 3: 查找"用户名"标签
        print("\n步骤 3: 查找用户名输入框...")
        username_label = rpa.find_text("用户名", fuzzy=True)
        if not username_label:
            username_label = rpa.find_text("Username", fuzzy=True)
        if not username_label:
            username_label = rpa.find_text("账号", fuzzy=True)
        
        if username_label:
            print(f"✓ 找到标签: {username_label['text']}")
            
            # 查找相邻输入框
            input_pos = rpa.find_nearest_input(username_label["bbox"])
            
            if input_pos:
                print(f"✓ 找到输入框位置: {input_pos}")
                
                # 步骤 4: 输入用户名
                print("\n步骤 4: 输入用户名...")
                rpa.click(input_pos[0], input_pos[1])
                username = "demo_user"
                rpa.type_text(username)
                print(f"✓ 已输入: {username}")
            else:
                print("⚠ 未找到输入框，尝试直接点击标签右侧...")
                x1, y1, x2, y2 = username_label["bbox"]
                rpa.click(x2 + 50, (y1 + y2) // 2)
                username = "demo_user"
                rpa.type_text(username)
                print(f"✓ 已输入: {username}")
        
        else:
            print("✗ 未找到用户名标签")
            print("提示: 请确保登录表单可见且包含'用户名'或'Username'文本")
            return
        
        # 步骤 5: 查找密码输入框
        print("\n步骤 5: 查找密码输入框...")
        password_label = rpa.find_text("密码", fuzzy=True)
        if not password_label:
            password_label = rpa.find_text("Password", fuzzy=True)
        
        if password_label:
            print(f"✓ 找到标签: {password_label['text']}")
            
            # 查找相邻输入框
            input_pos = rpa.find_nearest_input(password_label["bbox"])
            
            if input_pos:
                print(f"✓ 找到输入框位置: {input_pos}")
                
                # 输入密码
                print("\n步骤 6: 输入密码...")
                rpa.click(input_pos[0], input_pos[1])
                password = "demo_password"
                rpa.type_text(password)
                print(f"✓ 已输入: {password}")
            else:
                print("⚠ 未找到输入框，尝试直接点击标签右侧...")
                x1, y1, x2, y2 = password_label["bbox"]
                rpa.click(x2 + 50, (y1 + y2) // 2)
                password = "demo_password"
                rpa.type_text(password)
                print(f"✓ 已输入: {password}")
        
        # 步骤 7: 查找登录按钮
        print("\n步骤 7: 查找登录按钮...")
        login_button = rpa.find_text("登录", fuzzy=True)
        if not login_button:
            login_button = rpa.find_text("Login", fuzzy=True)
        if not login_button:
            login_button = rpa.find_text("Sign In", fuzzy=True)
        
        if login_button:
            print(f"✓ 找到按钮: {login_button['text']}")
            
            # 点击登录
            print("\n步骤 8: 点击登录...")
            rpa.click_text(login_button["text"])
            print("✓ 已点击登录")
            
            # 步骤 9: 等待结果
            print("\n步骤 9: 等待登录结果...")
            if rpa.wait_for_text("成功", timeout=10, fuzzy=True):
                print("✓ 登录成功！")
            elif rpa.wait_for_text("错误", timeout=5, fuzzy=True):
                print("⚠ 登录失败（检测到错误提示）")
            else:
                print("⚠ 未检测到明确的结果提示")
        
        else:
            print("✗ 未找到登录按钮")
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n调试输出已保存到: {rpa.debug.output_dir}")
        print("可以查看截图、OCR 结果和动作日志")


if __name__ == "__main__":
    main()
