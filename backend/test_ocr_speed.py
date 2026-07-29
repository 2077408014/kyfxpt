import sys, time
import fitz
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'

print("Loading OCR engine...")
start = time.time()
ocr = RapidOCR()
print(f"Engine loaded in {time.time()-start:.1f}s")

doc = fitz.open(pdf_path)

for page_num in [0, 10, 100, 200]:
    if page_num >= len(doc):
        break
    page = doc[page_num]
    
    for scale in [0.5, 0.7, 1.0]:
        print(f"\nPage {page_num+1} at {scale}x scale:")
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img_np = np.array(img)
        print(f"  Image: {img_np.shape}")
        
        start = time.time()
        result, _ = ocr(img_np)
        elapsed = time.time() - start
        print(f"  OCR: {elapsed:.1f}s, found {len(result) if result else 0} regions")

doc.close()