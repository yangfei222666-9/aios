"""每日电脑清理脚本 - 安全清理临时文件和缓存"""
import os, shutil, json, time
from pathlib import Path
from datetime import datetime

def sizeof_fmt(num):
    for unit in ['B','KB','MB','GB']:
        if abs(num) < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}TB"

def safe_remove(path, stats):
    """安全删除文件/文件夹，统计释放空间"""
    try:
        p = Path(path)
        if not p.exists():
            return
        if p.is_file():
            size = p.stat().st_size
            p.unlink()
            stats['freed'] += size
            stats['files'] += 1
        elif p.is_dir():
            size = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
            shutil.rmtree(p, ignore_errors=True)
            stats['freed'] += size
            stats['files'] += 1
    except (PermissionError, OSError):
        stats['skipped'] += 1

def clean_dir(dirpath, stats, max_age_days=1, extensions=None):
    """清理目录中的旧文件"""
    d = Path(dirpath)
    if not d.exists():
        return
    cutoff = time.time() - max_age_days * 86400
    try:
        items = list(d.iterdir())
    except (PermissionError, OSError):
        stats['skipped'] += 1
        return
    for item in items:
        try:
            if item.stat().st_mtime < cutoff:
                if extensions and item.is_file() and item.suffix.lower() not in extensions:
                    continue
                safe_remove(item, stats)
        except (PermissionError, OSError):
            stats['skipped'] += 1

def main():
    stats = {'freed': 0, 'files': 0, 'skipped': 0}
    user = os.environ.get('USERPROFILE', r'C:\Users\A')
    
    # 1. Windows Temp
    clean_dir(os.environ.get('TEMP', rf'{user}\AppData\Local\Temp'), stats, max_age_days=1)
    
    # 2. Windows Prefetch (超过7天的)
    clean_dir(r'C:\Windows\Prefetch', stats, max_age_days=7)
    
    # 3. 回收站 - 用 PowerShell 清空
    try:
        os.system('PowerShell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue" 2>nul')
    except:
        pass
    
    # 4. 浏览器缓存 (Chrome)
    chrome_cache = rf'{user}\AppData\Local\Google\Chrome\User Data\Default\Cache\Cache_Data'
    clean_dir(chrome_cache, stats, max_age_days=3)
    
    # 5. Windows Update 缓存 (超过7天)
    clean_dir(r'C:\Windows\SoftwareDistribution\Download', stats, max_age_days=7)
    
    # 6. 缩略图缓存
    thumb_cache = rf'{user}\AppData\Local\Microsoft\Windows\Explorer'
    if Path(thumb_cache).exists():
        for f in Path(thumb_cache).glob('thumbcache_*.db'):
            try:
                if f.stat().st_mtime < time.time() - 7 * 86400:
                    safe_remove(f, stats)
            except:
                pass
    
    # 7. pip 缓存 (超过7天)
    pip_cache = rf'{user}\AppData\Local\pip\cache'
    clean_dir(pip_cache, stats, max_age_days=7)
    
    # 8. npm 缓存 (超过7天)
    npm_cache = rf'{user}\AppData\Local\npm-cache'
    clean_dir(npm_cache, stats, max_age_days=7)
    
    # 9. Windows 日志 (超过7天)
    clean_dir(r'C:\Windows\Logs', stats, max_age_days=7, extensions={'.log', '.etl', '.tmp'})
    
    # 10. 最近文件快捷方式 (超过30天)
    recent = rf'{user}\AppData\Roaming\Microsoft\Windows\Recent'
    clean_dir(recent, stats, max_age_days=30, extensions={'.lnk'})

    # 输出结果
    result = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'freed': sizeof_fmt(stats['freed']),
        'freed_bytes': stats['freed'],
        'files_removed': stats['files'],
        'skipped': stats['skipped']
    }
    print(json.dumps(result, ensure_ascii=False))
    return result

if __name__ == '__main__':
    main()
