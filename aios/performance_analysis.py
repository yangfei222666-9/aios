#!/usr/bin/env python3
"""AIOS 性能分析工具"""
import sys
import time
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

def analyze_event_loading():
    """分析事件加载性能"""
    from core import engine, event_store
    
    results = {}
    
    # 测试 engine.load_events
    t0 = time.time()
    events = engine.load_events(30)
    engine_time = (time.time() - t0) * 1000
    results['engine_load_events'] = {
        'count': len(events),
        'time_ms': round(engine_time, 2)
    }
    
    # 测试 EventStore
    t0 = time.time()
    store = event_store.EventStore()
    events = store.load_events()
    store_time = (time.time() - t0) * 1000
    results['event_store_load'] = {
        'count': len(events),
        'time_ms': round(store_time, 2)
    }
    
    return results

def analyze_memory_usage():
    """分析内存使用"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    return {
        'rss_mb': round(mem_info.rss / 1024 / 1024, 2),
        'vms_mb': round(mem_info.vms / 1024 / 1024, 2)
    }

def analyze_file_sizes():
    """分析文件大小"""
    base = Path(__file__).parent
    
    sizes = {}
    for pattern in ['**/*.jsonl', '**/*.json', '**/*.db']:
        for f in base.glob(pattern):
            if f.is_file():
                size_mb = f.stat().st_size / 1024 / 1024
                if size_mb > 1:  # 只显示 >1MB 的文件
                    sizes[str(f.relative_to(base))] = round(size_mb, 2)
    
    return dict(sorted(sizes.items(), key=lambda x: x[1], reverse=True)[:20])

def analyze_bottlenecks():
    """识别性能瓶颈"""
    bottlenecks = []
    
    # 检查大文件
    file_sizes = analyze_file_sizes()
    large_files = {k: v for k, v in file_sizes.items() if v > 10}
    if large_files:
        bottlenecks.append({
            'type': 'large_files',
            'severity': 'high',
            'files': large_files,
            'recommendation': '考虑分片存储或归档压缩'
        })
    
    # 检查事件加载性能
    event_perf = analyze_event_loading()
    if event_perf['engine_load_events']['time_ms'] > 100:
        bottlenecks.append({
            'type': 'slow_event_loading',
            'severity': 'medium',
            'time_ms': event_perf['engine_load_events']['time_ms'],
            'recommendation': '优化 JSONL 解析或添加索引'
        })
    
    return bottlenecks

def main():
    print("AIOS Performance Analysis")
    print("=" * 60)
    
    # 1. Event loading performance
    print("\nEvent Loading Performance:")
    event_perf = analyze_event_loading()
    for key, val in event_perf.items():
        print(f"  {key}: {val['count']} events in {val['time_ms']}ms")
    
    # 2. Memory usage
    print("\nMemory Usage:")
    mem = analyze_memory_usage()
    print(f"  RSS: {mem['rss_mb']} MB")
    print(f"  VMS: {mem['vms_mb']} MB")
    
    # 3. Large files
    print("\nLarge Files (>1MB):")
    files = analyze_file_sizes()
    for path, size in list(files.items())[:10]:
        print(f"  {path}: {size} MB")
    
    # 4. Bottleneck analysis
    print("\nPerformance Bottlenecks:")
    bottlenecks = analyze_bottlenecks()
    if not bottlenecks:
        print("  No obvious bottlenecks found")
    else:
        for i, b in enumerate(bottlenecks, 1):
            print(f"\n  {i}. {b['type']} (severity: {b['severity']})")
            print(f"     Recommendation: {b['recommendation']}")
            if 'files' in b:
                for f, s in list(b['files'].items())[:3]:
                    print(f"       - {f}: {s} MB")
    
    # Save report
    report = {
        'timestamp': time.time(),
        'event_loading': event_perf,
        'memory': mem,
        'large_files': files,
        'bottlenecks': bottlenecks
    }
    
    report_path = Path(__file__).parent / 'performance_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFull report saved: {report_path}")

if __name__ == '__main__':
    main()
