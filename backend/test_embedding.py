import sys
sys.path.insert(0, '.')
from app.utils.embedding import SimpleEmbedder

embedder = SimpleEmbedder()

chunks = [
    '罚函数法是一种求解约束优化问题的方法',
    '罚函数的基本思想是将约束优化问题转化为无约束优化问题',
    '常见的罚函数包括外罚函数和内罚函数',
    '在最优化理论中，罚函数法有着重要的地位'
]

embedder._build_vocab(chunks)

query = '罚函数'
query_vec = embedder.embed_text(query)
print(f'Query tokens: {embedder._tokenize(query)}')

for i, chunk in enumerate(chunks):
    chunk_vec = embedder.embed_text(chunk)
    similarity = embedder.similarity(query_vec, chunk_vec)
    print(f'Chunk {i+1} similarity: {similarity:.4f} | {chunk[:30]}...')

print()
print('=== Testing N-gram matching ===')
test_chinese = '罚函数法'
tokens = embedder._tokenize(test_chinese)
print(f'Tokens for "{test_chinese}": {tokens}')

test_chinese2 = '罚函数'
tokens2 = embedder._tokenize(test_chinese2)
print(f'Tokens for "{test_chinese2}": {tokens2}')

overlap = set(tokens) & set(tokens2)
print(f'Overlap: {overlap}')
print(f'Overlap ratio: {len(overlap)}/{len(set(tokens2))} = {len(overlap)/max(len(set(tokens2)),1):.2f}')