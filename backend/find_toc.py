import sys, time
sys.path.insert(0, '.')
import fitz
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'

print("Loading OCR engine...")
ocr = RapidOCR()
print("Engine loaded.")

doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

# Check first 20 pages for table of contents
for page_num in range(min(20, len(doc))):
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img_np = np.array(img)
    result, _ = ocr(img_np)
    
    if result:
        texts = [item[1] for item in result]
        page_text = ' '.join(texts)
        print(f"\n=== Page {page_num+1} ===")
        print(page_text[:300])
        
        if '罚函数' in page_text or '罚' in page_text:
            print(f"  *** FOUND '罚' related content! ***")

doc.close()