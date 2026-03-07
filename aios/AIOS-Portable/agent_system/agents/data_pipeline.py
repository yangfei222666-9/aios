"""Data Pipeline Agent - 数据流管理"""
import json, shutil
from pathlib import Path
from datetime import datetime, timedelta

class DataPipeline:
    def __init__(self):
        self.data_dir = Path("data")
        self.archive_dir = Path("data/archive")
        
    def run(self):
        print("=" * 80)
        print("Data Pipeline - 数据流管理")
        print("=" * 80)
        
        # 1. 统计数据
        stats = self._collect_stats()
        print(f"\n📊 数据统计:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总大小: {stats['total_size_mb']:.1f} MB")
        print(f"  jsonl 文件: {stats['jsonl_count']}")
        
        # 2. 清理过期数据（30天前）
        cleaned = self._clean_old_data(days=30)
        print(f"\n🗑️  清理过期数据: {cleaned} 个文件")
        
        # 3. 归档大文件（>10MB）
        archived = self._archive_large_files(max_mb=10)
        print(f"📦 归档大文件: {archived} 个文件")
        
        # 4. 生成统计报告
        self._generate_report(stats)
        print(f"\n✓ 数据管道运行完成")
        print(f"\n{'=' * 80}")
    
    def _collect_stats(self):
        total_files = 0
        total_size = 0
        jsonl_count = 0
        
        if self.data_dir.exists():
            for f in self.data_dir.rglob("*"):
                if f.is_file():
                    total_files += 1
                    total_size += f.stat().st_size
                    if f.suffix == ".jsonl":
                        jsonl_count += 1
        
        return {
            "total_files": total_files,
            "total_size_mb": total_size / (1024 * 1024),
            "jsonl_count": jsonl_count
        }
    
    def _clean_old_data(self, days=30):
        cleaned = 0
        cutoff = datetime.now() - timedelta(days=days)
        
        if self.data_dir.exists():
            for f in self.data_dir.rglob("*.jsonl"):
                if f.stat().st_mtime < cutoff.timestamp():
                    # 只清理 temp 目录
                    if "temp" in str(f):
                        f.unlink()
                        cleaned += 1
        
        return cleaned
    
    def _archive_large_files(self, max_mb=10):
        archived = 0
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        if self.data_dir.exists():
            for f in self.data_dir.rglob("*.jsonl"):
                if f.stat().st_size > max_mb * 1024 * 1024:
                    dest = self.archive_dir / f.name
                    shutil.move(str(f), str(dest))
                    archived += 1
        
        return archived
    
    def _generate_report(self, stats):
        report = {"timestamp": datetime.now().isoformat(), **stats}
        report_file = Path("data/pipeline/pipeline_report.jsonl")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run()
