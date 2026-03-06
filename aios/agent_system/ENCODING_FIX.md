# Windows 编码修复指南

## 问题现象

PowerShell 执行 Python 脚本时出现乱码：
```
����λ�� ��:1 �ַ�: 56
```

## 根本原因

- Windows 默认编码：GBK (CP936)
- Python 脚本编码：UTF-8
- PowerShell 终端编码：GBK
- 三者不一致导致乱码

## 解决方案（三层防护）

### 1. 环境变量（推荐，全局生效）

```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING='utf-8'
```

**效果：**
- `PYTHONUTF8=1` - Python 3.7+ 全局 UTF-8 模式
- `PYTHONIOENCODING='utf-8'` - 标准输入输出强制 UTF-8

### 2. 命令行参数（局部生效）

```powershell
& "C:\Program Files\Python312\python.exe" -X utf8 script.py
```

**效果：**
- `-X utf8` - 强制当前进程使用 UTF-8

### 3. 双保险（环境变量 + 参数）

```powershell
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 script.py
```

**效果：**
- 即使忘了带参数，环境变量也能兜底
- 即使环境变量失效，参数也能生效

## 验证方法

```powershell
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -c "import sys; print(f'stdout encoding: {sys.stdout.encoding}'); print(f'UTF-8 mode: {sys.flags.utf8_mode}'); print('测试中文输出')"
```

**预期输出：**
```
stdout encoding: utf-8
UTF-8 mode: 1
测试中文输出
```

## AIOS 应用

所有 Heartbeat 命令已统一使用双保险模式：

**Heartbeat v5.0：**
```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_v5.py
```

**Demo 模式：**
```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_demo.py
```

**Full 模式：**
```powershell
cd C:\Users\A\.openclaw\workspace\aios\agent_system
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; & "C:\Program Files\Python312\python.exe" -X utf8 heartbeat_full.py
```

## 常见问题

### Q: 为什么不直接改 PowerShell 编码？

A: PowerShell 的 `chcp 65001` 会影响所有子进程，可能导致其他工具出问题。环境变量只影响 Python，更安全。

### Q: 为什么不在 Python 脚本里设置编码？

A: 脚本内设置只能影响脚本本身，无法影响 PowerShell 终端显示。环境变量 + 参数能覆盖整个调用链。

### Q: 为什么需要双保险？

A: 防止人为失误（忘了带参数）或环境差异（某些系统环境变量不生效）。双保险确保任何情况下都能正常工作。

## 参考资料

- [PEP 540 - UTF-8 Mode](https://www.python.org/dev/peps/pep-0540/)
- [Python 3.7+ UTF-8 Mode](https://docs.python.org/3/library/os.html#utf-8-mode)
- [PYTHONIOENCODING](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONIOENCODING)

---

**最后更新：** 2026-03-06  
**维护者：** 小九 + 珊瑚海
