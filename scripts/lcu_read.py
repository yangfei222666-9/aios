import subprocess, re, sys, ssl, urllib.request, json, base64
sys.stdout.reconfigure(encoding='utf-8')

# 方法1: PowerShell Get-CimInstance
port = token = None
try:
    r = subprocess.run(
        ['powershell', '-Command',
         "(Get-CimInstance Win32_Process -Filter \"name='LeagueClientUx.exe'\").CommandLine"],
        capture_output=True, text=True, timeout=10,
        creationflags=0x08000000
    )
    output = r.stdout
    if output:
        pm = re.search(r'--app-port=(\d+)', output)
        tm = re.search(r'--remoting-auth-token=([^\s"]+)', output)
        if pm and tm:
            port, token = pm.group(1), tm.group(1)
            print(f'方法1成功: port={port}')
except Exception as e:
    print(f'方法1失败: {e}')

# 方法2: lockfile
if not port:
    import os
    lf = r'E:\WeGameApps\英雄联盟\LeagueClient\lockfile'
    if os.path.exists(lf):
        try:
            # 用共享读取
            import ctypes
            from ctypes import wintypes
            GENERIC_READ = 0x80000000
            FILE_SHARE_READ = 1
            FILE_SHARE_WRITE = 2
            OPEN_EXISTING = 3
            handle = ctypes.windll.kernel32.CreateFileW(
                lf, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
                None, OPEN_EXISTING, 0, None)
            if handle != -1:
                buf = ctypes.create_string_buffer(1024)
                read = wintypes.DWORD()
                ctypes.windll.kernel32.ReadFile(handle, buf, 1024, ctypes.byref(read), None)
                ctypes.windll.kernel32.CloseHandle(handle)
                content = buf.value.decode('utf-8', errors='replace').strip()
                print(f'lockfile内容: {content}')
                parts = content.split(':')
                if len(parts) >= 4:
                    port, token = parts[2], parts[3]
                    print(f'方法2成功: port={port}')
        except Exception as e:
            print(f'方法2失败: {e}')

if not port:
    print('无法连接LCU客户端')
    sys.exit(1)

# LCU API
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
auth_str = base64.b64encode(f'riot:{token}'.encode()).decode()

def lcu(path):
    req = urllib.request.Request(f'https://127.0.0.1:{port}{path}')
    req.add_header('Authorization', f'Basic {auth_str}')
    req.add_header('Accept', 'application/json')
    resp = urllib.request.urlopen(req, context=ctx, timeout=5)
    return json.loads(resp.read().decode())

# 游戏状态
try:
    flow = lcu('/lol-gameflow/v1/session')
    phase = flow.get('phase', '?')
    gd = flow.get('gameData', {})
    mode = gd.get('queue', {}).get('gameMode', '?')
    print(f'\n阶段: {phase} | 模式: {mode}')
    
    if phase == 'InProgress':
        # 游戏中，从 gameData 读英雄
        summoner = lcu('/lol-summoner/v1/current-summoner')
        sid = summoner.get('summonerId')
        sname = summoner.get('displayName', '?')
        print(f'召唤师: {sname}')
        
        all_players = gd.get('teamOne', []) + gd.get('teamTwo', [])
        my_champ = 0
        for p in all_players:
            if p.get('summonerId') == sid:
                my_champ = p.get('championId', 0)
                break
        
        if my_champ:
            with open(r'C:\Users\A\Desktop\ARAM-Helper\aram_data.json', 'r', encoding='utf-8') as f:
                db = json.load(f)
            hero = db.get(str(my_champ), {})
            if hero:
                print(f'\n=== {hero.get("name","?")} ===')
                print(f'出装: {" > ".join(hero.get("items",[]))}')
                print(f'符文: {hero.get("runes","")}')
                print(f'技能: {hero.get("spells","")}')
                print(f'贴士: {hero.get("tips","")}')
                if hero.get('balance'):
                    print(f'ARAM调整: {hero["balance"]}')
            else:
                print(f'英雄ID {my_champ} 无数据')
        else:
            print('未找到自己的英雄')
    
    elif phase == 'ChampSelect':
        session = lcu('/lol-champ-select/v1/session')
        my_team = session.get('myTeam', [])
        local_cell = session.get('localPlayerCellId', -1)
        my_champ = 0
        for p in my_team:
            if p.get('cellId') == local_cell:
                my_champ = p.get('championId', 0)
        if my_champ:
            with open(r'C:\Users\A\Desktop\ARAM-Helper\aram_data.json', 'r', encoding='utf-8') as f:
                db = json.load(f)
            hero = db.get(str(my_champ), {})
            if hero:
                print(f'\n=== {hero.get("name","?")} ===')
                print(f'出装: {" > ".join(hero.get("items",[]))}')
            else:
                print(f'英雄ID {my_champ} 无数据')
    else:
        print(f'当前不在选人/游戏中 (phase={phase})')
        
except Exception as e:
    print(f'错误: {e}')
