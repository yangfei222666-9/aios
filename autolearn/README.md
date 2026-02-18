# autolearn

OpenClaw 自主学习系统 v1.0 — 错误→签名→教训→复测 闭环。

## Quickstart

```powershell
# 健康检查
python -m autolearn health

# 跑全量测试
python -m autolearn retest full

# 生成周报
python -m autolearn report

# 查看提案
python -m autolearn proposals

# 处理 inbox 待分类条目
python -m autolearn triage

# 查看版本
python -m autolearn version
```

## 工作原理

```
错误发生 → executor.run() 捕获
         → sign_strict + sign_loose 生成签名
         → lessons.find() 匹配已有教训 → 返回 tips
         → circuit_breaker 检查熔断（30min 内同 sig ≥3 次）
         → events.jsonl 落盘（带环境指纹）
```

## 目录结构

```
autolearn/
  __main__.py          # CLI 入口
  API.md               # v1.0 稳定 API 文档
  README.md            # 本文件
  core/
    version.py         # 版本常量
    errors.py          # sign_strict / sign_loose
    logger.py          # events.jsonl 写入
    lessons.py         # 教训库 CRUD + 双层匹配
    executor.py        # 统一执行入口
    retest.py          # 分级复测 (smoke/regression/full)
    circuit_breaker.py # 熔断器
    lifecycle.py       # 教训状态自动推进
    proposals.py       # 自动提案生成
    weekly_report.py   # 周报生成
  data/                # 运行时数据 (JSONL)
    events.jsonl
    lessons.jsonl
    retest_results.jsonl
  reports/             # 生成的报告
  inbox.md             # 错误收集箱
  playbook.md          # 操作手册
```

## v1.0 稳定 API

| 函数 | 签名 | 返回 |
|------|------|------|
| `executor.run` | `(intent, tool, payload, do_task)` | `dict` |
| `errors.sign_strict` | `(exc_type, msg)` | `str` |
| `errors.sign_loose` | `(msg)` | `{keywords, sig}` |
| `lessons.find` | `(sig_strict, sig_loose?)` | `tips[]` |
| `retest.run` | `(level)` | `{ok, passed, failed}` |
| `weekly_report.generate` | `(days=7)` | `markdown str` |
| `proposals.generate` | `(window_hours=72)` | `list` |
| `circuit_breaker.allow` | `(sig_strict)` | `bool` |

## 数据格式

所有 JSONL 记录带 `schema_version: "1.0"` + `module_version: "1.0.0"`。

## 对接其他系统

```python
import sys
sys.path.insert(0, "/path/to/autolearn")
from core.executor import run
from core.lessons import find, add_lesson
from core.errors import sign_strict, sign_loose

# 执行任务并自动记录
result = run("my_task", "my_tool", {}, my_function)
if not result["ok"] and result.get("tips"):
    print("建议:", result["tips"][0]["solution"])
```
