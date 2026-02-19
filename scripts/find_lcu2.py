import subprocess, sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

# 用 wmic 替代 Get-CimInstance（有时权限不同）
try:
    r = subprocess.run(
        ['wmic', 'process', 'where', "name='LeagueClientUx.exe'", 'get', 'CommandLine', '/value'],
        capture_output=True, text=True, timeout=10,
        creationflags=0x08000000
    )
    output = r.stdout.strip()
    print(f'wmic output: {repr(output[:300])}')
    
    if output:
        pm = re.search(r'--app-port=(\d+)', output)
        tm = re.search(r'--remoting-auth-token=([^\s"]+)', output)
        if pm and tm:
            print(f'port={pm.group(1)} token={tm.group(1)[:10]}...')
        else:
            print('找到进程但无法解析端口/令牌')
    else:
        print('wmic 无输出')
except Exception as e:
    print(f'wmic 错误: {e}')

# 备选：扫描 LeagueClient 目录下的 lockfile（用二进制模式）
lf = r'E:\WeGameApps\英雄联盟\LeagueClient\lockfile'
if os.path.exists(lf):
    size = os.path.getsize(lf)
    print(f'\nlockfile 大小: {size} bytes')
    with open(lf, 'rb') as f:
        raw = f.read()
    print(f'lockfile 原始: {raw}')
    if raw:
        text = raw.decode('utf-8', errors='replace')
        print(f'lockfile 文本: {text}')
