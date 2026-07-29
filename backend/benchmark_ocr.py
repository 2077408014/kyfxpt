import sys
import time
sys.path.insert(0, '.')
import fitz
from rapidocr_onnxruntime import RapidOCR

pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'

print("Loading RapidOCR engine...")
start = time.time()
ocr = RapidOCR()
print(f"Engine loaded in {time.time()-start:.1f}s")

doc = fitz.open(pdf_path)
print(f"PDF opened, {len(doc)} pages")

# Test first page
page = doc[0]
pix = page.get_pixmap()
print(f"Page 0 rendered: {pix.width}x{pix.height}")

temp_img = "temp_test_page.png"
pix.save(temp_img)

start = time.time()
result, _ = ocr(temp_img)
elapsed = time.time() - start
print(f"OCR page 0: {len(result) if result else 0} results, {elapsed:.1f}s")

if result:
    for item in result[:5]:
        print(f"  Text: {item[1][:50]}, Confidence: {item[2]:.2f}")

import os
os.remove(temp_img)

# Test another page
page = doc[100]
pix = page.get_pixmap()
pix.save(temp_img)
start = time.time()
result2, _ = ocr(temp_img)
elapsed = time.time() - start
print(f"OCR page 100: {len(result2) if result2 else 0} results, {elapsed:.1f}s")

if result2:
    for item in result2[:5]:
        print(f"  Text: {item[1][:50]}, Confidence: {item[2]:.2f}")

os.remove(temp_img)
doc.close()

# Estimate total time
avg_time = elapsed * 2  # rough estimate
total_pages = 478
est_total = avg_time * total_pages
print(f"\nEstimated total time for {total_pages} pages: {est_total:.0f}s = {est_total/60:.1f}min")
print(f"Estimated time with 150 DPI (2x pixels): {est_total*2:.0f}s")