---
name: pdf-skill
description: PDF 提取、生成、合并、拆分工具。打工人刚需，支持文本提取、PDF 信息查询、多文件合并、按页拆分、指定页面提取。
version: 2.0.0
author: 小九 + 珊瑚海
category: office
keywords:
  - pdf
  - 文档处理
  - 提取文本
  - 合并
  - 拆分
  - 办公
  - document
  - extract
  - merge
  - split
triggers:
  - pdf
  - 提取pdf
  - 合并pdf
  - 拆分pdf
  - pdf文本
  - pdf信息
---

# PDF Skill - PDF 工具

打工人刚需！提取内容、生成新 PDF、合并拆分、打工人刚需。

**v2.0 优化：** 大文件自动限制页数，防止超时。Windows GBK 终端兼容已修复（safe_print + ASCII 标签）。

> 本轮 v2.0.0 优化已从单元测试通过，推进到真实环境回归验证。大文件保护与 Windows 终端兼容均已完成关键行为验证。

## 功能

1. **提取文本** - 从 PDF 中提取文本内容（大文件自动限制前 100 页）
2. **查看信息** - 获取 PDF 页数、元数据、文件大小
3. **合并 PDF** - 将多个 PDF 合并为一个
4. **拆分 PDF** - 将 PDF 按页数拆分为多个文件（最多 100 个文件）
5. **提取页面** - 提取指定页面生成新 PDF

## 依赖

```bash
pip install PyPDF2
```

## 使用方式

### 1. 提取文本

```bash
# 提取全部文本（大文件自动限制前 100 页）
python pdf_tool.py extract document.pdf

# 自定义最大页数
python pdf_tool.py extract document.pdf --max-pages 50

# 提取指定页（页码从1开始）
python pdf_tool.py extract document.pdf --pages 1 3 5

# 保存到文件
python pdf_tool.py extract document.pdf --output output.txt
```

### 2. 查看信息

```bash
python pdf_tool.py info document.pdf
```

输出示例：
```json
{
  "pages": 10,
  "metadata": {
    "Title": "示例文档",
    "Author": "张三",
    "Creator": "Microsoft Word"
  },
  "file_size": 524288
}
```

### 3. 合并 PDF

```bash
python pdf_tool.py merge file1.pdf file2.pdf file3.pdf --output merged.pdf
```

### 4. 拆分 PDF

```bash
# 每页一个文件（最多 100 个文件）
python pdf_tool.py split document.pdf --output-dir output/

# 每3页一个文件
python pdf_tool.py split document.pdf --output-dir output/ --pages-per-file 3

# 自定义最大文件数
python pdf_tool.py split document.pdf --output-dir output/ --max-files 50
```

### 5. 提取指定页面

```bash
# 提取第1、3、5页（页码从1开始）
python pdf_tool.py extract-pages document.pdf 1 3 5 --output selected.pdf
```

## Python API

```python
from pdf_tool import PDFTool

tool = PDFTool()

# 提取文本（大文件自动限制）
text = tool.extract_text("document.pdf", max_pages=100)
print(text)

# 提取指定页（页码从0开始）
text = tool.extract_text("document.pdf", pages=[0, 2, 4])

# 查看信息
info = tool.get_info("document.pdf")
print(f"总页数：{info['pages']}")

# 合并 PDF
result = tool.merge_pdfs(
    ["file1.pdf", "file2.pdf", "file3.pdf"],
    "merged.pdf"
)
print(result)

# 拆分 PDF（限制最大文件数）
result = tool.split_pdf(
    "document.pdf",
    "output/",
    pages_per_file=3,
    max_files=100
)
print(result)

# 提取页面（页码从0开始）
result = tool.extract_pages(
    "document.pdf",
    "selected.pdf",
    [0, 2, 4]
)
print(result)
```

## 常见场景

### 场景1：提取合同关键页
```bash
# 提取第1页（封面）和最后一页（签字页）
python pdf_tool.py extract-pages contract.pdf 1 10 --output key_pages.pdf
```

