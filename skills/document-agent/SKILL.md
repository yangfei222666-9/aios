---
name: document-agent
description: Process documents (docx/pdf/txt) to extract text, generate summaries, extract outlines, and identify keywords. Use when users need to analyze documents, create summaries, or extract structured information from files.
---

# Document Agent - 文档处理 Agent

## 核心功能

自动处理文档，提取关键信息：

1. **文本提取** - 支持 docx/pdf/txt 格式
2. **智能摘要** - 生成文档摘要（前500字符）
3. **大纲提取** - 自动识别标题结构
4. **关键词提取** - 词频统计，提取核心关键词
5. **统计信息** - 字符数、行数、处理时间

## 使用方式

### 命令行

```bash
python document_agent.py <文件路径> [输出格式]
```

**输出格式：**
- `json` (默认) - JSON 格式
- `markdown` - Markdown 格式

**示例：**
```bash
# 处理 Word 文档
python document_agent.py report.docx

# 处理 PDF 并输出 Markdown
python document_agent.py report.pdf markdown

# 处理文本文件
python document_agent.py notes.txt
```

### 在 OpenClaw 中使用

当用户说"帮我分析这个文档"或"总结一下这个PDF"时：

```bash
cd C:\Users\A\.openclaw\workspace\skills\document-agent
$env:PYTHONIOENCODING='utf-8'
python document_agent.py <文件路径> markdown
```

## 输出示例

### JSON 格式

```json
{
  "file": "C:\\Users\\A\\Documents\\report.docx",
  "filename": "report.docx",
  "type": ".docx",
  "processed_at": "2026-02-26T15:40:00",
  "stats": {
    "characters": 5234,
    "lines": 156
  },
  "summary": "这是一份关于项目进展的报告...",
  "outline": [
    "项目概述",
    "核心功能",
    "技术架构",
    "进度安排"
  ],
  "keywords": [
    "项目", "功能", "架构", "进度", "团队"
  ]
}
```

### Markdown 格式

```markdown
# report.docx

## 摘要

这是一份关于项目进展的报告...

## 大纲

- 项目概述
- 核心功能
- 技术架构
- 进度安排

## 关键词

项目, 功能, 架构, 进度, 团队

## 统计

- 字符数: 5234
- 行数: 156
- 处理时间: 2026-02-26T15:40:00
```

## 支持的文件格式

| 格式 | 扩展名 | 依赖 |
|------|--------|------|
| 文本 | .txt | 无 |
| Word | .docx | python-docx |
| PDF | .pdf | pdfplumber |

## 安装依赖

```bash
# Word 文档支持
pip install python-docx

# PDF 支持
pip install pdfplumber
```

## 功能详解

### 1. 文本提取

**txt 文件：**
- 自动检测编码（utf-8/gbk/gb2312/latin-1）
- 容错处理

**docx 文件：**
- 提取所有段落文本
- 保留换行结构

**pdf 文件：**
- 逐页提取文本
- 处理多页文档

### 2. 智能摘要

**当前版本（简单）：**
- 提取前500字符
- 在句子边界截断
- 添加省略号

**未来版本（LLM）：**
- 集成 Claude/GPT 生成智能摘要
- 可配置摘要长度
- 多语言支持

### 3. 大纲提取

**识别规则：**
- Markdown 标题（# 开头）
- 全大写行
- 短行且不以标点结尾

**限制：**
- 最多提取20个标题
- 简单规则，可能不准确

### 4. 关键词提取

**当前版本（词频）：**
- 统计词频
- 过滤停用词
- 返回 Top 10

**未来版本（TF-IDF/LLM）：**
- TF-IDF 算法
- LLM 提取核心概念
- 多语言支持

## 集成到 AIOS

### 作为 Agent 任务

在 `task_queue.jsonl` 中添加：

```json
{
  "type": "document",
  "priority": "normal",
  "task": "process_document",
  "params": {
    "file_path": "C:\\Users\\A\\Documents\\report.docx",
    "output_format": "markdown"
  }
}
```

### 通过 Orchestrator 调用

```python
from orchestrator import Orchestrator

orch = Orchestrator()
result = orch.execute_task({
    "type": "document",
    "file_path": "report.docx",
    "output_format": "json"
})
```

## 使用场景

### 场景 1：会议纪要摘要

**输入：** meeting_notes.docx（5000字）  
**输出：** 500字摘要 + 大纲 + 关键词

### 场景 2：研究论文分析

**输入：** research_paper.pdf（20页）  
**输出：** 摘要 + 章节大纲 + 核心概念

### 场景 3：批量文档处理

**输入：** 文件夹中的所有 docx 文件  
**输出：** 每个文件的 JSON 摘要

## 限制

1. **摘要质量** - 当前版本只是简单截断，未来会集成 LLM
2. **大纲识别** - 基于简单规则，可能不准确
3. **关键词提取** - 词频统计，未考虑语义
4. **语言支持** - 主要针对中英文，其他语言可能效果不佳

## 未来改进

- [ ] 集成 LLM 生成智能摘要
- [ ] TF-IDF 关键词提取
- [ ] 支持更多格式（pptx/xlsx/html）
- [ ] 批量处理模式
- [ ] 文档对比功能
- [ ] 多语言支持
- [ ] 自定义摘要长度
- [ ] 导出为多种格式（PDF/HTML/Markdown）

---

**版本：** 1.0  
**最后更新：** 2026-02-26  
**维护者：** 小九 + 珊瑚海
