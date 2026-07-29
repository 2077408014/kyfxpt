import sys, os, pickle
sys.path.insert(0, '.')
from app.config import INDEX_PATH

meta_file = os.path.join(INDEX_PATH, '2', 'index.pkl')
with open(meta_file, 'rb') as f:
    metadata = pickle.load(f)

# Find chunks with penalty function content and check quality
print("=== 检查包含惩罚函数内容的分块质量 ===\n")

for i, meta in enumerate(metadata):
    content = meta.get('content', '')
    if '惩罚函数' in content and '本章介绍' in content:
        print(f"Index {i}:")
        print(f"Length: {len(content)} chars")
        print(f"Full content:\n{content[:1500]}")
        print("---END---")
        break

# Check chunks around the penalty function chapter
print("\n\n=== 检查第13章相关分块 ===")
found = False
for i, meta in enumerate(metadata):
    content = meta.get('content', '')
    if '第13章' in content:
        found = True
        print(f"\nIndex {i}:")
        print(f"Content: {content[:400]}...")

if not found:
    print("No chunks with '第13章' found")
    
# Check quality metric
print("\n\n=== 分块质量分析 ===")
import re
for i, meta in enumerate(metadata):
    content = meta.get('content', '')
    if len(content) > 500:
        # Count Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        # Count garbled characters (isolated special chars, numbers, etc)
        total_chars = len(content)
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        if i in [19, 418, 419]:
            print(f"Index {i}: Chinese ratio = {chinese_ratio:.2%}, Chinese={chinese_chars}, Total={total_chars}")
            print(f"  Sample: {content[:200]}")
