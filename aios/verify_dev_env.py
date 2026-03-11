#!/usr/bin/env python3
"""
太极OS (TaijiOS) - 开发环境验证脚本
检查所有必需的依赖和配置是否正确
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """打印成功信息"""
    print(f"✅ {text}")

def print_error(text):
    """打印错误信息"""
    print(f"❌ {text}")

def print_warning(text):
    """打印警告信息"""
    print(f"⚠️  {text}")

def check_python_version():
    """检查 Python 版本"""
    print_header("检查 Python 版本")
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 12:
        print_success("Python 版本符合要求 (>= 3.12)")
        return True
    else:
        print_error("Python 版本不符合要求，需要 >= 3.12")
        return False

def check_core_dependencies():
    """检查核心依赖"""
    print_header("检查核心依赖")
    
    dependencies = {
        'torch': 'PyTorch',
        'sentence_transformers': 'Sentence Transformers',
        'lancedb': 'LanceDB',
        'pydantic': 'Pydantic',
        'portalocker': 'Portalocker',
        'psutil': 'PSUtil',
        'requests': 'Requests',
        'yaml': 'PyYAML'
    }
    
    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_success(f"{name} 已安装")
        except ImportError:
            print_error(f"{name} 未安装")
            all_ok = False
    
    return all_ok

def check_optional_dependencies():
    """检查可选依赖"""
    print_header("检查可选依赖 (Dashboard)")
    
    dependencies = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'prometheus_client': 'Prometheus Client',
        'multipart': 'Python Multipart'
    }
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_success(f"{name} 已安装")
        except ImportError:
            print_warning(f"{name} 未安装 (可选)")

def check_torch_cuda():
    """检查 PyTorch CUDA 支持"""
    print_header("检查 PyTorch CUDA 支持")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        
        if cuda_available:
            print_success(f"CUDA 可用")
            print(f"   CUDA 版本: {torch.version.cuda}")
            print(f"   GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print_warning("CUDA 不可用，将使用 CPU")
            print("   如果你有 NVIDIA GPU，请安装 CUDA 版本的 PyTorch")
            print("   命令: pip install torch --index-url https://download.pytorch.org/whl/cu128")
        
        return True
    except Exception as e:
        print_error(f"检查 CUDA 时出错: {e}")
        return False

def check_project_structure():
    """检查项目结构"""
    print_header("检查项目结构")
    
    required_dirs = [
        'agent_system',
        'agent_system/core',
        'agent_system/agents',
        'agent_system/memory',
        'agent_system/data',
        'agent_system/docs',
        'agent_system/scripts',
        'agent_system/tests'
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists():
            print_success(f"{dir_path}/ 存在")
        else:
            print_error(f"{dir_path}/ 不存在")
            all_ok = False
    
    return all_ok

def check_key_files():
    """检查关键文件"""
    print_header("检查关键文件")
    
    required_files = [
        'requirements.txt',
        'agent_system/aios.py',
        'agent_system/heartbeat_v5.py',
        'agent_system/memory_server.py',
        'agent_system/agents.json'
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print_success(f"{file_path} 存在")
        else:
            print_error(f"{file_path} 不存在")
            all_ok = False
    
    return all_ok

def check_encoding():
    """检查编码配置"""
    print_header("检查编码配置")
    
    # 检查环境变量
    pythonutf8 = os.environ.get('PYTHONUTF8')
    pythonioencoding = os.environ.get('PYTHONIOENCODING')
    
    if pythonutf8 == '1':
        print_success("PYTHONUTF8=1 已设置")
    else:
        print_warning("PYTHONUTF8 未设置，建议设置为 1")
        print("   命令: $env:PYTHONUTF8=1")
    
    if pythonioencoding == 'utf-8':
        print_success("PYTHONIOENCODING=utf-8 已设置")
    else:
        print_warning("PYTHONIOENCODING 未设置，建议设置为 utf-8")
        print("   命令: $env:PYTHONIOENCODING='utf-8'")
    
    # 检查默认编码
    default_encoding = sys.getdefaultencoding()
    print(f"默认编码: {default_encoding}")
    
    if default_encoding == 'utf-8':
        print_success("默认编码为 UTF-8")
    else:
        print_warning(f"默认编码为 {default_encoding}，建议使用 UTF-8")

def check_memory_server():
    """检查 Memory Server 是否运行"""
    print_header("检查 Memory Server")
    
    try:
        import requests
        response = requests.get('http://127.0.0.1:7788/status', timeout=2)
        if response.status_code == 200:
            print_success("Memory Server 正在运行 (端口 7788)")
            return True
        else:
            print_warning("Memory Server 响应异常")
            return False
    except Exception:
        print_warning("Memory Server 未运行")
        print("   启动命令: python memory_server.py")
        return False

def check_dashboard():
    """检查 Dashboard 是否运行"""
    print_header("检查 Dashboard")
    
    try:
        import requests
        response = requests.get('http://127.0.0.1:8888', timeout=2)
        if response.status_code == 200:
            print_success("Dashboard 正在运行 (端口 8888)")
            return True
        else:
            print_warning("Dashboard 响应异常")
            return False
    except Exception:
        print_warning("Dashboard 未运行 (可选)")
        print("   启动命令: cd dashboard/AIOS-Dashboard-v3.4; python server.py")
        return False

def print_summary(results):
    """打印总结"""
    print_header("验证总结")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"总计: {total} 项检查")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    
    if failed == 0:
        print_success("\n所有检查通过！开发环境配置正确 ✨")
        return True
    else:
        print_error(f"\n有 {failed} 项检查失败，请根据上面的提示修复")
        return False

def main():
    """主函数"""
    print("\n太极OS (TaijiOS) - 开发环境验证")
    print("版本: v1.0")
    print("日期: 2026-03-10")
    
    results = {}
    
    # 运行所有检查
    results['Python 版本'] = check_python_version()
    results['核心依赖'] = check_core_dependencies()
    check_optional_dependencies()  # 可选依赖不计入结果
    results['PyTorch CUDA'] = check_torch_cuda()
    results['项目结构'] = check_project_structure()
    results['关键文件'] = check_key_files()
    check_encoding()  # 编码配置不计入结果
    check_memory_server()  # Memory Server 不计入结果
    check_dashboard()  # Dashboard 不计入结果
    
    # 打印总结
    success = print_summary(results)
    
    # 返回退出码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
