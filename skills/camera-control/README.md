# Camera Control Skill

摄像头控制技能 - 拍照、监控、分析画面

## 安装依赖

```bash
pip install opencv-python pillow
```

## 快速开始

### 拍照
```bash
python camera.py snap
```

### 监控模式（每10秒拍一张，持续5分钟）
```bash
python camera.py watch --interval 10 --duration 300
```

### 分析画面
```bash
python camera.py analyze --prompt "这个房间里有什么？"
```

## 详细文档

请查看 [SKILL.md](SKILL.md)
