#!/usr/bin/env python3
"""
Document Agent - 文档处理 Agent
支持 docx/pdf/txt 文档的提取、摘要、结构化输出
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def extract_text_from_txt(file_path: Path) -> str:
    """从 txt 文件提取文本"""
    try:
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return ""
    except Exception as e:
        print(f"⚠️  读取 txt 失败: {e}")
        return ""


def extract_text_from_docx(file_path: Path) -> str:
    """从 docx 文件提取文本"""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        print("⚠️  需要安装 python-docx: pip install python-docx")
        return ""
    except Exception as e:
        print(f"⚠️  读取 docx 失败: {e}")
        return ""


def extract_text_from_pdf(file_path: Path) -> str:
    """从 pdf 文件提取文本"""
    try:
        import pdfplumber
        text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    except ImportError:
        print("⚠️  需要安装 pdfplumber: pip install pdfplumber")
        return ""
    except Exception as e:
        print(f"⚠️  读取 pdf 失败: {e}")
        return ""


def extract_text(file_path: Path) -> str:
    """根据文件类型提取文本"""
    suffix = file_path.suffix.lower()
    
    if suffix == '.txt':
        return extract_text_from_txt(file_path)
    elif suffix == '.docx':
        return extract_text_from_docx(file_path)
    elif suffix == '.pdf':
        return extract_text_from_pdf(file_path)
    else:
        print(f"⚠️  不支持的文件类型: {suffix}")
        return ""


def generate_summary(text: str, max_length: int = 500) -> str:
    """生成摘要（简单版本：提取前N个字符）"""
    # TODO: 集成 LLM 生成智能摘要
    if len(text) <= max_length:
        return text
    
    # 简单截断到句子边界
    truncated = text[:max_length]
    last_period = max(truncated.rfind('。'), truncated.rfind('.'), truncated.rfind('！'), truncated.rfind('!'))
    
    if last_period > 0:
        return truncated[:last_period + 1] + "..."
    else:
        return truncated + "..."


def extract_outline(text: str) -> List[str]:
    """提取大纲（简单版本：提取标题行）"""
    lines = text.split('\n')
    outline = []
    
    for line in lines:
        line = line.strip()
        # 检测标题（简单规则）
        if line and (
            line.startswith('#') or  # Markdown 标题
            line.isupper() or  # 全大写
            (len(line) < 50 and not line.endswith(('。', '.', '，', ',')))  # 短行且不以标点结尾
        ):
            outline.append(line.lstrip('#').strip())
    
    return outline[:20]  # 最多20个标题


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """提取关键词（简单版本：词频统计）"""
    # TODO: 使用 TF-IDF 或 LLM 提取
    import re
    from collections import Counter
    
    # 移除标点和数字
    words = re.findall(r'[a-zA-Z\u4e00-\u9fa5]{2,}', text)
    
    # 过滤停用词（简单版本）
    stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    words = [w for w in words if w not in stopwords and len(w) > 1]
    
    # 统计词频
    counter = Counter(words)
    return [word for word, count in counter.most_common(top_k)]


def process_document(file_path: Path, output_format: str = "json") -> Dict:
    """处理文档"""
    print(f"📄 处理文档: {file_path.name}")
    
    # 1. 提取文本
    print("   提取文本...")
    text = extract_text(file_path)
    
    if not text:
        return {
            "error": "无法提取文本",
            "file": str(file_path)
        }
    
    # 2. 生成摘要
    print("   生成摘要...")
    summary = generate_summary(text, max_length=500)
    
    # 3. 提取大纲
    print("   提取大纲...")
    outline = extract_outline(text)
    
    # 4. 提取关键词
    print("   提取关键词...")
    keywords = extract_keywords(text, top_k=10)
    
    # 5. 统计信息
    word_count = len(text)
    line_count = len(text.split('\n'))
    
    result = {
        "file": str(file_path),
        "filename": file_path.name,
        "type": file_path.suffix,
        "processed_at": datetime.now().isoformat(),
        "stats": {
            "characters": word_count,
            "lines": line_count
        },
        "summary": summary,
        "outline": outline,
        "keywords": keywords
    }
    
    print(f"✅ 完成！")
    print(f"   字符数: {word_count}")
    print(f"   大纲: {len(outline)} 个标题")
    print(f"   关键词: {', '.join(keywords[:5])}")
    
    return result


def save_result(result: Dict, output_path: Path, format: str = "json"):
    """保存结果"""
    if format == "json":
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    elif format == "markdown":
        md = f"""# {result['filename']}

## 摘要

{result['summary']}

## 大纲

{chr(10).join(f"- {item}" for item in result['outline'])}

## 关键词

{', '.join(result['keywords'])}

## 统计

- 字符数: {result['stats']['characters']}
- 行数: {result['stats']['lines']}
- 处理时间: {result['processed_at']}
"""
        output_path.write_text(md, encoding="utf-8")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
📄 Document Agent - 文档处理工具

用法:
  python document_agent.py <文件路径> [输出格式]

输出格式:
  json (默认) - JSON 格式
  markdown    - Markdown 格式

示例:
  python document_agent.py report.docx
  python document_agent.py report.pdf markdown
        """)
        return
    
    file_path = Path(sys.argv[1])
    output_format = sys.argv[2] if len(sys.argv) > 2 else "json"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    # 处理文档
    result = process_document(file_path, output_format)
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    # 保存结果
    output_ext = ".json" if output_format == "json" else ".md"
    output_path = file_path.with_suffix(output_ext)
    save_result(result, output_path, output_format)
    
    print(f"\n💾 结果已保存: {output_path}")


if __name__ == "__main__":
    main()
