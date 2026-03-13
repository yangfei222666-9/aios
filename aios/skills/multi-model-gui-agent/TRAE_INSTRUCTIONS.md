# 给 Trae 的完整指令包

## 项目概述

实现一个多模型协同的 GUI 自动化代理，用于抖音评论自动化和智能客服场景。

**核心架构：**
- 2.0 Lite（老师）- 视觉理解，返回坐标
- 1.6 flash（执行）- 快速操作，生成内容
- 1.6 lite（容灾）- 超时降级，兜底处理

---

## Phase 1: 环境准备（15分钟）

### 1.1 安装 Python 依赖

```bash
pip install pyautogui pillow requests
```

**验证点：** 运行 `python -c "import pyautogui; print('OK')"` 应该输出 `OK`

### 1.2 克隆 UI-TARS-desktop（可选）

```bash
git clone https://github.com/bytedance/UI-TARS-desktop.git
cd UI-TARS-desktop
npm install
npm run build
npm run start
```

**验证点：** 浏览器打开 `http://localhost:3000`，看到 UI-TARS 界面

### 1.3 配置豆包 API

在 UI-TARS 设置中填入豆包 API Key，或直接在 `config.json` 中配置：

```json
{
  "teacher_key": "your-2.0-lite-key",
  "executor_key": "your-1.6-flash-key",
  "fallback_key": "your-1.6-lite-key"
}
```

**验证点：** 运行 `python test_screenshot.py`，所有测试通过

---

## Phase 2: 核心代码实现（30分钟）

### 2.1 实现 MultiModelAgent 类

**要求：**

1. **截图功能**
   - 使用 `PIL.ImageGrab.grab()` 截取全屏
   - 保存为 PNG 格式
   - 记录截图时间和文件大小

2. **视觉理解（teacher_analyze）**
   - 调用豆包 2.0 Lite API
   - 传入截图和 prompt
   - 解析返回的 JSON（坐标信息）
   - 超时时间：10秒

3. **容灾降级（fallback_analyze）**
   - 当 2.0 Lite 超时或失败时触发
   - 调用 1.6 lite API
   - 如果也失败，返回默认坐标
   - 记录降级次数

4. **执行操作（execute）**
   - 使用 `pyautogui.click()` 点击坐标
   - 使用 `pyautogui.write()` 输入文本
   - 每个操作间隔 0.5 秒
   - 记录执行日志

5. **生成内容（generate_comment）**
   - 调用豆包 1.6 flash API
   - 生成 10 字内的评论，带表情
   - 超时时间：3秒
   - 失败时返回默认评论 "666👍"

### 2.2 实现坐标缓存（CoordinateCache）

**要求：**

1. **缓存机制**
   - 使用 JSON 文件存储坐标
   - 缓存键：`{mode}_{file_size}`
   - 缓存值：坐标 JSON

2. **命中率统计**
   - 记录总请求数和命中数
   - 计算命中率：`hits / total_requests`
   - 目标命中率 > 80%

### 2.3 实现重试机制（run_with_retry）

**要求：**

1. **重试策略**
   - 最多重试 3 次
   - 指数退避：2^attempt 秒
   - 记录每次重试的原因

2. **失败处理**
   - 记录失败的 URL
   - 记录错误信息
   - 生成失败报告

### 2.4 实现执行报告（generate_report）

**要求：**

1. **统计信息**
   - 总任务数
   - 成功/失败数
   - 缓存命中率
   - 降级次数

2. **详细结果**
   - 每个 URL 的执行结果
   - 执行耗时
   - 重试次数
   - 错误信息

3. **报告格式**
   - JSON 格式
   - 文件名：`report_YYYYMMDD_HHMMSS.json`
   - 包含时间戳

**验证点：** 运行 `python agent.py --config config.json --urls urls.txt --mode douyin`，生成执行报告

---

## Phase 3: 测试验证（20分钟）

### 3.1 单元测试

创建 `test_agent.py`：

```python
import unittest
from agent import MultiModelAgent, CoordinateCache

class TestMultiModelAgent(unittest.TestCase):
    def test_screenshot(self):
        """测试截图功能"""
        agent = MultiModelAgent('config.json')
        img_path = agent.screenshot()
        self.assertTrue(Path(img_path).exists())
    
    def test_coordinate_cache(self):
        """测试坐标缓存"""
        cache = CoordinateCache()
        cache.set('test_key', {'x': 100, 'y': 200})
        result = cache.get('test_key')
        self.assertEqual(result, {'x': 100, 'y': 200})
    
    def test_fallback(self):
        """测试容灾降级"""
        agent = MultiModelAgent('config.json')
        result = agent.fallback_analyze('test.png', 'douyin')
        self.assertIn('input', result)
        self.assertIn('publish', result)

if __name__ == '__main__':
    unittest.main()
```

**验证点：** 运行 `python test_agent.py`，所有测试通过

### 3.2 集成测试

1. **准备测试数据**
   - 创建 `urls.txt`，包含 5 条测试链接
   - 确保链接可访问

2. **运行完整流程**
   ```bash
   python agent.py --config config.json --urls urls.txt --mode douyin
   ```

