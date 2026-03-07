from paths import EVENTS_LOG
#!/usr/bin/env python3
"""
Camera Monitor Agent - Insta360 Link 2 Pro 鐩戞帶
鐩戞帶鎽勫儚澶寸姸鎬併€佹崟鑾风敾闈€佸姩浣滄娴?"""

import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys

# 娣诲姞 agent_system 鍒拌矾寰?sys.path.insert(0, str(Path(__file__).parent))

from data_collector import DataCollector

class CameraMonitorAgent:
    def __init__(self):
        self.agent_id = "camera-monitor"
        self.agent_name = "Camera_Monitor"
        self.dc = DataCollector()
        self.camera_name = "Insta360 Link 2 Pro"
        self.snapshot_dir = Path(__file__).parent.parent / "snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)
        
    def check_camera_status(self):
        """妫€鏌ユ憚鍍忓ご鏄惁杩炴帴"""
        try:
            # 浣跨敤 PowerShell 妫€鏌ユ憚鍍忓ご璁惧
            result = subprocess.run(
                ["powershell", "-Command", 
                 "Get-PnpDevice -Class Camera | Select-Object Status, FriendlyName | ConvertTo-Json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                devices = json.loads(result.stdout)
                if not isinstance(devices, list):
                    devices = [devices]
                
                for device in devices:
                    if "Insta360" in device.get("FriendlyName", ""):
                        status = device.get("Status", "Unknown")
                        return {
                            "connected": status == "OK",
                            "status": status,
                            "name": device.get("FriendlyName")
                        }
                
                return {"connected": False, "status": "Not Found", "name": None}
            else:
                return {"connected": False, "status": "Error", "error": result.stderr}
                
        except Exception as e:
            return {"connected": False, "status": "Error", "error": str(e)}
    
    def capture_snapshot(self):
        """鎹曡幏鎽勫儚澶寸敾闈?""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.snapshot_dir / f"snapshot_{timestamp}.jpg"
            
            # 浣跨敤 FFmpeg 鎹曡幏鐢婚潰锛堥渶瑕佸畨瑁?FFmpeg锛?            # 濡傛灉娌℃湁 FFmpeg锛屽彲浠ョ敤 OpenCV 鎴栧叾浠栧伐鍏?            result = subprocess.run(
                ["ffmpeg", "-f", "dshow", "-i", f"video={self.camera_name}",
                 "-frames:v", "1", "-y", str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and output_file.exists():
                return {
                    "success": True,
                    "file": str(output_file),
                    "size": output_file.stat().st_size
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "error": "FFmpeg not found. Please install FFmpeg or use alternative capture method."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_monitoring_cycle(self):
        """杩愯涓€娆＄洃鎺у懆鏈?""
        task_id = f"camera-monitor-{int(time.time())}"
        start_time = time.time()
        
        try:
            # 1. 妫€鏌ユ憚鍍忓ご鐘舵€?            status = self.check_camera_status()
            
            # 2. 濡傛灉杩炴帴姝ｅ父锛屽皾璇曟崟鑾风敾闈?            snapshot_result = None
            if status["connected"]:
                snapshot_result = self.capture_snapshot()
            
            # 3. 璁板綍浠诲姟瀹屾垚
            duration_ms = int((time.time() - start_time) * 1000)
            
            event = self.dc.collect_task_event(
                task_id=task_id,
                task_type="camera_monitoring",
                description=f"Monitor {self.camera_name}",
                priority="normal",
                status="completed" if status["connected"] else "failed",
                duration_ms=duration_ms,
                metadata={
                    "camera_status": status,
                    "snapshot": snapshot_result
                }
            )
            
            # 鍐欏叆浜嬩欢鏃ュ織
            events_file = EVENTS_LOG
            events_file.parent.mkdir(parents=True, exist_ok=True)
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            
            return {
                "success": True,
                "camera_status": status,
                "snapshot": snapshot_result,
                "duration": duration_ms / 1000
            }
            
        except Exception as e:
            # 璁板綍澶辫触
            duration_ms = int((time.time() - start_time) * 1000)
            
            event = self.dc.collect_task_event(
                task_id=task_id,
                task_type="camera_monitoring",
                description=f"Monitor {self.camera_name}",
                priority="normal",
                status="failed",
                duration_ms=duration_ms,
                error_type="exception",
                error_message=str(e)
            )
            
            # 鍐欏叆浜嬩欢鏃ュ織
            events_file = EVENTS_LOG
            events_file.parent.mkdir(parents=True, exist_ok=True)
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            
            return {
                "success": False,
                "error": str(e),
                "duration": duration_ms / 1000
            }

def main():
    """涓诲嚱鏁?""
    agent = CameraMonitorAgent()
    result = agent.run_monitoring_cycle()
    
    # 杈撳嚭缁撴灉
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 杩斿洖鐘舵€佺爜
    return 0 if result["success"] else 1

if __name__ == "__main__":
    sys.exit(main())


