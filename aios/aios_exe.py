#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS CLI (EXE-compatible) - 命令行工具
直接 import 执行，不依赖外部 Python 解释器
"""
import sys
import os
import argparse
from pathlib import Path
import json
import time

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

# AIOS 根目录（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后
    AIOS_ROOT = Path(sys.executable).resolve().parent
else:
    AIOS_ROOT = Path(__file__).resolve().parent

sys.path.insert(0, str(AIOS_ROOT))


class AIOSCLI:
    """AIOS 命令行工具（EXE 兼容版）"""
    
    def __init__(self):
        self.aios_root = AIOS_ROOT
    
    def status(self):
        """查看 AIOS 状态"""
        print("=" * 60)
        print("AIOS 系统状态")
        print("=" * 60)
        
        # 检查组件状态
        print("\n📦 组件状态:")
        
        components = {
            "EventBus": self.aios_root / "core" / "event_bus.py",
            "Scheduler": self.aios_root / "core" / "production_scheduler.py",
            "Reactor": self.aios_root / "core" / "production_reactor.py",
            "Dashboard": self.aios_root / "dashboard" / "server.py",
        }
        
        for name, path in components.items():
            status = "✅" if path.exists() else "❌"
            print(f"   {status} {name}")
        
        # 检查性能数据
        perf_file = self.aios_root / "data" / "performance_stats.jsonl"
        if perf_file.exists():
            with open(perf_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n📊 性能数据: {len(lines)} 条记录")
        
        # 检查事件数据
        events_file = self.aios_root / "events" / "events.jsonl"
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📝 事件数据: {len(lines)} 条记录")
        
        print("\n" + "=" * 60)
    
    def demo(self, scenario=None):
        """运行演示（直接 import，不走 subprocess）"""
        print("🎬 AIOS 演示")
        print("=" * 60)
        
        if scenario is None:
            print("\n选择演示场景：")
            print("  1. 文件监控 + 自动分类（推荐，真实场景，20秒）")
            print("  2. API 健康检查 + 自动恢复（真实场景，20秒）")
            print("  3. 日志分析 + 自动生成 Playbook（真实场景，10秒）")
            print("\n默认运行场景 1（文件监控 + 自动分类）")
            print("=" * 60)
            scenario = "1"
        
        try:
            if scenario == "1":
                print("\n[Demo 1] 文件监控 + 自动分类")
                from demo_file_monitor import main as demo_main
                demo_main()
            elif scenario == "2":
                print("\n[Demo 2] API 健康检查 + 自动恢复")
                from demo_api_health import main as demo_main
                demo_main()
            elif scenario == "3":
                print("\n[Demo 3] 日志分析 + 自动生成 Playbook")
                from demo_log_analysis import main as demo_main
                demo_main()
            else:
                print(f"\n❌ 未知场景: {scenario}")
                return
            print("\n✅ 演示完成")
        except Exception as e:
            print(f"\n❌ 演示失败: {e}")
            import traceback
            traceback.print_exc()
    
    def version(self):
        """显示版本信息"""
        print("AIOS CLI v1.0 (EXE)")
        print("AIOS v0.6")
        print(f"路径: {self.aios_root}")
        frozen = "是" if getattr(sys, 'frozen', False) else "否"
        print(f"打包模式: {frozen}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AIOS CLI - 统一管理 AIOS 系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  AIOS status              查看系统状态
  AIOS demo                运行完整演示
  AIOS demo --scenario 2   运行 API 健康检查演示
  AIOS version             显示版本信息
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "demo", "version"],
        help="要执行的命令"
    )
    
    parser.add_argument(
        "--scenario",
        choices=["1", "2", "3"],
        help="演示场景（1=文件监控，2=API健康检查，3=日志分析）"
    )
    
    args = parser.parse_args()
    
    cli = AIOSCLI()
    
    if args.command == "status":
        cli.status()
    elif args.command == "demo":
        cli.demo(scenario=args.scenario)
    elif args.command == "version":
        cli.version()


if __name__ == "__main__":
    main()
