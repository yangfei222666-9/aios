# Stop-Process 权限不足

- **日期**: 2026-02-19
- **类别**: permission
- **严重度**: low

## 场景
尝试 `Stop-Process -Name "L-Connect-Service" -Force` 被拒绝

## 原因
系统服务进程需要管理员权限才能终止

## 正确做法
用 `Start-Process powershell -Verb RunAs` 提权执行

## 复测命令
```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-Command "whoami /priv"'
```
