# PowerShell dir 参数错误

- **日期**: 2026-02-19
- **类别**: powershell
- **严重度**: low

## 场景
执行 `dir "C:\Users\A\Downloads" /O-D /B` 报错

## 原因
PowerShell 的 `dir` 是 `Get-ChildItem` 的别名，不支持 cmd 的 `/O-D /B` 参数

## 正确做法
用 `Get-ChildItem ... | Sort-Object LastWriteTime -Descending`

## 复测命令
```powershell
Get-ChildItem "$env:USERPROFILE\Downloads" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name
```
