import sys, time
sys.path.insert(0, '.')
import fitz
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'

print("Opening PDF...")
doc = fitz.open(pdf_path)
page = doc[0]

print("Rendering page...")
pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
print(f"Page size: {pix.width}x{pix.height}")

print("Converting to numpy...")
img = Image.open(io.BytesIO(pix.tobytes("png")))
img_np = np.array(img)
print(f"Image shape: {img_np.shape}")

print("Loading OCR engine...")
start = time.time()
ocr = RapidOCR()
print(f"Engine loaded in {time.time()-start:.1f}s")

print("Running OCR on first page...")
start = time.time()
result, _ = ocr(img_np)
elapsed = time.time() - start
print(f"OCR done in {elapsed:.1f}s")

if result:
    print(f"Found {len(result)} text regions:")
    for item in result:
        print(f"  Text: {item[1][:80]}, Conf: {item[2]:.2f}")
else:
    print("No text found!")

doc.close()