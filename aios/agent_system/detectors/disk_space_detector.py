"""
磁盘空间检测器 v0 (Capacity)

监控磁盘剩余空间，识别资源耗尽风险。

核心能力：
1. 检查系统盘 + 工作目录所在盘
2. 双阈值判断（百分比 + 绝对值）
3. 三级状态：healthy / warn / critical
4. 只报警，不自动清理

阈值规则：
- warn:     剩余 < 15% 或 < 20GB
- critical: 剩余 < 8%  或 < 10GB
"""

import json
import time
import shutil
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


# 默认阈值
WARN_PERCENT = 15.0
WARN_GB = 20.0
CRITICAL_PERCENT = 8.0
CRITICAL_GB = 10.0

# 太极OS 工作目录
WORKSPACE_DIR = r"C:\Users\A\.openclaw\workspace"


class DiskSpaceDetector:
    """磁盘空间检测器"""

    def __init__(
        self,
        warn_percent: float = WARN_PERCENT,
        warn_gb: float = WARN_GB,
        critical_percent: float = CRITICAL_PERCENT,
        critical_gb: float = CRITICAL_GB,
    ):
        self.warn_percent = warn_percent
        self.warn_gb = warn_gb
        self.critical_percent = critical_percent
        self.critical_gb = critical_gb

    def _get_target_drives(self) -> List[str]:
        """获取需要监控的盘符（系统盘 + 工作目录所在盘，去重）"""
        drives = set()

        # 系统盘
        sys_drive = os.environ.get("SystemDrive", "C:")
        drives.add(sys_drive.rstrip("\\").upper())

        # 工作目录所在盘
        workspace_drive = os.path.splitdrive(WORKSPACE_DIR)[0].upper()
        if workspace_drive:
            drives.add(workspace_drive)

        return sorted(drives)

    def _check_drive(self, drive: str) -> Dict[str, Any]:
        """
        检查单个盘符的磁盘空间

        Returns:
            {
                "drive": str,
                "status": "healthy" | "warn" | "critical" | "error",
                "severity": "info" | "warning" | "critical" | "error",
                "total_bytes": int,
                "free_bytes": int,
                "free_gb": float,
                "free_percent": float,
                "threshold_triggered": str | None,
                "suggested_action": str | None,
                "error": str | None,
            }
        """
        drive_path = drive + "\\"
        try:
            usage = shutil.disk_usage(drive_path)
        except (OSError, FileNotFoundError) as e:
            return {
                "drive": drive,
                "status": "error",
                "severity": "error",
                "total_bytes": 0,
                "free_bytes": 0,
                "free_gb": 0.0,
                "free_percent": 0.0,
                "threshold_triggered": None,
                "suggested_action": None,
                "error": str(e),
            }

        total = usage.total
        free = usage.free
        free_gb = round(free / (1024 ** 3), 2)
        free_percent = round((free / total) * 100, 2) if total > 0 else 0.0

        # 判断状态（双阈值：百分比 OR 绝对值）
        is_critical = free_percent < self.critical_percent or free_gb < self.critical_gb
        is_warn = free_percent < self.warn_percent or free_gb < self.warn_gb

        if is_critical:
            status = "critical"
            severity = "critical"
            if free_percent < self.critical_percent and free_gb < self.critical_gb:
                threshold_triggered = f"percent<{self.critical_percent}% AND gb<{self.critical_gb}GB"
            elif free_percent < self.critical_percent:
                threshold_triggered = f"percent<{self.critical_percent}%"
            else:
                threshold_triggered = f"gb<{self.critical_gb}GB"
            suggested_action = "检查 logs / archive / temp，考虑创建清理任务"
        elif is_warn:
            status = "warn"
            severity = "warning"
            if free_percent < self.warn_percent and free_gb < self.warn_gb:
                threshold_triggered = f"percent<{self.warn_percent}% AND gb<{self.warn_gb}GB"
            elif free_percent < self.warn_percent:
                threshold_triggered = f"percent<{self.warn_percent}%"
            else:
                threshold_triggered = f"gb<{self.warn_gb}GB"
            suggested_action = "标记 observation，关注空间变化趋势"
        else:
            status = "healthy"
            severity = "info"
            threshold_triggered = None
            suggested_action = None

        return {
            "drive": drive,
            "status": status,
            "severity": severity,
            "total_bytes": total,
            "free_bytes": free,
            "free_gb": free_gb,
            "free_percent": free_percent,
            "threshold_triggered": threshold_triggered,
            "suggested_action": suggested_action,
            "error": None,
        }

    def check(self) -> Dict[str, Any]:
        """
        检查所有目标盘符

        Returns:
            {
                "overall_status": "healthy" | "warn" | "critical",
                "drives": [drive_result, ...],
                "timestamp": str,
            }
        """
        drives = self._get_target_drives()
        results = [self._check_drive(d) for d in drives]

        # 整体状态取最严重的
        statuses = [r["status"] for r in results]
        if "critical" in statuses:
            overall = "critical"
        elif "warn" in statuses:
            overall = "warn"
        elif "error" in statuses:
            overall = "warn"
        else:
            overall = "healthy"

        return {
            "overall_status": overall,
            "drives": results,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_event(self, drive_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从单盘检查结果生成标准事件（仅 warn/critical 生成）

        Returns:
            标准事件对象，healthy 返回 None
        """
        status = drive_result["status"]
        if status == "healthy":
            return None

        drive = drive_result["drive"]
        free_gb = drive_result["free_gb"]
        free_percent = drive_result["free_percent"]
        severity = drive_result["severity"]

        if status == "critical":
            summary = f"磁盘 {drive} 空间严重不足 (剩余 {free_gb}GB, {free_percent}%)"
        elif status == "warn":
            summary = f"磁盘 {drive} 空间偏低 (剩余 {free_gb}GB, {free_percent}%)"
        else:
            summary = f"磁盘 {drive} 检查异常: {drive_result.get('error', 'unknown')}"

        return {
            "event_id": f"evt-disk-space-{drive.replace(':', '')}-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "source": "health_check_v3_1",
            "entity_type": "disk",
            "entity_id": drive,
            "event_type": "disk_space_low",
            "severity": severity,
            "status": "detected",
            "summary": summary,
            "evidence": {
                "free_bytes": drive_result["free_bytes"],
                "free_gb": free_gb,
                "free_percent": free_percent,
                "total_bytes": drive_result["total_bytes"],
                "threshold_triggered": drive_result["threshold_triggered"],
            },
            "suggested_action": drive_result["suggested_action"],
            "cooldown_key": f"disk:{drive}:disk_space_low",
            "requires_verification": False,
            "trace_id": f"trace-disk-space-{drive.replace(':', '')}-{int(time.time())}",
        }

    def format_heartbeat_line(self, drive_result: Dict[str, Any]) -> str:
        """格式化单盘结果为 Heartbeat 展示行"""
        drive = drive_result["drive"]
        status = drive_result["status"]
        free_gb = drive_result["free_gb"]
        free_percent = drive_result["free_percent"]

        if status == "healthy":
            icon = "✅"
        elif status == "warn":
            icon = "⚠️"
        elif status == "critical":
            icon = "🔴"
        else:
            icon = "❓"

        return f"  {icon} {drive} {status} | Free: {free_gb}GB ({free_percent}%)"

    def format_heartbeat_section(self, check_result: Dict[str, Any]) -> str:
        """格式化完整 Heartbeat Capacity 板块"""
        lines = ["[DISK_SPACE] Capacity Check:"]
        for dr in check_result["drives"]:
            lines.append(self.format_heartbeat_line(dr))
        return "\n".join(lines)


def write_events(check_result: Dict[str, Any], events_path: Path) -> int:
    """将 warn/critical 事件追加写入 events.jsonl，返回写入数量"""
    detector = DiskSpaceDetector()
    written = 0
    with open(events_path, "a", encoding="utf-8") as f:
        for dr in check_result["drives"]:
            event = detector.generate_event(dr)
            if event:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                written += 1
    return written


def main():
    """独立运行：检查磁盘空间并输出结果"""
    detector = DiskSpaceDetector()

    print("磁盘空间检测器 v0 (Capacity)")
    print("=" * 60)

    result = detector.check()

    print(f"\n整体状态: {result['overall_status']}")
    print(f"检查时间: {result['timestamp']}")
    print()
    print(detector.format_heartbeat_section(result))

    # 输出详细信息
    for dr in result["drives"]:
        print(f"\n--- {dr['drive']} ---")
        print(f"  状态: {dr['status']}")
        print(f"  剩余: {dr['free_gb']}GB ({dr['free_percent']}%)")
        if dr["threshold_triggered"]:
            print(f"  触发阈值: {dr['threshold_triggered']}")
        if dr["suggested_action"]:
            print(f"  建议动作: {dr['suggested_action']}")
        if dr["error"]:
            print(f"  错误: {dr['error']}")

    # 写入事件
    events_path = Path(__file__).parent.parent / "data" / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    written = write_events(result, events_path)
    if written:
        print(f"\n已写入 {written} 条事件到 {events_path}")
    else:
        print(f"\n无需写入事件（所有盘 healthy）")


if __name__ == "__main__":
    main()
