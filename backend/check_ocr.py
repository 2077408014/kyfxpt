import sys
sys.path.insert(0, '.')

try:
    from rapidocr_onnxruntime import RapidOCR
    print("RapidOCR available")
except:
    print("RapidOCR NOT available")

try:
    import fitz
    print(f"fitz available, version: {fitz.version}")
except:
    print("fitz NOT available")

try:
    from PIL import Image
    print("PIL available")
except:
    print("PIL NOT available")

import os
pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'
print(f"PDF size: {os.path.getsize(pdf_path)/1024/1024:.1f} MB")

doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(dpi=150)
print(f"Page 0 pixmap: {pix.width}x{pix.height}")
print(f"Estimated pages: {len(doc)}")
doc.close()