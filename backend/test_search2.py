import sys, os, pickle, re
sys.path.insert(0, '.')
from app.config import INDEX_PATH

meta_file = os.path.join(INDEX_PATH, '2', 'index.pkl')
with open(meta_file, 'rb') as f:
    metadata = pickle.load(f)

# Test keyword search directly
query = '罚函数'

# Extract Chinese phrases
def extract_chinese_phrases(text):
    phrases = []
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    for chunk in chinese:
        n = len(chunk)
        for length in range(min(n, 6), 1, -1):
            for i in range(n - length + 1):
                phrases.append(chunk[i:i+length])
    return phrases

phrases = extract_chinese_phrases(query.lower())
print(f'Query: {query}')
print(f'Extracted phrases: {phrases}')

# Search in metadata
results = []
for idx, meta in enumerate(metadata):
    content = meta.get('content', '')
    if not content:
        continue
    
    score = 0.0
    for phrase in phrases:
        if phrase in content:
            phrase_len = len(phrase)
            if phrase_len >= 3:
                score += phrase_len * 2.0
            elif phrase_len == 2:
                score += 2.0
            else:
                score += 0.5
    
    if query in content:
        score += 10.0
    
    if score > 0:
        results.append((idx, score, content[:200]))

# Sort by score
results.sort(key=lambda x: x[1], reverse=True)

print(f'\nKeyword search results (top 10):')
for i, (idx, score, preview) in enumerate(results[:10]):
    print(f'{i+1}. Index {idx}, Score={score:.1f}')
    print(f'   Preview: {preview}...')
    print()

# Now check the vector search issue
print('\n=== Testing vector embedding quality ===')
from app.utils.embedding import get_text_embedder
import numpy as np

embedder = get_text_embedder()
query_vector = embedder.embed_text(query)
print(f'Query vector (first 10 dims): {query_vector[:10]}...')
print(f'Query vector norm: {np.linalg.norm(query_vector):.4f}')

# Check vectors of relevant chunks
print('\nChecking vectors of penalty function chunks:')
for idx in [19, 418, 419, 421]:
    content = metadata[idx].get('content', '')
    if content:
        chunk_vector = embedder.embed_text(content)
        similarity = np.dot(query_vector, chunk_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector))
        print(f'  Index {idx}: cosine_similarity = {similarity:.4f}')
        
        # Also check if content contains the keyword
        has_keyword = '罚函数' in content
        print(f'    Has keyword: {has_keyword}')

# Check vectors of irrelevant chunks that were returned
print('\nChecking vectors of irrelevant chunks (those returned in search):')
# These are the ones returned by the vector search
for idx in [15, 16, 17]:  # Guess at the irrelevant chunks
    if idx < len(metadata):
        content = metadata[idx].get('content', '')
        if content:
            chunk_vector = embedder.embed_text(content)
            similarity = np.dot(query_vector, chunk_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector))
            has_keyword = '罚函数' in content
            print(f'  Index {idx}: cosine_similarity = {similarity:.4f}, has_keyword={has_keyword}')
