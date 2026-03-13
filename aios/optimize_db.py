#!/usr/bin/env python3
"""Database optimization utilities for AIOS"""
import sqlite3
import time
from pathlib import Path

def vacuum_database(db_path: Path) -> dict:
    """
    Optimize SQLite database with VACUUM
    
    Returns:
        dict with before/after sizes and time taken
    """
    if not db_path.exists():
        return {'error': 'Database not found'}
    
    # Get size before
    size_before = db_path.stat().st_size / 1024 / 1024  # MB
    
    # Run VACUUM
    t0 = time.time()
    conn = sqlite3.connect(str(db_path))
    conn.execute('VACUUM')
    conn.close()
    elapsed = (time.time() - t0) * 1000  # ms
    
    # Get size after
    size_after = db_path.stat().st_size / 1024 / 1024  # MB
    saved = size_before - size_after
    
    return {
        'size_before_mb': round(size_before, 2),
        'size_after_mb': round(size_after, 2),
        'saved_mb': round(saved, 2),
        'time_ms': round(elapsed, 2),
        'reduction_pct': round((saved / size_before * 100) if size_before > 0 else 0, 1)
    }

def enable_wal_mode(db_path: Path) -> bool:
    """Enable WAL mode for better concurrency"""
    if not db_path.exists():
        return False
    
    conn = sqlite3.connect(str(db_path))
    conn.execute('PRAGMA journal_mode=WAL')
    result = conn.execute('PRAGMA journal_mode').fetchone()[0]
    conn.close()
    
    return result == 'wal'

def create_indexes(db_path: Path) -> list:
    """Create performance indexes if they don't exist"""
    if not db_path.exists():
        return []
    
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)',
        'CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)',
        'CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)',
    ]
    
    conn = sqlite3.connect(str(db_path))
    created = []
    for idx in indexes:
        try:
            conn.execute(idx)
            created.append(idx.split('idx_')[1].split(' ')[0])
        except Exception as e:
            pass
    conn.commit()
    conn.close()
    
    return created

def main():
    base = Path(__file__).parent
    db_path = base / 'storage' / 'aios.db'
    
    print("Database Optimization")
    print("=" * 60)
    
    # 1. VACUUM
    print("\n1. Running VACUUM...")
    result = vacuum_database(db_path)
    if 'error' in result:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Before: {result['size_before_mb']} MB")
        print(f"   After: {result['size_after_mb']} MB")
        print(f"   Saved: {result['saved_mb']} MB ({result['reduction_pct']}%)")
        print(f"   Time: {result['time_ms']}ms")
    
    # 2. Enable WAL
    print("\n2. Enabling WAL mode...")
    if enable_wal_mode(db_path):
        print("   WAL mode enabled")
    else:
        print("   Failed to enable WAL")
    
    # 3. Create indexes
    print("\n3. Creating indexes...")
    indexes = create_indexes(db_path)
    if indexes:
        for idx in indexes:
            print(f"   Created: {idx}")
    else:
        print("   All indexes already exist")
    
    print("\nOptimization complete!")

if __name__ == '__main__':
    main()
