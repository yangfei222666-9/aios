#!/usr/bin/env python3
"""AIOS 存储优化工具"""
import sys
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

def compress_old_archives(days_threshold=30):
    """压缩旧归档文件"""
    base = Path(__file__).parent
    archive_dir = base / 'archive'
    
    if not archive_dir.exists():
        return []
    
    compressed = []
    cutoff = datetime.now() - timedelta(days=days_threshold)
    
    for jsonl_file in archive_dir.glob('*.jsonl'):
        # 检查文件修改时间
        mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
        
        if mtime < cutoff:
            gz_file = jsonl_file.with_suffix('.jsonl.gz')
            
            # 压缩
            with open(jsonl_file, 'rb') as f_in:
                with gzip.open(gz_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 验证压缩成功
            if gz_file.exists():
                original_size = jsonl_file.stat().st_size
                compressed_size = gz_file.stat().st_size
                ratio = (1 - compressed_size / original_size) * 100
                
                compressed.append({
                    'file': jsonl_file.name,
                    'original_mb': round(original_size / 1024 / 1024, 2),
                    'compressed_mb': round(compressed_size / 1024 / 1024, 2),
                    'saved_percent': round(ratio, 1)
                })
                
                # 删除原文件
                jsonl_file.unlink()
    
    return compressed

def vacuum_database():
    """优化数据库"""
    import sqlite3
    
    db_path = Path(__file__).parent / 'aios.db'
    if not db_path.exists():
        return None
    
    original_size = db_path.stat().st_size / 1024 / 1024
    
    conn = sqlite3.connect(db_path)
    conn.execute('VACUUM')
    conn.close()
    
    new_size = db_path.stat().st_size / 1024 / 1024
    
    return {
        'original_mb': round(original_size, 2),
        'new_mb': round(new_size, 2),
        'saved_mb': round(original_size - new_size, 2)
    }

def cleanup_temp_files():
    """清理临时文件"""
    base = Path(__file__).parent
    patterns = ['**/*.tmp', '**/*.bak', '**/__pycache__']
    
    removed = []
    for pattern in patterns:
        for f in base.glob(pattern):
            if f.is_file():
                size_mb = f.stat().st_size / 1024 / 1024
                f.unlink()
                removed.append({'file': str(f.relative_to(base)), 'size_mb': round(size_mb, 2)})
            elif f.is_dir() and '__pycache__' in str(f):
                shutil.rmtree(f)
                removed.append({'file': str(f.relative_to(base)), 'type': 'dir'})
    
    return removed

def main():
    print("AIOS Storage Optimization")
    print("=" * 60)
    
    # 1. 压缩旧归档
    print("\n1. Compressing old archives (>30 days)...")
    compressed = compress_old_archives(30)
    if compressed:
        for item in compressed:
            print(f"   [OK] {item['file']}: {item['original_mb']}MB -> {item['compressed_mb']}MB (saved {item['saved_percent']}%)")
    else:
        print("   No old archives to compress")
    
    # 2. 优化数据库
    print("\n2. Vacuuming database...")
    db_result = vacuum_database()
    if db_result:
        print(f"   [OK] Database: {db_result['original_mb']}MB -> {db_result['new_mb']}MB (saved {db_result['saved_mb']}MB)")
    else:
        print("   No database found")
    
    # 3. 清理临时文件
    print("\n3. Cleaning temp files...")
    removed = cleanup_temp_files()
    if removed:
        for item in removed[:5]:
            print(f"   [OK] Removed: {item['file']}")
        if len(removed) > 5:
            print(f"   ... and {len(removed) - 5} more")
    else:
        print("   No temp files to clean")
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'compressed_archives': compressed,
        'database_vacuum': db_result,
        'temp_files_removed': len(removed)
    }
    
    report_path = Path(__file__).parent / 'optimization_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n[OK] Optimization complete! Report: {report_path}")

if __name__ == '__main__':
    main()
