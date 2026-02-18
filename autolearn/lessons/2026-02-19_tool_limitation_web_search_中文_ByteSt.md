# web_search 中文 ByteString bug

- **日期**: 2026-02-19
- **类别**: tool_limitation
- **严重度**: medium (工具限制，非代码错误)

## 场景
搜索包含中文的查询时报 ByteString 编码错误

## 原因
web_search 工具内部的 ByteString 转换不支持 Unicode 字符

## 正确做法
用英文关键词搜索，或用 web_fetch 直接访问已知 URL

## 复测命令
```powershell
# No auto-verify available
```
