# 2026-02-23 工作日志（续）

## AIOS Pipeline 编码修复

### 问题
- pipeline.py 运行时出现 UnicodeDecodeError
- 错误来自 subprocess 调用 PowerShell 命令
- 3 个线程同时报错（sensors 模块的 3 个探针）

### 根本原因
- sensors.py 中 3 处 subprocess.run 调用没有指定编码
- ProcessMonitor: Get-Process 输出
- SystemHealth: Get-CimInstance 内存查询
- NetworkProbe: ping 命令输出
- PowerShell 默认输出 GBK，Python 期望 UTF-8

### 解决方案
1. pipeline.py 头部加 `os.environ['PYTHONIOENCODING'] = 'utf-8'`
2. sensors.py 所有 subprocess.run 加 `encoding='utf-8', errors='replace'`
3. 3 处修改：
   - ProcessMonitor.scan() line 135
   - SystemHealth.scan() line 193
   - NetworkProbe.scan() line 244

### 测试结果
- ✅ 无 UnicodeDecodeError
- ✅ 无 Exception/Traceback
- ✅ Pipeline 正常运行（482ms）
- ✅ 所有阶段全绿
- ⚠️ PowerShell 终端 emoji 乱码（不影响功能，是终端问题）

### 文件变更
- aios/pipeline.py: 加 PYTHONIOENCODING + stderr 包装
- aios/core/sensors.py: 3 处 subprocess.run 加编码参数

### 关键教训
- Windows subprocess 调用必须显式指定 encoding='utf-8'
- errors='replace' 避免解码失败导致崩溃
- 环境变量 PYTHONIOENCODING 是全局保险
