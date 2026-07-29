import sys
import time
sys.path.insert(0, '.')
import fitz
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'

print("Loading RapidOCR engine...")
start = time.time()
ocr = RapidOCR()
print(f"Engine loaded in {time.time()-start:.1f}s")

doc = fitz.open(pdf_path)

# Test with 0.7x matrix (optimized)
page = doc[100]
pix = page.get_pixmap(matrix=fitz.Matrix(0.7, 0.7))
print(f"Optimized size: {pix.width}x{pix.height}")

img_bytes = pix.tobytes("png")
img = Image.open(io.BytesIO(img_bytes))
img_np = np.array(img)

start = time.time()
result, _ = ocr(img_np)
elapsed = time.time() - start
print(f"OCR optimized: {len(result) if result else 0} results, {elapsed:.1f}s")

if result:
    for item in result[:3]:
        print(f"  Text: {item[1][:50]}, Conf: {item[2]:.2f}")

# Test default size for comparison
pix2 = page.get_pixmap()
print(f"Default size: {pix2.width}x{pix2.height}")
img_bytes2 = pix2.tobytes("png")
img2 = Image.open(io.BytesIO(img_bytes2))
img_np2 = np.array(img2)

start = time.time()
result2, _ = ocr(img_np2)
elapsed2 = time.time() - start
print(f"OCR default: {len(result2) if result2 else 0} results, {elapsed2:.1f}s")

# Speedup
print(f"\nSpeedup: {elapsed2/elapsed:.1f}x")
print(f"Estimated time per page (optimized): {elapsed:.1f}s")
print(f"Estimated total for 478 pages: {elapsed * 478:.0f}s = {elapsed * 478 / 60:.1f}min")

doc.close()