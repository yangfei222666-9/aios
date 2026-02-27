"""
从零构建大语言模型 - 章节提取工具
"""
import PyPDF2
import sys

pdf_path = r"C:\Users\A\Downloads\Telegram Desktop\从零构建大语言模型（中文版）.pdf"

with open(pdf_path, 'rb') as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    total_pages = len(reader.pages)
    
    print(f"总页数: {total_pages}\n")
    
    # 提取前 50 页的内容（包含第 1-3 章）
    for i in range(min(50, total_pages)):
        text = reader.pages[i].extract_text()
        if text.strip():
            print(f"\n{'='*60}")
            print(f"第 {i+1} 页")
            print('='*60)
            print(text[:500])  # 每页只显示前 500 字符
