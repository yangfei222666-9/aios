# 故障排查手册

## 常见问题

### 1. 截图失败

**症状：** `PIL.ImageGrab.grab()` 报错

**原因：**
- Windows 权限不足
- 显示器驱动问题
- 多显示器配置问题

**解决方案：**
```bash
# 以管理员身份运行
# 或者指定显示器
img = ImageGrab.grab(bbox=(0, 0, 1920, 1080))
```

---

### 2. API 调用超时

**症状：** `requests.Timeout` 错误

**原因：**
- 网络不稳定
- API 服务器响应慢
- 超时时间设置过短

**解决方案：**
```json
// 增加超时时间
{
  "timeout": {
    "teacher": 20,  // 从 10 增加到 20
    "executor": 5,
    "fallback": 10
  }
}
```

---

### 3. 坐标不准确

**症状：** 点击位置不对

**原因：**
- 屏幕分辨率变化
- 页面布局改版
- 缓存坐标过期

**解决方案：**
```bash
# 清空坐标缓存
rm coordinate_cache.json

# 或者禁用缓存
# 在 agent.py 中注释掉缓存相关代码
```

---

### 4. 连续失败

**症状：** 连续失败 ≥ 3 次

**原因：**
- API Key 无效
- 网络故障
- 页面结构变化
- 反爬虫机制

**解决方案：**
1. 检查 API Key 是否有效
2. 检查网络连接
3. 检查页面是否改版
4. 增加随机延迟：
   ```python
   import random
   time.sleep(random.uniform(2, 5))
   ```

---

### 5. 缓存命中率低

**症状：** 缓存命中率 < 50%

**原因：**
- 页面结构变化频繁
- 缓存键设计不合理
- 缓存过期时间过短

**解决方案：**
```python
# 优化缓存键
cache_key = f"{mode}_{page_type}_{resolution}"

# 增加缓存过期时间
# 在 CoordinateCache 中添加过期时间检查
```

---

### 6. 内存占用过高

**症状：** 内存占用 > 1GB

**原因：**
- 截图未释放
- 日志文件过大
- 缓存文件过大

**解决方案：**
```python
# 及时释放截图
img = ImageGrab.grab()
img.save('screen.png')
del img  # 释放内存

# 定期清理日志
# 定期清理缓存
```

---

### 7. pyautogui 操作失败

**症状：** `pyautogui.click()` 无效

**原因：**
- 窗口未激活
- 坐标超出屏幕范围
- 安全模式阻止

**解决方案：**
```python
# 激活窗口
pyautogui.click(x, y)
time.sleep(0.5)

# 检查坐标范围
screen_width, screen_height = pyautogui.size()
if x < 0 or x > screen_width or y < 0 or y > screen_height:
    raise ValueError(f"坐标超出范围: ({x}, {y})")

# 禁用安全模式（谨慎使用）
pyautogui.FAILSAFE = False
```

---

## 日志分析

### 查看执行日志

```bash
# 查看最近 50 行
tail -n 50 execution.log

# 查看错误日志
grep ERROR execution.log

# 查看超时日志
grep Timeout execution.log
```

### 查看执行报告

```bash
# 查看最新报告
ls -lt report_*.json | head -n 1

# 分析成功率
cat report_*.json | jq '.summary.success / .summary.total'

# 分析缓存命中率
cat report_*.json | jq '.cache_hit_rate'
```

---

## 性能调优

### 1. 减少 API 调用

```python
# 启用坐标缓存
# 预热缓存
# 批量处理
```

### 2. 并发处理

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(agent.run_with_retry, urls)
```

### 3. 优化截图

```python
# 只截取需要的区域
img = ImageGrab.grab(bbox=(0, 0, 1920, 1080))

# 降低截图质量
img.save('screen.png', quality=70)
```

---

## 联系方式

如果以上方法都无法解决问题，请联系：

- **Telegram:** @shh7799
- **GitHub Issues:** [提交问题](https://github.com/your-repo/issues)
- **邮箱:** your-email@example.com

---

**版本：** v1.0  
**最后更新：** 2026-03-13
