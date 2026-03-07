"""
生成测试 PDF 文件
"""
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    
    # 创建测试 PDF
    c = canvas.Canvas("test_document.pdf", pagesize=A4)
    
    # 第1页
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Test PDF Document")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "Page 1: Introduction")
    c.drawString(100, 680, "This is a test PDF created for pdf-skill testing.")
    c.drawString(100, 660, "Author: Xiaojiu + Shanhu Hai")
    c.showPage()
    
    # 第2页
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Page 2: Content")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "AIOS - AI Operating System")
    c.drawString(100, 680, "Features:")
    c.drawString(120, 660, "- Self-Improving Loop")
    c.drawString(120, 640, "- DataCollector")
    c.drawString(120, 620, "- Quality Gates")
    c.drawString(120, 600, "- Heartbeat Monitor")
    c.showPage()
    
    # 第3页
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Page 3: Conclusion")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "PDF Skill is working correctly!")
    c.drawString(100, 680, "Version: 1.0.0")
    c.showPage()
    
    c.save()
    print("Test PDF created: test_document.pdf (3 pages)")

except ImportError:
    # 如果没有 reportlab，用 PyPDF2 创建简单 PDF
    from PyPDF2 import PdfWriter
    
    writer = PdfWriter()
    
    for i in range(3):
        page = writer.add_blank_page(width=595, height=842)
    
    with open("test_document.pdf", "wb") as f:
        writer.write(f)
    
    print("Test PDF created: test_document.pdf (3 blank pages)")
