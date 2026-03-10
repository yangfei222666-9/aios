from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

c = canvas.Canvas("test_large.pdf", pagesize=letter)
for i in range(150):
    c.drawString(100, 700, f"Page {i+1} of 150 - Large file test")
    c.drawString(100, 680, "A" * 500)
    c.showPage()
c.save()
size = os.path.getsize("test_large.pdf")
print(f"Created: {size} bytes, 150 pages")
