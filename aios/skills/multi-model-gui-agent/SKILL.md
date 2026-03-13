# Multi-Model GUI Agent - 多模型视觉代理

## 概述

基于豆包多模型协同的 GUI 自动化代理：
- **2.0 Lite（老师）** - 视觉理解，返回坐标
- **1.6 flash（执行）** - 快速操作，生成内容
- **1.6 lite（容灾）** - 超时降级，兜底处理

## 适用场景

1. **抖音评论自动化** - 批量访问链接，自动发评论
2. **智能客服** - 识别截图中的错误码、订单号、异常状态
3. **任何需要"看懂界面 → 执行操作"的场景**

## 核心架构

```
[读链接] → [截图] → [2.0 Lite分析坐标] → [1.6 flash点击输入] → [下一链接]
   ↓失败/超时
   [1.6 lite降级处理]
```

## 依赖

```bash
pip install pyautogui pillow requests
```

## 配置

在 `config.json` 中配置豆包 API Keys：

```json
{
  "teacher_key": "your-2.0-lite-key",
  "executor_key": "your-1.6-flash-key",
  "fallback_key": "your-1.6-lite-key",
  "timeout": {
    "teacher": 10,
    "executor": 3,
    "fallback": 5
  },
  "retry": {
    "max_attempts": 3,
    "backoff": 2
  }
}
```

## 使用方式

### 1. 准备链接列表

创建 `urls.txt`：
```
https://www.douyin.com/video/123456
https://www.douyin.com/video/789012
https://www.douyin.com/video/345678
```

### 2. 运行代理

```bash
python agent.py --config config.json --urls urls.txt --mode douyin
```

### 3. 切换场景

```bash
# 智能客服模式
python agent.py --config config.json --urls urls.txt --mode customer-service

# 自定义模式
python agent.py --config config.json --urls urls.txt --mode custom --prompt "你的自定义prompt"
```

## 容灾机制

1. **超时降级** - 2.0 Lite 超时 → 自动切换 1.6 lite
2. **坐标缓存** - 相同页面结构复用坐标
3. **失败重试** - 最多重试 3 次，指数退避
4. **日志记录** - 所有失败都记录到 `execution.log`

## 给 Trae 的完整指令

### Phase 1: 环境准备

```
1. 安装依赖：pip install pyautogui pillow requests
2. 克隆 UI-TARS-desktop：
   git clone https://github.com/bytedance/UI-TARS-desktop.git
   cd UI-TARS-desktop
   npm install && npm run build && npm run start
3. 在 UI-TARS 设置中填入豆包 API Key
4. 验证截图功能：运行 test_screenshot.py
```

### Phase 2: 核心代码实现

```
实现多模型 GUI 代理，要求：

1. 架构：
   - 2.0 Lite 视觉理解返回坐标
   - 1.6 flash 执行点击和内容生成
   - 1.6 lite 容灾降级

2. 流程：
   - 读取 urls.txt
   - 对每个链接：截图 → 老师分析 → 执行动作
   - 记录执行日志

3. 容灾：
   - 超时自动降级
   - 失败重试（最多3次）
   - 坐标缓存

4. 技术栈：
   - pyautogui 操作界面
   - requests 调豆包 API
   - PIL 截图

给出完整可运行代码，包括：
- agent.py（主逻辑）
- config.json（配置模板）
- test_screenshot.py（测试脚本）
- README.md（使用说明）
```

### Phase 3: 测试验证

```
1. 单元测试：
   - 测试截图功能
   - 测试 API 调用
   - 测试坐标解析

2. 集成测试：
   - 准备 5 条测试链接
   - 运行完整流程
   - 验证评论是否发布成功

3. 容灾测试：
   - 模拟 2.0 Lite 超时
   - 验证降级到 1.6 lite
   - 验证重试机制
```

### Phase 4: 生产部署

```
1. 性能优化：
   - 坐标缓存命中率 > 80%
   - 单次操作耗时 < 5s
   - 失败率 < 5%

2. 监控告警：
   - 记录每次执行的耗时、成功率
   - 失败超过 3 次连续告警
   - 每日生成执行报告

3. 文档完善：
   - 故障排查手册
   - 常见问题 FAQ
   - 扩展开发指南
```

## 扩展场景

### 智能客服

只需修改 `teacher_analyze` 的 prompt：

```python
def teacher_analyze_customer_service(self, img_path):
    prompt = """
    识别截图中的：
    1. 错误码（红色文字）
    2. 订单号（格式：ORD-XXXXXX）
    3. 异常状态（黄色/红色标签）
    
    返回 JSON: {
        'error_code': '...',
        'order_id': '...',
        'status': '...'
    }
    """
    # 其他代码完全复用
```

### 其他场景

- **电商自动下单** - 识别商品、价格、购买按钮
- **社交媒体管理** - 批量点赞、转发、私信
- **数据采集** - 自动翻页、提取表格数据

## 已知限制

1. **依赖屏幕分辨率** - 不同分辨率坐标会变化（可通过相对坐标解决）
2. **依赖页面结构** - 页面改版需要重新训练（可通过定期更新坐标缓存解决）
3. **依赖网络稳定** - API 调用失败会影响执行（已有重试机制）

## 维护者

- **创建时间：** 2026-03-13
- **维护者：** 小九 + 珊瑚海
- **版本：** v1.0

## 更新日志

- **v1.0 (2026-03-13)** - 初始版本，支持抖音评论自动化
