# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## 应用路径
- QQ音乐 → E:\QQMusic\QQMusic.exe

## Memory Server（常驻进程）
- **作用：** 保持 embedding 模型热加载，消除冷启动 9s 延迟
- **启动：** `cd C:\Users\A\.openclaw\workspace\aios\agent_system; & "C:\Program Files\Python312\python.exe" memory_server.py`
- **端口：** 7788
- **接口：** GET /status | POST /query | POST /ingest | POST /feedback
- **注意：** 每次重启电脑后需要手动启动，或加入开机自启


- **版本：** v3.4（默认使用）
- **路径：** C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4\
- **启动命令：** `cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4; & "C:\Program Files\Python312\python.exe" server.py`
- **访问地址：** http://127.0.0.1:8888
- **端口：** 8888

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
