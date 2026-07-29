import sys
sys.path.insert(0, '.')
from PyPDF2 import PdfReader
pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'
reader = PdfReader(pdf_path)
print(f'Pages: {len(reader.pages)}')
for i in range(min(5, len(reader.pages))):
    text = reader.pages[i].extract_text()
    preview = text[:100] if text else "(empty)"
    print(f'Page {i+1}: len={len(text) if text else 0}, preview={preview}')