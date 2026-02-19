import subprocess, sys, re, ssl, urllib.request, json, base64
sys.stdout.reconfigure(encoding='utf-8')

# 用 netstat 找 LeagueClientUx 的监听端口
r = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=10)
lines = r.stdout.splitlines()

# 获取 LeagueClientUx PID
r2 = subprocess.run(
    ['powershell', '-Command', '(Get-Process LeagueClientUx).Id'],
    capture_output=True, text=True, timeout=5, creationflags=0x08000000
)
pid = r2.stdout.strip()
print(f'LeagueClientUx PID: {pid}')

# 找这个 PID 监听的端口
listening = []
for line in lines:
    if 'LISTENING' in line and pid in line:
        parts = line.split()
        addr = parts[1]
        port = addr.split(':')[-1]
        listening.append(int(port))

print(f'监听端口: {listening}')

# 尝试用 Riot Client 的 token 连接（有时共享）
riot_token = '1t__imTu_1kjQjnB6CmkRw'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for port in listening:
    auth = base64.b64encode(f'riot:{riot_token}'.encode()).decode()
    try:
        req = urllib.request.Request(f'https://127.0.0.1:{port}/lol-summoner/v1/current-summoner')
        req.add_header('Authorization', f'Basic {auth}')
        req.add_header('Accept', 'application/json')
        resp = urllib.request.urlopen(req, context=ctx, timeout=3)
        data = json.loads(resp.read().decode())
        print(f'\nport {port} 连接成功!')
        print(f'召唤师: {data.get("displayName","?")}')
        
        # 读游戏数据
        req2 = urllib.request.Request(f'https://127.0.0.1:{port}/lol-gameflow/v1/session')
        req2.add_header('Authorization', f'Basic {auth}')
        req2.add_header('Accept', 'application/json')
        resp2 = urllib.request.urlopen(req2, context=ctx, timeout=3)
        flow = json.loads(resp2.read().decode())
        phase = flow.get('phase', '?')
        mode = flow.get('gameData', {}).get('queue', {}).get('gameMode', '?')
        print(f'阶段: {phase} | 模式: {mode}')
        
        if phase == 'InProgress':
            gd = flow.get('gameData', {})
            sid = data.get('summonerId')
            all_p = gd.get('teamOne', []) + gd.get('teamTwo', [])
            for p in all_p:
                if p.get('summonerId') == sid:
                    cid = p.get('championId', 0)
                    print(f'我的英雄ID: {cid}')
                    with open(r'C:\Users\A\Desktop\ARAM-Helper\aram_data.json', 'r', encoding='utf-8') as f:
                        db = json.load(f)
                    hero = db.get(str(cid), {})
                    if hero:
                        print(f'\n=== {hero.get("name","?")} ===')
                        print(f'出装: {" > ".join(hero.get("items",[]))}')
                        print(f'符文: {hero.get("runes","")}')
                        print(f'技能: {hero.get("spells","")}')
                        print(f'贴士: {hero.get("tips","")}')
                    break
        break
    except Exception as e:
        print(f'port {port}: {e}')
