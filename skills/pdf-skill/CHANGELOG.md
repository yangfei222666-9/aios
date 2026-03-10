# PDF Skill - Changelog

## v2.0.0 (2026-03-08)

### 本次新增能力

- **大文件页数保护** - 提取文本默认最多 100 页，防止超时
- **拆分文件数保护** - 拆分 PDF 默认最多 100 个文件，防止资源耗尽
- **可配置限制** - 通过 `--max-pages` 和 `--max-files` 自定义限制
- **Windows 终端兼容** - 修复 GBK 控制台 Unicode 输出问题

### 已验证场景

**正常场景：**
- 3 页小文件提取 ✓
- 3 页文件拆分（每页一个文件）✓
- 2 个文件合并 ✓
- 指定页面提取 ✓

**边界场景：**
- 150 页大文件提取（自动限制前 5 页）✓
- 3 页文件拆分限制最多 2 个文件（触发 WARN）✓
- Windows GBK 终端输出（无 crash）✓

**实际输出表现：**
```
[WARN] File too large (150 pages), extracting first 5 only
[WARN] Max file limit reached (2), remaining pages skipped
[OK] Merged 2 files -> merged.pdf
[OK] Split done: 3 pages -> 2 files (demo_split)
```

### 已发现并修复的问题

**问题：Windows GBK 控制台下 Unicode 输出崩溃**
- **现象：** emoji（❌、✅、⚠️）和中文在 GBK 终端触发 `UnicodeEncodeError`
- **影响：** 命令直接崩溃，无法正常使用
- **修复方式：**
  1. 新增 `safe_print()` 函数 - 三层兜底（正常输出 → replace 降级 → buffer 写入）
  2. 所有 emoji 替换为 ASCII 标签（`❌→[ERROR]`、`✅→[OK]`、`⚠️→[WARN]`）
  3. 页面分隔符从 `第 X 页` 改为 `Page X`（避免 GBK 乱码）
  4. 所有外部输出从 `print()` 改为 `safe_print()`
- **验证：** 真实 Windows 终端回归通过，零 crash

### 仍待补完的边界

- **OCR 支持** - 扫描版 PDF 文本提取（需要额外依赖）
- **加密 PDF** - 当前不支持加密文件
- **性能基准** - 不同文件大小的处理时间统计

---

## v1.0.0 (2026-02-27)

### 初始版本

- 提取文本（全部页 / 指定页）
- 查看 PDF 信息（页数、元数据、文件大小）
- 合并多个 PDF
- 拆分 PDF（按页数）
- 提取指定页面

**已知限制：**
- 大文件无超时保护
- Windows 终端 Unicode 兼容问题
