import sys
sys.path.insert(0, '.')
import fitz

pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'
doc = fitz.open(pdf_path)

page = doc[0]

# Try different text extraction methods
text1 = page.get_text("text")
print(f"get_text('text'): len={len(text1)}, preview={text1[:200]}")

text2 = page.get_text("blocks")
print(f"get_text('blocks'): len={len(str(text2))}, first block: {text2[0] if text2 else 'empty'}")

text3 = page.get_text("words")
print(f"get_text('words'): len={len(text3)}, first words: {text3[:5]}")

# Check if there are any annotations
annots = list(page.annots() or [])
print(f"Annotations: {len(annots)}")

# Check page dimensions
print(f"Page rect: {page.rect}")

# Try extracting text with different options
text4 = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
print(f"get_text with flags: len={len(text4)}, preview={repr(text4[:200])}")

# Check if it's an image-based PDF by looking at page content
try:
    xobjects = page.get_xobjects()
    print(f"XObjects: {len(xobjects)}")
except:
    print("No XObjects")

# Try to get the raw content stream
print(f"\nPage 1 content: {page.read_contents()[:500] if page.read_contents() else 'empty'}")

doc.close()