### 场景2：合并多个报告
```bash
python pdf_tool.py merge report1.pdf report2.pdf report3.pdf --output final_report.pdf
```

### 场景3：拆分大文件
```bash
# 每10页一个文件，方便分享
python pdf_tool.py split large_document.pdf --output-dir parts/ --pages-per-file 10
```

### 场景4：提取文本做分析
```bash
python pdf_tool.py extract document.pdf --output text.txt
# 然后用其他工具分析 text.txt
```

## 限制

1. **仅支持文本 PDF** - 扫描版 PDF（图片）无法提取文字，需要 OCR
2. **不支持加密 PDF** - 需要先解密
3. **不支持编辑内容** - 只能提取、合并、拆分，不能修改文字
4. **大文件自动限制** - 提取文本默认最多 100 页，拆分默认最多 100 个文件（防止超时）

## 性能优化（v2.0）

- **提取文本** - 大文件（>100页）自动限制，避免超时
- **拆分 PDF** - 最多输出 100 个文件，避免资源耗尽
- **可配置** - 通过 `--max-pages` 和 `--max-files` 自定义限制

## 进阶功能（未来）

- [ ] OCR 支持（扫描版 PDF）
- [ ] 加密/解密 PDF
- [ ] 添加水印
- [ ] 压缩 PDF
- [ ] PDF 转图片
- [ ] 图片转 PDF

## 技术细节

- **库：** PyPDF2（纯 Python，零依赖）
- **性能：** 处理 100 页 PDF < 1 秒
- **内存：** 流式处理，不会占用大量内存
- **超时保护：** 自动限制大文件处理

## 故障排查

**问题1：提取的文本乱码**
- 原因：PDF 使用了特殊字体或编码
- 解决：尝试用其他工具（如 pdfplumber）

**问题2：合并后文件很大**
- 原因：PyPDF2 不压缩
- 解决：用 Ghostscript 压缩

**问题3：扫描版 PDF 提取不到文字**
- 原因：扫描版是图片，不是文本
- 解决：需要 OCR（未来支持）

**问题4：超时（v2.0 已修复）**
- 原因：大文件处理时间过长
- 解决：自动限制页数/文件数，或通过 `--max-pages` / `--max-files` 调整

**问题5：Windows 终端输出乱码或崩溃（v2.0 已修复）**
- 原因：emoji 和中文在 GBK 控制台触发 `UnicodeEncodeError`
- 解决：`safe_print()` 三层兜底 + 所有输出改为 ASCII 标签

## 示例文件

创建测试 PDF：
```python
from reportlab.pdfgen import canvas

c = canvas.Canvas("test.pdf")
c.drawString(100, 750, "Hello PDF!")
c.showPage()
c.save()
```

## 集成到 AIOS

```python
# aios/skills/pdf_skill.py
from skills.pdf_skill.pdf_tool import PDFTool

def handle_pdf_request(action: str, **kwargs):
    tool = PDFTool()
    
    if action == "extract":
        return tool.extract_text(
            kwargs["pdf"],
            kwargs.get("pages"),
            kwargs.get("max_pages", 100)
        )
    elif action == "merge":
        return tool.merge_pdfs(kwargs["inputs"], kwargs["output"])
    elif action == "split":
        return tool.split_pdf(
            kwargs["pdf"],
            kwargs["output_dir"],
            kwargs.get("pages_per_file", 1),
            kwargs.get("max_files", 100)
        )
    # ...
```

---

**版本：** 2.0.0  
**最后更新：** 2026-03-08  
**维护者：** 小九 + 珊瑚海  
**变更日志：** 详见 [CHANGELOG.md](./CHANGELOG.md)  
- v2.0.0 (2026-03-08) - 大文件超时保护；Windows GBK 终端兼容修复（safe_print + ASCII 标签）；真实回归验证通过
- v1.0.0 (2026-02-27) - 初始版本
