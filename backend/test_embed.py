import sys
sys.path.insert(0, '.')
from app.utils.embedding import SimpleEmbedder

embedder = SimpleEmbedder(dim=384)

# Test tokenization
test_queries = ['罚函数', '惩罚函数法', '罚函数法', '函数']

for query in test_queries:
    tokens = embedder._tokenize(query)
    vec = embedder._text_to_vec(query)
    non_zero = sum(1 for v in vec if v != 0)
    norm = sum(v * v for v in vec) ** 0.5
    print(f'Query: "{query}"')
    print(f'  Tokens: {tokens}')
    print(f'  Non-zero dims: {non_zero}/384')
    print(f'  Vector norm: {norm:.4f}')
    print(f'  First 20 dims: {vec[:20]}')
    print()

# Test with more context
print('=== Testing with context ===')
embedder._build_vocab(['罚函数是一种约束最优化方法'])
vec1 = embedder._text_to_vec('罚函数')
tokens1 = embedder._tokenize('罚函数')
non_zero1 = sum(1 for v in vec1 if v != 0)
print(f'After building vocab with context:')
print(f'  Tokens: {tokens1}')
print(f'  Non-zero dims: {non_zero1}/384')

# Check if the token is in vocab
print(f'  Vocab contains "罚函数": {"罚函数" in embedder.vocab}')
print(f'  Vocab contains "罚函": {"罚函" in embedder.vocab}')
print(f'  Vocab contains "函数": {"函数" in embedder.vocab}')

# Test with index
print(f'\n  Hash("罚函数") % 384 = {hash("罚函数") % 384}')
print(f'  Hash("罚函") % 384 = {hash("罚函") % 384}')
print(f'  Hash("函数") % 384 = {hash("函数") % 384}')
