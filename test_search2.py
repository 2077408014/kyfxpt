import sys
sys.path.insert(0, r'd:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend')
from app.services.knowledge_base_service import knowledge_base_service

index_data = knowledge_base_service._load_index(2)
metadata = index_data["metadata"]

print(f'Total chunks: {len(metadata)}')
for i, m in enumerate(metadata):
    content = m.get("content", "")
    has_xinpu = "辛普森" in content or "辛普" in content
    has_fuhua = "复化" in content
    print(f'Chunk {i}: len={len(content)}, has_辛普森={has_xinpu}, has_复化={has_fuhua}')
    if has_xinpu or has_fuhua:
        print(f'  Content: {content[:300]}...')
        print()

# Now test search
print('\nTesting search for "复化辛普森法":')
results = knowledge_base_service.search(2, '复化辛普森法', top_k=5, threshold=0.15, enable_keyword_fallback=True)
print(f'Found {len(results)} results')
for i, r in enumerate(results):
    sim = r["similarity"]
    content = r['content'][:200]
    print(f'  Result {i+1}: similarity={sim:.3f}')
    print(f'  Content: {content}...')
    print()