#!/usr/bin/env python3
"""
语音系统启动脚本
确保正确的编码配置和系统初始化
"""

import sys
import os
import argparse
from pathlib import Path

def setup_encoding():
    """设置编码配置"""
    # 强制使用 UTF-8 编码
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            print("[编码配置] 标准输出已设置为 UTF-8")
        except AttributeError:
            # Python 3.7 以下版本
            import io
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace'
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding='utf-8',
                errors='replace'
            )
            print("[编码配置] 标准输出已替换为 UTF-8 包装器")
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    print(f"[编码配置] 当前编码: {sys.stdout.encoding}")

def check_dependencies():
    """检查依赖"""
    print("\n[依赖检查] 检查系统依赖...")
    
    dependencies = [
        ("vosk", "vosk", "语音识别"),
        ("sounddevice", "sounddevice", "音频输入"),
        ("numpy", "numpy", "数值计算"),
        ("yaml", "yaml", "配置解析"),
        ("edge_tts", "edge-tts", "语音合成"),
    ]
    
    missing = []
    
    for import_name, package_name, description in dependencies:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}: {description}")
        except ImportError:
            print(f"  ❌ {package_name}: {description} (未安装)")
            missing.append(package_name)
    
    if missing:
        print(f"\n[警告] 缺少 {len(missing)} 个依赖:")
        for package in missing:
            print(f"  pip install {package}")
        return False
    
    print("[依赖检查] 所有依赖已安装")
    return True

def setup_directories():
    """设置必要的目录"""
    print("\n[目录设置] 检查工作目录...")
    
    directories = [
        "notes",
        "logs",
        "tools",
        "models",
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  创建: {directory}/")
        else:
            print(f"  存在: {directory}/")
    
    # 检查模型目录
    model_path = Path("models/vosk-cn")
    if not model_path.exists():
        print(f"\n[警告] 语音识别模型未找到: {model_path}")
        print("  请下载模型: https://alphacephei.com/vosk/models")
        print("  并解压到: models/vosk-cn/")
        return False
    
    print("[目录设置] 目录结构正常")
    return True

def start_wake_listener(config_path: str = "openclaw.yaml"):
    """启动语音唤醒监听器"""
    print(f"\n[系统启动] 启动语音唤醒服务...")
    print(f"  配置文件: {config_path}")
    
    try:
        # 导入并启动服务
        from tools.wake_listener import main as wake_main
        
        # 修改 sys.argv 以传递配置路径
        original_argv = sys.argv.copy()
        sys.argv = [sys.argv[0], config_path]
        
        try:
            wake_main()
        finally:
            sys.argv = original_argv
            
    except KeyboardInterrupt:
        print("\n[系统停止] 收到中断信号，正在退出...")
    except Exception as e:
        print(f"\n[系统错误] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_system():
    """测试系统功能"""
    print("\n[系统测试] 运行功能测试...")
    
    tests = [
        ("Unicode 清理", "tools/unicode_sanitizer.py"),
        ("命令路由器", "tools/command_router.py"),
        ("语音命令处理器", "tools/voice_command_handler_integrated.py"),
    ]
    
    all_passed = True
    
    for test_name, test_script in tests:
        if not Path(test_script).exists():
            print(f"  ❌ {test_name}: 脚本不存在")
            all_passed = False
            continue
        
        print(f"  运行: {test_name}...")
        
        import subprocess
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"  ✅ {test_name}: 通过")
        else:
            print(f"  ❌ {test_name}: 失败")
            print(f"     错误: {result.stderr[:100]}...")
            all_passed = False
    
    if all_passed:
        print("[系统测试] 所有测试通过！")
    else:
        print("[系统测试] 部分测试失败")
    
    return all_passed

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="语音系统启动脚本")
    parser.add_argument("--config", default="openclaw.yaml", help="配置文件路径")
    parser.add_argument("--test", action="store_true", help="只运行测试，不启动服务")
    parser.add_argument("--list-devices", action="store_true", help="列出音频设备")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("语音唤醒系统启动")
    print("=" * 60)
    
    # 1. 设置编码
    setup_encoding()
    
    # 2. 检查依赖
    if not check_dependencies():
        print("\n[错误] 缺少必要依赖，请先安装")
        return 1
    
    # 3. 设置目录
    if not setup_directories():
        print("\n[警告] 目录设置有问题，但继续启动...")
    
    # 4. 列出设备（如果请求）
    if args.list_devices:
        print("\n[设备列表] 音频输入设备:")
        from tools.wake_listener import list_input_devices
        list_input_devices()
        return 0
    
    # 5. 测试系统（如果请求）
    if args.test:
        success = test_system()
        return 0 if success else 1
    
    # 6. 启动服务
    print("\n" + "=" * 60)
    print("系统状态总结:")
    print("=" * 60)
    print("✅ 编码配置完成")
    print("✅ 依赖检查通过")
    print("✅ 目录结构正常")
    print("🚀 准备启动语音唤醒服务")
    print()
    print("使用说明:")
    print("  1. 说唤醒词: '小九', '小酒', '你好小九'")
    print("  2. 听系统回应: '我在，请说命令'")
    print("  3. 说命令: '检查系统状态', '添加笔记', '现在几点'等")
    print("  4. 系统执行命令并记录结果")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动服务
    return 0 if start_wake_listener(args.config) else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[系统] 启动过程被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[系统错误] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)