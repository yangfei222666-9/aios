# Autolearn Inbox
# 错误和事件先记录在这里，等待 triage 处理
# 格式：每条一个 section

## 2026-02-19 | PowerShell dir 参数错误
- **场景**: 执行 `dir "C:\Users\A\Downloads" /O-D /B` 报错
- **原因**: PowerShell 的 `dir` 是 `Get-ChildItem` 的别名，不支持 cmd 的 `/O-D /B` 参数
- **正确做法**: 用 `Get-ChildItem ... | Sort-Object LastWriteTime -Descending`
- **严重度**: low
- **状态**: processed

## 2026-02-19 | ~ 路径未展开
- **场景**: 脚本路径用 `~\.openclaw\workspace\scripts\health_check.ps1`，执行失败
- **原因**: 在某些执行环境中 `~` 不会被展开为 `$env:USERPROFILE`
- **正确做法**: 始终使用绝对路径或 `$env:USERPROFILE` 变量
- **严重度**: medium
- **状态**: processed

## 2026-02-19 | web_search 中文 ByteString bug
- **场景**: 搜索包含中文的查询时报 ByteString 编码错误
- **原因**: web_search 工具内部的 ByteString 转换不支持 Unicode 字符
- **正确做法**: 用英文关键词搜索，或用 web_fetch 直接访问已知 URL
- **严重度**: medium (工具限制，非代码错误)
- **状态**: processed

## 2026-02-19 | Stop-Process 权限不足
- **场景**: 尝试 `Stop-Process -Name "L-Connect-Service" -Force` 被拒绝
- **原因**: 系统服务进程需要管理员权限才能终止
- **正确做法**: 用 `Start-Process powershell -Verb RunAs` 提权执行
- **严重度**: low
- **状态**: processed
