"""
提取《从零构建大语言模型》第 1-3 章大纲
"""
import pdfplumber

pdf_path = r"C:\Users\A\Downloads\Telegram Desktop\从零构建大语言模型（中文版）.pdf"

print("正在提取 PDF 内容...\n")

with pdfplumber.open(pdf_path) as pdf:
    print(f"总页数: {len(pdf.pages)}\n")
    
    # 提取前 80 页（估计包含第 1-3 章）
    all_text = []
    for i in range(min(80, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()
        if text:
            all_text.append(f"=== 第 {i+1} 页 ===\n{text}\n")
    
    # 保存到文件
    output_file = r"C:\Users\A\.openclaw\workspace\llm_book_chapters_1-3.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_text))
    
    print(f"✅ 已提取前 80 页内容到: {output_file}")
    print(f"文件大小: {len(''.join(all_text))} 字符")
