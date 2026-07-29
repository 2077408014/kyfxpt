import sys
sys.path.insert(0, '.')
from app.utils.embedding import SimpleEmbedder

embedder = SimpleEmbedder(dim=384)

# Test new tokenization
test_queries = ['罚函数', '惩罚函数法', '罚函数法', '函数', '罚']

for query in test_queries:
    tokens = embedder._tokenize(query)
    print(f'Query: "{query}"')
    print(f'  Tokens: {tokens}')
    print(f'  Token count: {len(tokens)}')
    print()

# Now test matching
print('=== Testing vector matching ===')

# Simulate document content
doc_content = '罚函数法是一种约束最优化方法，包括外点罚函数法和内点罚函数法'
doc_tokens = embedder._tokenize(doc_content)
print(f'Doc tokens: {doc_tokens[:20]}...')

# Build vocab with doc
embedder._build_vocab([doc_content])

# Test query
query = '罚函数'
query_tokens = embedder._tokenize(query)
query_vec = embedder._text_to_vec(query)
doc_vec = embedder._text_to_vec(doc_content)

similarity = embedder.similarity(query_vec, doc_vec)
non_zero_query = sum(1 for v in query_vec if v != 0)
non_zero_doc = sum(1 for v in doc_vec if v != 0)

print(f'\nQuery: "{query}"')
print(f'  Query tokens: {query_tokens}')
print(f'  Query non-zero dims: {non_zero_query}/384')
print(f'  Doc non-zero dims: {non_zero_doc}/384')
print(f'  Similarity: {similarity:.4f}')

# Test with shorter query
query2 = '函数'
query2_vec = embedder._text_to_vec(query2)
similarity2 = embedder.similarity(query2_vec, doc_vec)
print(f'\nQuery: "{query2}"')
print(f'  Similarity: {similarity2:.4f}')

# Test with completely different topic
doc2_content = '运输问题的数学模型与表上作业法'
embedder._build_vocab([doc2_content])
doc2_vec = embedder._text_to_vec(doc2_content)
similarity3 = embedder.similarity(query_vec, doc2_vec)
print(f'\nQuery "罚函数" vs Doc "运输问题":')
print(f'  Similarity: {similarity3:.4f}')
