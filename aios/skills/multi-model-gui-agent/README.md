# Multi-Model GUI Agent

多模型协同的 GUI 自动化代理，支持抖音评论自动化和智能客服场景。

## 快速开始

### 1. 安装依赖

```bash
pip install pyautogui pillow requests
```

### 2. 配置 API Keys

编辑 `config.json`，填入豆包 API Keys：

```json
{
  "teacher_key": "your-2.0-lite-key",
  "executor_key": "your-1.6-flash-key",
  "fallback_key": "your-1.6-lite-key"
}
```

### 3. 准备链接列表

编辑 `urls.txt`，添加要处理的链接：

```
https://www.douyin.com/video/123456
https://www.douyin.com/video/789012
```

### 4. 运行

```bash
# 抖音评论模式
python agent.py --config config.json --urls urls.txt --mode douyin

# 智能客服模式
python agent.py --config config.json --urls urls.txt --mode customer-service
```

## 核心特性

- **多模型协同** - 2.0 Lite 理解 + 1.6 flash 执行 + 1.6 lite 容灾
- **智能缓存** - 坐标缓存，命中率 > 80%
- **自动重试** - 失败自动重试，最多 3 次
- **容灾降级** - 超时自动降级，不会卡死
- **详细日志** - 所有操作都有日志记录
- **执行报告** - 自动生成统计报告

## 架构

```
[读链接] → [截图] → [2.0 Lite分析坐标] → [1.6 flash点击输入] → [下一链接]
   ↓失败/超时
   [1.6 lite降级处理]
```

## 文档

- [SKILL.md](SKILL.md) - 完整技能文档
- [TRAE_INSTRUCTIONS.md](TRAE_INSTRUCTIONS.md) - 给 Trae 的开发指令
- [test_screenshot.py](test_screenshot.py) - 环境测试脚本

## 测试

```bash
# 测试环境
python test_screenshot.py

# 单元测试
python test_agent.py
```

## 性能指标

- 单次操作耗时 < 5s
- 成功率 > 80%
- 缓存命中率 > 80%
- 失败率 < 5%

## 扩展场景

- 抖音评论自动化
- 智能客服
- 电商自动下单
- 社交媒体管理
- 数据采集

## 维护者

- 小九 + 珊瑚海
- 版本：v1.0
- 创建时间：2026-03-13

## License

MIT
