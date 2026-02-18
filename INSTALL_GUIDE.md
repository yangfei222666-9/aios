# 语音唤醒系统 - 安装指南

## 🚀 快速安装

### 1. 克隆或下载项目
```bash
# 克隆项目
git clone <项目地址>
cd openclaw-workspace

# 或者直接下载并解压
```

### 2. 安装 Python 依赖
```bash
pip install vosk sounddevice numpy pyyaml edge-tts
```

### 3. 下载语音识别模型
```bash
# 创建模型目录
mkdir -p models

# 下载中文语音模型
# 从以下地址下载: https://alphacephei.com/vosk/models
# 选择: vosk-model-small-cn-0.22.zip (65MB)

# 解压到 models/vosk-cn/
# 最终目录结构:
# models/vosk-cn/
#   ├── am/
#   ├── conf/
#   ├── graph/
#   └── ivector/
```

### 4. 启动系统
```bash
python start_voice_system.py
```

## 📦 详细安装步骤

### Windows 系统

#### 1. 安装 Python
- 下载 Python 3.8+ 从 [python.org](https://www.python.org/)
- 安装时勾选 "Add Python to PATH"

#### 2. 安装依赖（命令提示符）
```cmd
pip install vosk sounddevice numpy pyyaml edge-tts
```

#### 3. 下载语音模型
1. 访问: https://alphacephei.com/vosk/models
2. 下载: `vosk-model-small-cn-0.22.zip`
3. 解压到: `C:\Users\你的用户名\.openclaw\workspace\models\vosk-cn\`

#### 4. 启动系统
```cmd
cd C:\Users\你的用户名\.openclaw\workspace
python start_voice_system.py
```

### macOS 系统

#### 1. 安装 Homebrew（如果未安装）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. 安装 Python 和依赖
```bash
brew install python
pip3 install vosk sounddevice numpy pyyaml edge-tts
```

#### 3. 下载语音模型
```bash
mkdir -p models
cd models
curl -L https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip -o model.zip
unzip model.zip
mv vosk-model-small-cn-0.22 vosk-cn
rm model.zip
```

#### 4. 启动系统
```bash
python3 start_voice_system.py
```

### Linux 系统

#### 1. 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip portaudio19-dev

# CentOS/RHEL
sudo yum install python3 python3-pip portaudio-devel
```

#### 2. 安装 Python 依赖
```bash
pip3 install vosk sounddevice numpy pyyaml edge-tts
```

#### 3. 下载语音模型
```bash
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip
mv vosk-model-small-cn-0.22 vosk-cn
rm vosk-model-small-cn-0.22.zip
```

#### 4. 启动系统
```bash
python3 start_voice_system.py
```

## 🔧 配置说明

### 默认配置
系统使用 `openclaw.yaml` 配置文件。如果不存在，启动时会自动创建。

### 自定义配置
编辑 `openclaw.yaml` 文件：

```yaml
voice_wake:
  enabled: true                    # 启用语音唤醒
  model_path: "models/vosk-cn"     # 模型路径
  wake_phrases: ["小九", "小酒", "你好小九"]  # 唤醒词
  command_timeout: 8.0             # 命令超时时间（秒）
  cooldown: 2.0                    # 唤醒冷却时间（秒）
  pause_while_tts: true            # TTS播放时暂停语音处理
  vad_end_silence_ms: 800          # 语音结束静音检测（毫秒）
  sample_rate: 16000               # 采样率
  blocksize: 4000                  # 音频块大小
  device: null                     # 音频设备（null为自动选择）

log_level: "INFO"                  # 日志级别
```

### 音频设备选择
要查看可用音频设备：
```bash
python start_voice_system.py --list-devices
```

然后在配置中指定设备ID：
```yaml
device: 1  # 使用设备ID 1
```

## 🧪 测试安装

### 运行系统测试
```bash
python start_voice_system.py --test
```

### 测试单个组件
```bash
# 测试 Unicode 清理
python tools/unicode_sanitizer.py

# 测试命令路由器
python tools/command_router.py

# 测试语音命令处理器
python tools/voice_command_handler_integrated.py
```

### 验证安装
```bash
python final_verification_simple.py
```

## 🐛 故障排除

### 常见问题

#### 1. "ModuleNotFoundError: No module named 'vosk'"
```bash
pip install vosk
```

#### 2. "无法打开音频设备"
```bash
# 列出可用设备
python start_voice_system.py --list-devices

# 修改配置中的 device 参数
```

#### 3. "模型文件未找到"
- 确认模型路径: `models/vosk-cn/`
- 确认目录包含: `am/`, `conf/`, `graph/`, `ivector/`
- 重新下载并解压模型

#### 4. 编码问题（Windows）
```bash
# 运行编码修复
python tools/encoding_fix.py
```

#### 5. 权限问题（Linux/macOS）
```bash
# 添加音频设备权限
sudo usermod -a -G audio $USER

# 重新登录生效
```

### 日志查看
```bash
# 查看系统日志
cat logs/voice_wake.log

# 查看命令历史
cat logs/command_results.log

# 实时查看日志
tail -f logs/voice_wake.log
```

## 📚 使用说明

### 基本使用
1. **启动系统**: `python start_voice_system.py`
2. **唤醒系统**: 说"小九"、"小酒"或"你好小九"
3. **听回应**: 系统会回应"我在，请说命令"
4. **说命令**: 如"检查系统状态"、"添加笔记"、"现在几点"
5. **查看结果**: 命令结果会记录在日志中

### 可用命令
- **状态检查**: "检查系统状态"、"查看运行状态"
- **笔记管理**: "添加笔记：内容"、"记录备忘"
- **时间查询**: "现在几点"、"当前时间"
- **搜索功能**: "搜索关键词"、"查一下信息"
- **系统功能**: "测试语音"、"有什么功能"、"帮助"

### 停止系统
按 `Ctrl+C` 停止系统。

## 🔄 更新系统

### 更新代码
```bash
# 如果使用 git
git pull origin main

# 如果手动下载
# 下载最新版本并替换文件
```

### 更新依赖
```bash
pip install --upgrade vosk sounddevice numpy pyyaml edge-tts
```

### 更新模型
```bash
# 备份旧模型
mv models/vosk-cn models/vosk-cn-backup

# 下载新模型
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip
mv vosk-model-small-cn-0.22 vosk-cn
rm vosk-model-small-cn-0.22.zip
```

## 📞 支持与帮助

### 文档
- `SYSTEM_SUMMARY.md` - 系统完整文档
- `INSTALL_GUIDE.md` - 安装指南（本文档）
- 代码中的注释和文档字符串

### 问题报告
1. 查看日志文件: `logs/voice_wake.log`
2. 描述问题现象
3. 提供系统信息（操作系统、Python版本等）
4. 提供复现步骤

### 功能请求
1. 描述使用场景
2. 说明具体需求
3. 讨论实现方案

## 🎉 完成安装

安装完成后，系统应该：
- ✅ 所有依赖已安装
- ✅ 语音模型已下载
- ✅ 配置文件已创建
- ✅ 目录结构完整
- ✅ 系统可以正常启动

现在可以开始使用语音唤醒系统了！

```bash
# 启动系统
python start_voice_system.py

# 说"小九"开始体验！
```

---

*最后更新：2026-02-17*  
*版本：1.0.0*