3. **验证结果**
   - 检查 `execution.log`，确认每个步骤都有日志
   - 检查 `report_*.json`，确认统计信息正确
   - 检查 `coordinate_cache.json`，确认坐标已缓存

**验证点：** 成功率 > 80%，缓存命中率 > 60%

### 3.3 容灾测试

1. **模拟 2.0 Lite 超时**
   - 修改 `timeout.teacher` 为 0.1 秒
   - 运行代理，观察是否自动降级到 1.6 lite

2. **模拟网络故障**
   - 断开网络
   - 运行代理，观察是否使用默认坐标

3. **模拟连续失败**
   - 使用无效的 API Key
   - 运行代理，观察是否触发告警

**验证点：** 所有容灾机制都正常工作，没有崩溃

---

## Phase 4: 生产部署（15分钟）

### 4.1 性能优化

1. **坐标缓存优化**
   - 预热缓存：提前截图并分析常见页面
   - 缓存过期：24小时后自动失效
   - 缓存清理：定期清理无效缓存

2. **并发优化**
   - 支持多线程处理多个链接
   - 限制并发数：最多 5 个
   - 避免 API 限流

3. **日志优化**
   - 日志分级：INFO/WARNING/ERROR
   - 日志轮转：每天一个文件
   - 日志压缩：保留最近 7 天

**验证点：** 单次操作耗时 < 5s，失败率 < 5%

### 4.2 监控告警

1. **实时监控**
   - 每次执行记录耗时
   - 每次执行记录成功率
   - 每次执行记录降级次数

2. **告警规则**
   - 连续失败 ≥ 3 次 → 发送告警
   - 成功率 < 80% → 发送告警
   - 降级次数 > 50% → 发送告警

3. **日报生成**
   - 每天 23:00 生成执行报告
   - 包含统计信息和趋势图
   - 发送到指定邮箱或 Telegram

**验证点：** 告警机制正常工作，日报按时生成

### 4.3 文档完善

1. **故障排查手册**
   - 常见错误及解决方案
   - 日志分析方法
   - 联系方式

2. **常见问题 FAQ**
   - 如何配置 API Key？
   - 如何调整超时时间？
   - 如何自定义坐标？

3. **扩展开发指南**
   - 如何添加新模式？
   - 如何自定义 prompt？
   - 如何集成到其他系统？

**验证点：** 文档完整，新用户能独立部署

---

## Phase 5: 扩展场景（可选）

### 5.1 智能客服模式

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
        'status': '...',
        'action_button': [x, y]
    }
    """
    # 其他代码完全复用
```

**验证点：** 能正确识别错误码、订单号、异常状态

### 5.2 其他场景

- **电商自动下单** - 识别商品、价格、购买按钮
- **社交媒体管理** - 批量点赞、转发、私信
- **数据采集** - 自动翻页、提取表格数据

---

## 交付清单

完成后应包含以下文件：

```
multi-model-gui-agent/
├── SKILL.md              # 技能文档
├── agent.py              # 主程序
├── config.json           # 配置文件
├── test_screenshot.py    # 测试脚本
├── test_agent.py         # 单元测试
├── urls.txt              # 链接列表
├── README.md             # 使用说明
├── TROUBLESHOOTING.md    # 故障排查
├── FAQ.md                # 常见问题
└── EXTENSION_GUIDE.md    # 扩展指南
```

---

## 成功标准

1. **功能完整性**
   - ✅ 所有核心功能实现
   - ✅ 容灾机制正常工作
   - ✅ 重试机制正常工作
   - ✅ 缓存机制正常工作

2. **性能指标**
   - ✅ 单次操作耗时 < 5s
   - ✅ 成功率 > 80%
   - ✅ 缓存命中率 > 80%
   - ✅ 失败率 < 5%

3. **代码质量**
   - ✅ 代码结构清晰
   - ✅ 注释完整
   - ✅ 日志详细
   - ✅ 错误处理完善

4. **文档完整性**
   - ✅ 使用说明清晰
   - ✅ 故障排查手册完整
   - ✅ 常见问题 FAQ 完整
   - ✅ 扩展指南完整

---

## 时间估算

- Phase 1: 15 分钟
- Phase 2: 30 分钟
- Phase 3: 20 分钟
- Phase 4: 15 分钟
- Phase 5: 可选

**总计：** 约 80 分钟（不含扩展场景）

---

## 注意事项

1. **API Key 安全**
   - 不要提交到 Git
   - 使用环境变量或配置文件
   - 定期轮换

2. **屏幕分辨率**
   - 不同分辨率坐标会变化
   - 建议使用相对坐标
   - 或在配置中指定分辨率

3. **页面加载时间**
   - 不同网速加载时间不同
   - 建议动态检测页面加载完成
   - 或增加等待时间

4. **反爬虫机制**
   - 抖音可能有反爬虫机制
   - 建议增加随机延迟
   - 或使用代理 IP

---

**版本：** v1.0  
**创建时间：** 2026-03-13  
**维护者：** 小九 + 珊瑚海
