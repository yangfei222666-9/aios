# AIOS 常见问题解答 (FAQ)

## 1. 如何启动 Memory Server？

Memory Server 用于保持 embedding 模型热加载，消除冷启动延迟。需要在每次重启电脑后手动启动。

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python memory_server.py
```

服务将在端口 7788 上运行，可通过 `http://127.0.0.1:7788/status` 检查状态。

---

## 2. 如何启动 AIOS Dashboard？

Dashboard 提供可视化界面来管理和监控 AIOS 系统。默认使用 v3.4 版本。

```bash
cd C:\Users\A\.openclaw\workspace\aios\dashboard\AIOS-Dashboard-v3.4
python server.py
```

启动后访问 `http://127.0.0.1:8888` 即可使用。

---

## 3. Memory Server 启动失败怎么办？

常见原因包括端口被占用或 Python 环境问题。首先检查端口 7788 是否被占用，然后确认 Python 版本和依赖。

```bash
netstat -ano | findstr :7788
pip install -r requirements.txt
```

如果端口被占用，可以终止占用进程或修改配置文件中的端口号。

---

## 4. 如何处理语音消息中的应用别名？

AIOS 使用 `aios/core/app_alias.py` 的 `resolve()` 函数进行别名归一化，自动处理繁简转换和 ASR 识别错误。

```python
from aios.core.app_alias import resolve
canonical_name = resolve("QQ音乐")  # 返回标准化名称
```

系统会自动将语音识别的错词（如"扣扣音乐"）映射到正确的应用名称。

---

## 5. 如何添加新的应用路径？

在 `TOOLS.md` 或相应配置文件中添加应用的完整路径。确保路径使用绝对路径以避免找不到文件。

```markdown
## 应用路径
- 应用名称 → E:\Path\To\Application.exe
```

添加后，系统可以通过语音或文本命令直接启动该应用。

---

## 6. Memory Server 的接口有哪些？

Memory Server 提供 RESTful API 用于查询、摄取和反馈操作。主要接口包括状态检查、向量查询、文档摄取和用户反馈。

```bash
GET  http://127.0.0.1:7788/status      # 检查服务状态
POST http://127.0.0.1:7788/query       # 向量相似度查询
POST http://127.0.0.1:7788/ingest      # 摄取新文档
POST http://127.0.0.1:7788/feedback    # 提交反馈
```

---

## 7. 如何让 Memory Server 开机自启？

可以通过 Windows 任务计划程序或启动文件夹实现开机自启。推荐使用任务计划程序以获得更好的控制。

```bash
# 创建快捷方式到启动文件夹
shell:startup
```

或在任务计划程序中创建新任务，触发器设为"启动时"，操作设为运行 `memory_server.py`。

---

## 8. Dashboard 无法访问怎么办？

检查服务是否正常启动、端口 8888 是否被占用、防火墙设置是否阻止访问。

```bash
netstat -ano | findstr :8888
python server.py  # 查看启动日志
```

确保在启动 Dashboard 前已经启动了 Memory Server，因为 Dashboard 可能依赖后端服务。

---

## 9. 如何查看 AIOS 系统日志？

系统日志通常存储在 `memory/` 目录下，按日期组织。可以直接查看对应日期的 Markdown 文件。

```bash
# 查看今天的日志
type memory\2025-01-XX.md

# 查看长期记忆
type MEMORY.md
```

日志包含操作记录、决策过程和重要事件，便于追溯和调试。

---

## 10. 语音命令执行失败如何调试？

首先检查语音转写是否正确，然后验证别名解析和命令执行逻辑。查看日志中的错误信息和堆栈跟踪。

```python
# 测试别名解析
from aios.core.app_alias import resolve
print(resolve("你的语音输入"))

# 检查应用路径是否存在
import os
print(os.path.exists("E:\\QQMusic\\QQMusic.exe"))
```

如果是 ASR 识别问题，可以在 `app_alias.py` 中添加新的别名映射规则。

---

## 贡献

如有其他常见问题，欢迎提交 Issue 或 Pull Request 补充本文档。
