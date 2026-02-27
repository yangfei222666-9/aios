"""
PDF Tool - PDF 提取、生成、合并、拆分工具
打工人刚需，零依赖（使用 PyPDF2）
"""
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

try:
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger
except ImportError:
    print("❌ 缺少依赖：pip install PyPDF2")
    sys.exit(1)


class PDFTool:
    """PDF 工具类"""
    
    @staticmethod
    def extract_text(pdf_path: str, pages: Optional[List[int]] = None) -> str:
        """
        提取 PDF 文本
        
        Args:
            pdf_path: PDF 文件路径
            pages: 页码列表（从0开始），None 表示全部页
        
        Returns:
            提取的文本内容
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            if pages is None:
                pages = range(total_pages)
            
            text_parts = []
            for page_num in pages:
                if 0 <= page_num < total_pages:
                    page = reader.pages[page_num]
                    text_parts.append(f"--- 第 {page_num + 1} 页 ---\n")
                    text_parts.append(page.extract_text())
                    text_parts.append("\n\n")
            
            return "".join(text_parts)
        
        except Exception as e:
            return f"❌ 提取失败：{str(e)}"
    
    @staticmethod
    def get_info(pdf_path: str) -> Dict[str, Any]:
        """
        获取 PDF 信息
        
        Returns:
            包含页数、元数据等信息的字典
        """
        try:
            reader = PdfReader(pdf_path)
            
            info = {
                "pages": len(reader.pages),
                "metadata": {},
                "file_size": os.path.getsize(pdf_path)
            }
            
            # 提取元数据
            if reader.metadata:
                for key, value in reader.metadata.items():
                    clean_key = key.replace("/", "")
                    info["metadata"][clean_key] = str(value)
            
            return info
        
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def merge_pdfs(input_paths: List[str], output_path: str) -> str:
        """
        合并多个 PDF
        
        Args:
            input_paths: 输入 PDF 路径列表
            output_path: 输出 PDF 路径
        
        Returns:
            成功消息或错误信息
        """
        try:
            merger = PdfMerger()
            
            for pdf_path in input_paths:
                if not os.path.exists(pdf_path):
                    return f"❌ 文件不存在：{pdf_path}"
                merger.append(pdf_path)
            
            merger.write(output_path)
            merger.close()
            
            return f"✅ 合并成功：{len(input_paths)} 个文件 → {output_path}"
        
        except Exception as e:
            return f"❌ 合并失败：{str(e)}"
    
    @staticmethod
    def split_pdf(input_path: str, output_dir: str, pages_per_file: int = 1) -> str:
        """
        拆分 PDF
        
        Args:
            input_path: 输入 PDF 路径
            output_dir: 输出目录
            pages_per_file: 每个文件包含的页数
        
        Returns:
            成功消息或错误信息
        """
        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            
            os.makedirs(output_dir, exist_ok=True)
            
            base_name = Path(input_path).stem
            file_count = 0
            
            for start_page in range(0, total_pages, pages_per_file):
                writer = PdfWriter()
                
                end_page = min(start_page + pages_per_file, total_pages)
                for page_num in range(start_page, end_page):
                    writer.add_page(reader.pages[page_num])
                
                output_path = os.path.join(
                    output_dir,
                    f"{base_name}_part{file_count + 1}.pdf"
                )
                
                with open(output_path, "wb") as output_file:
                    writer.write(output_file)
                
                file_count += 1
            
            return f"✅ 拆分成功：{total_pages} 页 → {file_count} 个文件（{output_dir}）"
        
        except Exception as e:
            return f"❌ 拆分失败：{str(e)}"
    
    @staticmethod
    def extract_pages(input_path: str, output_path: str, pages: List[int]) -> str:
        """
        提取指定页面
        
        Args:
            input_path: 输入 PDF 路径
            output_path: 输出 PDF 路径
            pages: 页码列表（从0开始）
        
        Returns:
            成功消息或错误信息
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            total_pages = len(reader.pages)
            
            for page_num in pages:
                if 0 <= page_num < total_pages:
                    writer.add_page(reader.pages[page_num])
                else:
                    return f"❌ 页码超出范围：{page_num + 1}（总页数：{total_pages}）"
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            return f"✅ 提取成功：{len(pages)} 页 → {output_path}"
        
        except Exception as e:
            return f"❌ 提取失败：{str(e)}"


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF 工具 - 提取、合并、拆分")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # extract 命令
    extract_parser = subparsers.add_parser("extract", help="提取文本")
    extract_parser.add_argument("pdf", help="PDF 文件路径")
    extract_parser.add_argument("--pages", nargs="+", type=int, help="页码（从1开始）")
    extract_parser.add_argument("--output", "-o", help="输出文件路径")
    
    # info 命令
    info_parser = subparsers.add_parser("info", help="查看信息")
    info_parser.add_argument("pdf", help="PDF 文件路径")
    
    # merge 命令
    merge_parser = subparsers.add_parser("merge", help="合并 PDF")
    merge_parser.add_argument("inputs", nargs="+", help="输入 PDF 文件")
    merge_parser.add_argument("--output", "-o", required=True, help="输出文件路径")
    
    # split 命令
    split_parser = subparsers.add_parser("split", help="拆分 PDF")
    split_parser.add_argument("pdf", help="PDF 文件路径")
    split_parser.add_argument("--output-dir", "-o", required=True, help="输出目录")
    split_parser.add_argument("--pages-per-file", "-p", type=int, default=1, help="每个文件的页数")
    
    # extract-pages 命令
    extract_pages_parser = subparsers.add_parser("extract-pages", help="提取指定页面")
    extract_pages_parser.add_argument("pdf", help="PDF 文件路径")
    extract_pages_parser.add_argument("pages", nargs="+", type=int, help="页码（从1开始）")
    extract_pages_parser.add_argument("--output", "-o", required=True, help="输出文件路径")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tool = PDFTool()
    
    if args.command == "extract":
        pages = [p - 1 for p in args.pages] if args.pages else None
        text = tool.extract_text(args.pdf, pages)
        
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"✅ 文本已保存到：{args.output}")
        else:
            print(text)
    
    elif args.command == "info":
        info = tool.get_info(args.pdf)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    elif args.command == "merge":
        result = tool.merge_pdfs(args.inputs, args.output)
        print(result)
    
    elif args.command == "split":
        result = tool.split_pdf(args.pdf, args.output_dir, args.pages_per_file)
        print(result)
    
    elif args.command == "extract-pages":
        pages = [p - 1 for p in args.pages]
        result = tool.extract_pages(args.pdf, args.output, pages)
        print(result)


if __name__ == "__main__":
    main()
