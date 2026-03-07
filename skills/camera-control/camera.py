#!/usr/bin/env python3
"""
Camera Control - 摄像头控制工具
支持拍照、监控、分析三大功能
"""

# Windows GBK 编码修复（Phase 3 学习应用）
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import argparse
import cv2
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Phase 3 经验学习集成
try:
    from experience_library import experience
    PHASE3_ENABLED = True
except ImportError:
    PHASE3_ENABLED = False
    print("[WARN] Phase 3 experience learning not available")


class CameraController:
    """摄像头控制器"""
    
    def __init__(self, device_id: int = 0, output_dir: str = "./snapshots"):
        self.device_id = device_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.camera = None
        
    def open_camera(self) -> bool:
        """打开摄像头"""
        try:
            self.camera = cv2.VideoCapture(self.device_id)
            if not self.camera.isOpened():
                print(f"❌ 无法打开摄像头 (device {self.device_id})", file=sys.stderr)
                return False
            
            # 设置分辨率（可选）
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            return True
        except Exception as e:
            print(f"❌ 打开摄像头失败: {e}", file=sys.stderr)
            return False
    
    def close_camera(self):
        """关闭摄像头"""
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def capture_frame(self) -> Optional[Tuple[bool, any]]:
        """捕获一帧"""
        if not self.camera:
            return None
        
        ret, frame = self.camera.read()
        return (ret, frame) if ret else None
    
    def save_frame(self, frame, filename: str) -> str:
        """保存帧到文件"""
        filepath = self.output_dir / filename
        cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return str(filepath)
    
    def snap(self) -> Optional[str]:
        """拍摄单张照片"""
        if not self.open_camera():
            return None
        
        try:
            # 预热摄像头（丢弃前几帧）
            for _ in range(5):
                self.camera.read()
            
            # 捕获照片
            result = self.capture_frame()
            if not result:
                print("❌ 捕获照片失败", file=sys.stderr)
                return None
            
            ret, frame = result
            
            # 保存照片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
            filepath = self.save_frame(frame, filename)
            
            print(f"✅ 已保存照片: {filepath}")
            return filepath
            
        finally:
            self.close_camera()
    
    def watch(self, interval: int = 5, duration: int = 60) -> int:
        """监控模式（连续拍照）"""
        if not self.open_camera():
            return 0
        
        try:
            import time
            
            start_time = time.time()
            count = 0
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            print(f"🎥 开始监控 (间隔: {interval}秒, 时长: {duration}秒)")
            
            while True:
                # 检查是否超时
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
                
                # 捕获照片
                result = self.capture_frame()
                if result:
                    ret, frame = result
                    count += 1
                    filename = f"watch_{session_id}_{count:03d}.jpg"
                    filepath = self.save_frame(frame, filename)
                    print(f"📸 [{count}] {filepath}")
                
                # 等待间隔
                time.sleep(interval)
            
            print(f"✅ 监控完成，共拍摄 {count} 张照片")
            return count
            
        except KeyboardInterrupt:
            print(f"\n⚠️ 监控中断，已拍摄 {count} 张照片")
            return count
        finally:
            self.close_camera()
    
    def analyze(self, prompt: str = "描述这个画面中的内容") -> Optional[dict]:
        """分析画面内容（已集成 Phase 3 经验学习）"""
        start_time = time.time()
        
        # 先拍照
        if not self.open_camera():
            # ============== Phase 3 自动学习钩子（摄像头打开失败）==============
            if PHASE3_ENABLED:
                error = Exception(f"无法打开摄像头 (device {self.device_id})")
                experience.record_failure(
                    task_id="camera_analyze",
                    error=error,
                    context={
                        "delay": time.time() - start_time,
                        "suggest": "检查摄像头设备ID、驱动或权限",
                        "prompt_used": prompt,
                        "device_id": self.device_id
                    }
                )
            # ================================================================
            return None
        
        try:
            # 预热摄像头
            for _ in range(5):
                self.camera.read()
            
            # 捕获照片
            result = self.capture_frame()
            if not result:
                error = Exception("无法捕获画面")
                
                # ============== Phase 3 自动学习钩子 ==============
                if PHASE3_ENABLED:
                    experience.record_failure(
                        task_id="camera_analyze",
                        error=error,
                        context={
                            "delay": time.time() - start_time,
                            "suggest": "检查摄像头连接、光线或 prompt 长度",
                            "prompt_used": prompt
                        }
                    )
                # =================================================
                
                print("❌ 捕获照片失败", file=sys.stderr)
                return None
            
            ret, frame = result
            
            # 保存照片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analyze_{timestamp}.jpg"
            filepath = self.save_frame(frame, filename)
            
            print(f"✅ 已保存照片: {filepath}")
            
            # 调用 OpenClaw 的 image 工具分析
            # 注意：这里需要通过 OpenClaw 的 image 工具来分析
            # 在实际使用时，应该由 OpenClaw 调用这个脚本，然后再调用 image 工具
            print(f"\n📝 分析提示: {prompt}")
            print(f"📷 照片路径: {filepath}")
            print("\n💡 提示: 请使用 OpenClaw 的 image 工具分析这张照片")
            
            # ============== Phase 3 成功记录 ==============
            if PHASE3_ENABLED:
                duration = time.time() - start_time
                experience.record_success(
                    task_id="camera_analyze",
                    strategy="capture_and_save",
                    duration=duration,
                    success_rate=1.0
                )
            # ==============================================
            
            return {
                "filepath": filepath,
                "prompt": prompt,
                "timestamp": timestamp
            }
            
        except Exception as e:
            # ============== Phase 3 异常学习钩子 ==============
            if PHASE3_ENABLED:
                experience.record_failure(
                    task_id="camera_analyze",
                    error=e,
                    context={
                        "delay": time.time() - start_time,
                        "suggest": "检查摄像头驱动、权限或系统资源",
                        "prompt_used": prompt
                    }
                )
            # =================================================
            
            print(f"❌ 分析失败: {e}", file=sys.stderr)
            raise
            
        finally:
            self.close_camera()


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(description="Camera Control - 摄像头控制工具")
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # snap 命令
    snap_parser = subparsers.add_parser('snap', help='拍摄单张照片')
    snap_parser.add_argument('--device', type=int, default=0, help='摄像头设备ID')
    snap_parser.add_argument('--output', type=str, default='./snapshots', help='保存路径')
    
    # watch 命令
    watch_parser = subparsers.add_parser('watch', help='监控模式（连续拍照）')
    watch_parser.add_argument('--device', type=int, default=0, help='摄像头设备ID')
    watch_parser.add_argument('--interval', type=int, default=5, help='拍照间隔（秒）')
    watch_parser.add_argument('--duration', type=int, default=60, help='监控时长（秒，0表示无限）')
    watch_parser.add_argument('--output', type=str, default='./snapshots', help='保存路径')
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析画面内容')
    analyze_parser.add_argument('--device', type=int, default=0, help='摄像头设备ID')
    analyze_parser.add_argument('--prompt', type=str, default='描述这个画面中的内容', help='分析提示词')
    analyze_parser.add_argument('--output', type=str, default='./snapshots', help='保存路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 加载配置
    config = load_config()
    
    # 创建控制器
    device_id = args.device if hasattr(args, 'device') else config.get('default_device', 0)
    output_dir = args.output if hasattr(args, 'output') else config.get('default_output', './snapshots')
    
    controller = CameraController(device_id, output_dir)
    
    # 执行命令
    if args.command == 'snap':
        result = controller.snap()
        return 0 if result else 1
        
    elif args.command == 'watch':
        interval = args.interval if hasattr(args, 'interval') else config.get('default_interval', 5)
        duration = args.duration if hasattr(args, 'duration') else config.get('default_duration', 60)
        count = controller.watch(interval, duration)
        return 0 if count > 0 else 1
        
    elif args.command == 'analyze':
        prompt = args.prompt if hasattr(args, 'prompt') else "描述这个画面中的内容"
        result = controller.analyze(prompt)
        return 0 if result else 1
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
