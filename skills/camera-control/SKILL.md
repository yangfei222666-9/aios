# Camera Control Skill

摄像头控制技能 - 拍照、监控、分析画面

## 触发词

- `camera snap` / `拍照` / `拍个照` - 拍摄单张照片
- `camera watch` / `监控模式` / `开始监控` - 启动监控模式（连续拍照）
- `camera analyze` / `分析画面` / `看看现在什么情况` - 分析当前画面内容

## 功能说明

### 1. camera snap - 拍照
拍摄单张照片并保存到本地。

**用法：**
```bash
python camera.py snap [--device 0] [--output ./snapshots]
```

**参数：**
- `--device` - 摄像头设备ID（默认0，即默认摄像头）
- `--output` - 保存路径（默认 `./snapshots`）

**输出：**
- 照片文件：`snapshot_YYYYMMDD_HHMMSS.jpg`
- 返回文件路径

### 2. camera watch - 监控模式
启动监控模式，每隔指定时间拍摄一张照片。

**用法：**
```bash
python camera.py watch [--device 0] [--interval 5] [--duration 60] [--output ./snapshots]
```

**参数：**
- `--device` - 摄像头设备ID（默认0）
- `--interval` - 拍照间隔（秒，默认5秒）
- `--duration` - 监控时长（秒，默认60秒，0表示无限）
- `--output` - 保存路径（默认 `./snapshots`）

**输出：**
- 多张照片文件：`watch_YYYYMMDD_HHMMSS_001.jpg`, `watch_YYYYMMDD_HHMMSS_002.jpg`, ...
- 监控统计信息

### 3. camera analyze - 分析画面
拍摄一张照片并使用 AI 分析画面内容。

**用法：**
```bash
python camera.py analyze [--device 0] [--prompt "描述这个画面"]
```

**参数：**
- `--device` - 摄像头设备ID（默认0）
- `--prompt` - 分析提示词（默认："描述这个画面中的内容"）

**输出：**
- 照片文件：`analyze_YYYYMMDD_HHMMSS.jpg`
- AI 分析结果（文本描述）

## 依赖

需要安装以下 Python 包：

```bash
pip install opencv-python pillow
```

## 配置

可以在 `config.json` 中配置默认参数：

```json
{
  "default_device": 0,
  "default_output": "./snapshots",
  "default_interval": 5,
  "default_duration": 60,
  "image_quality": 95,
  "image_format": "jpg"
}
```

## 示例

**拍照：**
```bash
python camera.py snap
# 输出: 已保存照片: ./snapshots/snapshot_20260305_063700.jpg
```

**监控模式（每10秒拍一张，持续5分钟）：**
```bash
python camera.py watch --interval 10 --duration 300
# 输出: 监控完成，共拍摄 30 张照片
```

**分析画面：**
```bash
python camera.py analyze --prompt "这个房间里有什么？"
# 输出: 
# 已保存照片: ./snapshots/analyze_20260305_063800.jpg
# AI 分析结果: 这是一个办公室，有一张桌子、一台电脑显示器、一把椅子...
```

## 注意事项

1. **权限** - 首次使用时可能需要授予摄像头访问权限
2. **设备ID** - 如果有多个摄像头，使用 `--device 1` 或 `--device 2` 切换
3. **存储空间** - 监控模式会生成大量照片，注意磁盘空间
4. **隐私** - 使用摄像头时请注意隐私保护

## 故障排查

**摄像头无法打开：**
- 检查摄像头是否被其他程序占用
- 尝试更换设备ID（`--device 1`）
- 检查摄像头驱动是否正常

**照片保存失败：**
- 检查输出目录是否存在写入权限
- 检查磁盘空间是否充足

**AI 分析失败：**
- 确保已配置 OpenClaw 的 image 工具
- 检查网络连接（如果使用云端 AI）

## 版本历史

- v1.0 (2026-03-05) - 初始版本
  - 支持拍照、监控、分析三大功能
  - 支持多摄像头切换
  - 支持自定义参数配置
